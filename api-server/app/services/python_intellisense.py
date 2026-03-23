from __future__ import annotations

import ast
import pkgutil
import re
import sys
from functools import lru_cache
from pathlib import Path

import jedi

from app.schemas import (
    IntellisenseTextEdit,
    PythonCompletionItem,
    PythonCompletionRequest,
    PythonCompletionResponse,
    PythonHoverRequest,
    PythonHoverResponse,
)


ATTRIBUTE_PATTERN = re.compile(r"([A-Za-z_][A-Za-z0-9_\.]*)\.([A-Za-z0-9_]*)$")
IDENTIFIER_PATTERN = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)$")
MAX_COMPLETION_ITEMS = 80
MAX_MODULE_SUGGESTIONS = 20
SKIP_LOCAL_MODULES = {"solution", "starter", "__init__"}


def _normalize_position(code: str, line: int, column: int) -> tuple[int, int]:
    lines = code.splitlines() or [""]
    safe_line = min(max(line, 1), len(lines))
    line_text = lines[safe_line - 1]
    safe_column = min(max(column, 1), len(line_text) + 1)
    return safe_line, safe_column


def _line_prefix(code: str, line: int, column: int) -> str:
    lines = code.splitlines() or [""]
    if line > len(lines):
        return ""
    return lines[line - 1][: max(column - 1, 0)]


def _line_text(code: str, line: int) -> str:
    lines = code.splitlines() or [""]
    if line > len(lines):
        return ""
    return lines[line - 1]


def _safe_jedi_complete(code: str, path: str, line: int, column: int) -> list[jedi.api.classes.Completion]:
    try:
        script = jedi.Script(code=code, path=path)
        return list(script.complete(line=line, column=max(column - 1, 0)))
    except Exception:
        return []


def _safe_jedi_help(code: str, path: str, line: int, column: int) -> list[jedi.api.classes.Name]:
    try:
        script = jedi.Script(code=code, path=path)
        return list(script.help(line=line, column=max(column - 1, 0)))
    except Exception:
        return []


def _safe_jedi_infer(code: str, path: str, line: int, column: int) -> list[jedi.api.classes.Name]:
    try:
        script = jedi.Script(code=code, path=path)
        return list(script.infer(line=line, column=max(column - 1, 0)))
    except Exception:
        return []


@lru_cache(maxsize=1)
def _environment_modules() -> tuple[str, ...]:
    names = set(sys.stdlib_module_names)
    names.update(module.name for module in pkgutil.iter_modules())
    filtered = {
        name
        for name in names
        if name
        and name.isidentifier()
        and not name.startswith("_")
    }
    return tuple(sorted(filtered))


def _problem_local_modules(problem_dir: Path | None) -> set[str]:
    if problem_dir is None or not problem_dir.exists():
        return set()

    local_modules: set[str] = set()
    for child in problem_dir.iterdir():
        if child.is_file() and child.suffix == ".py" and child.stem not in SKIP_LOCAL_MODULES:
            local_modules.add(child.stem)
        if child.is_dir() and (child / "__init__.py").exists():
            local_modules.add(child.name)
    return local_modules


def _top_level_catalog(problem_dir: Path | None) -> tuple[str, ...]:
    names = set(_environment_modules())
    names.update(_problem_local_modules(problem_dir))
    return tuple(sorted(names))


def _import_state(code: str) -> tuple[set[str], dict[str, str]]:
    imported_roots: set[str] = set()
    aliases: dict[str, str] = {}

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return imported_roots, aliases

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                imported_roots.add(root)
                aliases[alias.asname or root] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            root = node.module.split(".")[0]
            imported_roots.add(root)
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    return imported_roots, aliases


def _identifier_at_position(code: str, line: int, column: int) -> str | None:
    line_text = _line_text(code, line)
    if not line_text:
        return None

    index = min(max(column - 1, 0), len(line_text) - 1)
    if not (line_text[index].isalnum() or line_text[index] == "_"):
        if index > 0 and (line_text[index - 1].isalnum() or line_text[index - 1] == "_"):
            index -= 1
        else:
            return None

    start = index
    while start > 0 and (line_text[start - 1].isalnum() or line_text[start - 1] == "_"):
        start -= 1

    end = index + 1
    while end < len(line_text) and (line_text[end].isalnum() or line_text[end] == "_"):
        end += 1

    return line_text[start:end]


