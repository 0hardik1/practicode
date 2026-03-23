from __future__ import annotations

import base64
import mimetypes
from collections.abc import Sequence
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import Problem, TestCase
from app.schemas import (
    ProblemApiDocs,
    ProblemDetail,
    ProblemFileCreateRequest,
    ProblemFileCreateResponse,
    ProblemFileContent,
    ProblemFileNode,
    ProblemFileTreeResponse,
    ProblemFileUpdateRequest,
    ProblemSummary,
    TestCaseView,
)
from app.services.problem_loader import find_problem_dir, seed_problems


router = APIRouter(prefix="/api/problems", tags=["problems"])
TEXT_EXTENSIONS = {
    ".json",
    ".md",
    ".py",
    ".svg",
    ".txt",
    ".yaml",
    ".yml",
}
IGNORED_NAMES = {".DS_Store", "__pycache__"}


async def _get_problem(
    identifier: str,
    session: AsyncSession,
) -> Problem:
    result = await session.execute(
        select(Problem).where(or_(Problem.id == identifier, Problem.slug == identifier))
    )
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


def _filter_problems(
    problems: Sequence[Problem],
    difficulty: str | None,
    tags: list[str],
) -> list[Problem]:
    filtered = list(problems)
    if difficulty:
        filtered = [problem for problem in filtered if problem.difficulty == difficulty]
    if tags:
        required = set(tags)
        filtered = [
            problem
            for problem in filtered
            if required.issubset(set(problem.tags or []))
        ]
    return filtered


def _resolve_problem_dir(identifier: str) -> Path:
    settings = get_settings()
    problem_dir = find_problem_dir(settings.problems_dir, identifier)
    if problem_dir is None:
        raise HTTPException(status_code=404, detail="Problem files not found")
    return problem_dir


def _resolve_problem_file(problem_dir: Path, relative_path: str) -> Path:
    if not relative_path:
        raise HTTPException(status_code=400, detail="File path is required")

    candidate = (problem_dir / relative_path).resolve()
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="Problem file not found")
    if problem_dir.resolve() not in candidate.parents and candidate != problem_dir.resolve():
        raise HTTPException(status_code=400, detail="Invalid problem file path")
    if candidate.is_dir():
        raise HTTPException(status_code=400, detail="Expected a file path")
    return candidate


def _resolve_problem_directory(problem_dir: Path, relative_path: str | None) -> Path:
    if not relative_path:
        return problem_dir.resolve()

    candidate = (problem_dir / relative_path).resolve()
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="Target directory not found")
    if problem_dir.resolve() not in candidate.parents and candidate != problem_dir.resolve():
        raise HTTPException(status_code=400, detail="Invalid problem directory path")
    if not candidate.is_dir():
        raise HTTPException(status_code=400, detail="Expected a directory path")
    return candidate


def _is_text_file(path: Path, mime_type: str | None) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or bool(
        mime_type and (mime_type.startswith("text/") or mime_type == "image/svg+xml")
    )


def _build_tree(root: Path, current: Path) -> ProblemFileNode | None:
    if current.name in IGNORED_NAMES:
        return None

    relative_path = "" if current == root else current.relative_to(root).as_posix()
    if current.is_dir():
        children = [
            node
            for child in sorted(current.iterdir(), key=lambda item: (item.is_file(), item.name))
            if (node := _build_tree(root, child)) is not None
        ]
        return ProblemFileNode(
            name=current.name if current != root else root.name,
            path=relative_path,
            kind="directory",
            children=children,
        )

    mime_type, _ = mimetypes.guess_type(current.name)
    is_binary = not _is_text_file(current, mime_type)
    return ProblemFileNode(
        name=current.name,
        path=relative_path,
        kind="file",
        editable=not is_binary,
        is_binary=is_binary,
        mime_type=mime_type,
        size=current.stat().st_size,
    )


def _read_problem_file(problem_id: str, file_path: Path, root: Path) -> ProblemFileContent:
    mime_type, _ = mimetypes.guess_type(file_path.name)
    is_text = _is_text_file(file_path, mime_type)
    raw_bytes = file_path.read_bytes()
    relative_path = file_path.relative_to(root).as_posix()

    if is_text:
        return ProblemFileContent(
            problem_id=problem_id,
            path=relative_path,
            name=file_path.name,
            editable=True,
            is_binary=False,
            mime_type=mime_type,
            size=len(raw_bytes),
            text_content=raw_bytes.decode("utf-8"),
        )

    return ProblemFileContent(
        problem_id=problem_id,
        path=relative_path,
        name=file_path.name,
        editable=False,
        is_binary=True,
        mime_type=mime_type,
        size=len(raw_bytes),
        base64_content=base64.b64encode(raw_bytes).decode("ascii"),
    )


