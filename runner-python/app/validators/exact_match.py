from __future__ import annotations

import json
from typing import Any


def _coerce_candidate(stdout: str) -> Any:
    stripped = stdout.strip()
    if not stripped:
        return None

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return stripped


def _last_non_empty_line(stdout: str) -> str | None:
    for line in reversed(stdout.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def validate_exact_match(stdout: str, expected: Any) -> tuple[bool, str, Any, Any]:
    full_output = _coerce_candidate(stdout)
    if full_output == expected:
        return True, "Exact match succeeded.", full_output, expected

    last_line = _last_non_empty_line(stdout)
    if last_line is not None:
        final_output = _coerce_candidate(last_line)
        if final_output == expected:
            return True, "Matched final output line after ignoring debug logs.", final_output, expected
        return False, "Output did not match expected value.", final_output, expected

    return False, "Output did not match expected value.", full_output, expected
