from __future__ import annotations

import json
from typing import Any


def _coerce_stdout(stdout: str) -> Any:
    stripped = stdout.strip()
    if not stripped:
        return ""

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return stripped


def validate_program_output(stdout: str) -> tuple[bool, str, Any, Any]:
    actual = _coerce_stdout(stdout)
    return True, "Program executed successfully.", actual, None