@router.get("", response_model=list[ProblemSummary])
async def list_problems(
    difficulty: str | None = None,
    tags: str | None = Query(default=None, description="Comma-separated tags"),
    session: AsyncSession = Depends(get_session),
) -> list[ProblemSummary]:
    result = await session.execute(select(Problem).order_by(Problem.id))
    raw_tags = [tag.strip() for tag in (tags or "").split(",") if tag.strip()]
    problems = _filter_problems(result.scalars().all(), difficulty, raw_tags)
    return [ProblemSummary.model_validate(problem) for problem in problems]


@router.get("/{problem_id}", response_model=ProblemDetail)
async def get_problem_detail(
    problem_id: str,
    session: AsyncSession = Depends(get_session),
) -> ProblemDetail:
    problem = await _get_problem(problem_id, session)
    visible_result = await session.execute(
        select(TestCase)
        .where(TestCase.problem_id == problem.id, TestCase.is_hidden.is_(False))
        .order_by(TestCase.ordinal)
    )
    return ProblemDetail(
        **ProblemSummary.model_validate(problem).model_dump(),
        description=problem.description,
        starter_code=problem.starter_code,
        api_docs=problem.api_docs,
        visible_tests=[
            TestCaseView.model_validate(test) for test in visible_result.scalars().all()
        ],
    )


@router.get("/{problem_id}/api-docs", response_model=ProblemApiDocs)
async def get_problem_api_docs(
    problem_id: str,
    session: AsyncSession = Depends(get_session),
) -> ProblemApiDocs:
    problem = await _get_problem(problem_id, session)
    return ProblemApiDocs(problem_id=problem.id, api_docs=problem.api_docs)


@router.get("/{problem_id}/files", response_model=ProblemFileTreeResponse)
async def list_problem_files(problem_id: str) -> ProblemFileTreeResponse:
    problem_dir = _resolve_problem_dir(problem_id)
    root = _build_tree(problem_dir, problem_dir)
    if root is None:
        raise HTTPException(status_code=404, detail="Problem files not found")
    return ProblemFileTreeResponse(problem_id=problem_id, root=root)


@router.get("/{problem_id}/files/content", response_model=ProblemFileContent)
async def get_problem_file_content(
    problem_id: str,
    path: str = Query(..., description="Path relative to the problem directory"),
) -> ProblemFileContent:
    problem_dir = _resolve_problem_dir(problem_id)
    file_path = _resolve_problem_file(problem_dir, path)
    return _read_problem_file(problem_id, file_path, problem_dir)


@router.put("/{problem_id}/files/content", response_model=ProblemFileContent)
async def update_problem_file_content(
    problem_id: str,
    payload: ProblemFileUpdateRequest,
    path: str = Query(..., description="Path relative to the problem directory"),
    session: AsyncSession = Depends(get_session),
) -> ProblemFileContent:
    problem_dir = _resolve_problem_dir(problem_id)
    file_path = _resolve_problem_file(problem_dir, path)
    mime_type, _ = mimetypes.guess_type(file_path.name)
    if not _is_text_file(file_path, mime_type):
        raise HTTPException(status_code=400, detail="This file cannot be edited in the browser")

    original_content = file_path.read_text(encoding="utf-8")
    try:
        file_path.write_text(payload.content, encoding="utf-8")
        await seed_problems(session, get_settings().problems_dir)
    except Exception as exc:
        file_path.write_text(original_content, encoding="utf-8")
        await seed_problems(session, get_settings().problems_dir)
        raise HTTPException(status_code=400, detail=f"Failed to save file: {exc}") from exc

    return _read_problem_file(problem_id, file_path, problem_dir)


@router.post("/{problem_id}/files", response_model=ProblemFileCreateResponse)
async def create_problem_file_or_directory(
    problem_id: str,
    payload: ProblemFileCreateRequest,
) -> ProblemFileCreateResponse:
    problem_dir = _resolve_problem_dir(problem_id)
    parent_dir = _resolve_problem_directory(problem_dir, payload.parent_path)

    if not payload.name or payload.name.strip() in {".", ".."}:
        raise HTTPException(status_code=400, detail="A valid file or directory name is required")
    if "/" in payload.name or "\\" in payload.name:
        raise HTTPException(status_code=400, detail="Nested paths are not allowed in the name field")

    target = parent_dir / payload.name.strip()
    if target.exists():
        raise HTTPException(status_code=409, detail="A file or directory with that name already exists")

    if payload.kind == "directory":
        target.mkdir(parents=False, exist_ok=False)
    else:
        target.write_text("", encoding="utf-8")

    return ProblemFileCreateResponse(
        problem_id=problem_id,
        path=target.relative_to(problem_dir).as_posix(),
        kind=payload.kind,
    )