def _is_docstring_node(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _insertion_position(code: str, after_line: int) -> tuple[int, int, str]:
    lines = code.splitlines()
    if not lines:
        return 1, 1, ""

    if after_line < len(lines):
        return after_line + 1, 1, ""

    return len(lines), len(lines[-1]) + 1, "\n"


def _build_import_edit(code: str, module_name: str) -> IntellisenseTextEdit | None:
    imported_roots, _ = _import_state(code)
    root_name = module_name.split(".")[0]
    if root_name in imported_roots:
        return None

    after_line = 0
    lines = code.splitlines()
    if lines and lines[0].startswith("#!"):
        after_line = 1
        if len(lines) > 1 and "coding" in lines[1]:
            after_line = 2

    try:
        body = ast.parse(code).body
    except SyntaxError:
        body = []

    index = 0
    if body and _is_docstring_node(body[0]):
        after_line = max(after_line, body[0].end_lineno or 1)
        index = 1

    while index < len(body) and isinstance(body[index], (ast.Import, ast.ImportFrom)):
        after_line = max(after_line, body[index].end_lineno or after_line)
        index += 1

    start_line, start_column, prefix = _insertion_position(code, after_line)
    return IntellisenseTextEdit(
        start_line=start_line,
        start_column=start_column,
        end_line=start_line,
        end_column=start_column,
        text=f"{prefix}import {root_name}\n",
    )


def _completion_kind(jedi_type: str) -> str:
    mapping = {
        "class": "class",
        "function": "function",
        "instance": "variable",
        "keyword": "keyword",
        "module": "module",
        "param": "parameter",
        "path": "file",
        "property": "property",
        "statement": "variable",
    }
    return mapping.get(jedi_type, "text")


def _completion_documentation(completion: jedi.api.classes.Completion) -> str | None:
    try:
        doc = completion.docstring()
    except Exception:
        return None
    return doc or None


def _from_jedi(
    completions: list[jedi.api.classes.Completion],
    *,
    additional_edit: IntellisenseTextEdit | None = None,
    sort_prefix: str = "1",
) -> list[PythonCompletionItem]:
    items: list[PythonCompletionItem] = []
    for completion in completions[:MAX_COMPLETION_ITEMS]:
        detail = None
        try:
            detail = completion.description
        except Exception:
            detail = None
        item = PythonCompletionItem(
            label=completion.name,
            kind=_completion_kind(completion.type),
            detail=detail,
            documentation=_completion_documentation(completion),
            insert_text=completion.name,
            sort_text=f"{sort_prefix}:{completion.name}",
            additional_text_edits=[additional_edit] if additional_edit else [],
        )
        items.append(item)
    return items


def _format_hover_content(name: jedi.api.classes.Name) -> list[str]:
    contents: list[str] = []

    try:
        doc = name.docstring()
    except Exception:
        doc = ""

    signature = ""
    details = ""
    if doc:
        signature, _, details = doc.partition("\n\n")

    if signature:
        contents.append(f"```python\n{signature}\n```")
    elif getattr(name, "description", None):
        contents.append(f"```python\n{name.description}\n```")

    full_name = getattr(name, "full_name", None)
    if full_name:
        contents.append(f"`{full_name}`")

    if details:
        contents.append(details)

    return contents


def _module_suggestions(
    prefix: str,
    code: str,
    problem_dir: Path | None,
    imported_roots: set[str],
) -> list[PythonCompletionItem]:
    if len(prefix) < 2:
        return []

    suggestions: list[PythonCompletionItem] = []
    for module_name in _top_level_catalog(problem_dir):
        if module_name in imported_roots:
            continue
        if not module_name.startswith(prefix):
            continue
        suggestions.append(
            PythonCompletionItem(
                label=module_name,
                kind="module",
                detail="Auto import module",
                documentation=f"Insert `import {module_name}`",
                insert_text=module_name,
                sort_text=f"0:{module_name}",
                additional_text_edits=list(
                    filter(None, [_build_import_edit(code, module_name)])
                ),
            )
        )
        if len(suggestions) >= MAX_MODULE_SUGGESTIONS:
            break
    return suggestions


def _unimported_module_attribute_context(
    code: str,
    line: int,
    column: int,
    imported_roots: set[str],
    problem_dir: Path | None,
) -> tuple[str, str] | None:
    del problem_dir
    prefix = _line_prefix(code, line, column)
    match = ATTRIBUTE_PATTERN.search(prefix)
    if not match:
        return None

    expression = match.group(1)
    root_name = expression.split(".")[0]
    if root_name in imported_roots:
        return None

    module_catalog = set(_environment_modules())
    if root_name not in module_catalog:
        return None

    synthetic_code = f"import {root_name}\n{code}"
    return root_name, synthetic_code


def _module_hover_contents(
    code: str,
    path: str,
    line: int,
    column: int,
    imported_roots: set[str],
) -> list[str]:
    module_context = _unimported_module_attribute_context(
        code,
        line,
        column,
        imported_roots,
        None,
    )
    if module_context is not None:
        _, synthetic_code = module_context
        names = _safe_jedi_help(
            synthetic_code,
            path,
            line + 1,
            column,
        ) or _safe_jedi_infer(
            synthetic_code,
            path,
            line + 1,
            column,
        )
        if names:
            return _format_hover_content(names[0])

    identifier = _identifier_at_position(code, line, column)
    if not identifier or identifier in imported_roots:
        return []
    if identifier not in set(_environment_modules()):
        return []

    synthetic_code = f"import {identifier}\n{code}"
    names = _safe_jedi_help(
        synthetic_code,
        path,
        line + 1,
        column,
    ) or _safe_jedi_infer(
        synthetic_code,
        path,
        line + 1,
        column,
    )
    if not names:
        return []
    return _format_hover_content(names[0])


def build_python_completion_response(
    payload: PythonCompletionRequest,
    *,
    problem_dir: Path | None = None,
) -> PythonCompletionResponse:
    line, column = _normalize_position(
        payload.code,
        payload.position.line,
        payload.position.column,
    )
    imported_roots, _ = _import_state(payload.code)
    items = _from_jedi(
        _safe_jedi_complete(payload.code, payload.path, line, column),
        sort_prefix="1",
    )

    module_attribute_context = _unimported_module_attribute_context(
        payload.code,
        line,
        column,
        imported_roots,
        problem_dir,
    )
    if module_attribute_context is not None:
        module_name, synthetic_code = module_attribute_context
        completions = _safe_jedi_complete(
            synthetic_code,
            path="intellisense.py",
            line=line + 1,
            column=column,
        )
        items.extend(
            _from_jedi(
                completions,
                additional_edit=_build_import_edit(payload.code, module_name),
                sort_prefix="0",
            )
        )
    else:
        prefix = ""
        match = IDENTIFIER_PATTERN.search(_line_prefix(payload.code, line, column))
        if match:
            prefix = match.group(1)
        items.extend(
            _module_suggestions(prefix, payload.code, problem_dir, imported_roots)
        )

    deduped: dict[tuple[str, str], PythonCompletionItem] = {}
    for item in items:
        key = (item.label, item.kind)
        if key not in deduped:
            deduped[key] = item

    return PythonCompletionResponse(items=list(deduped.values())[:MAX_COMPLETION_ITEMS])


def build_python_hover_response(
    payload: PythonHoverRequest,
    *,
    problem_dir: Path | None = None,
) -> PythonHoverResponse:
    del problem_dir
    line, column = _normalize_position(
        payload.code,
        payload.position.line,
        payload.position.column,
    )
    imported_roots, _ = _import_state(payload.code)

    names = _safe_jedi_help(
        payload.code,
        payload.path,
        line,
        column,
    ) or _safe_jedi_infer(
        payload.code,
        payload.path,
        line,
        column,
    )
    if names:
        return PythonHoverResponse(contents=_format_hover_content(names[0]))

    return PythonHoverResponse(
        contents=_module_hover_contents(
            payload.code,
            payload.path,
            line,
            column,
            imported_roots,
        )
    )
