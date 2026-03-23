from __future__ import annotations

from typing import Any

import requests


def aggregate_output(results: list[dict[str, Any]], field: str) -> str | None:
    chunks = []
    for result in results:
        value = result.get(field)
        if value:
            chunks.append(f"[{result['test_id']}] {value}")
    if not chunks:
        return None
    if len(chunks) == 1:
        return chunks[0].split("] ", 1)[-1]
    return "\n\n".join(chunks)


def determine_status(results: list[dict[str, Any]]) -> str:
    if any(result.get("error") == "Time Limit Exceeded" for result in results):
        return "timeout"
    if all(result.get("passed") for result in results):
        return "passed"
    return "failed"


def post_results(callback_url: str, payload: dict[str, Any]) -> str | None:
    if not callback_url:
        return None

    try:
        response = requests.post(callback_url, json=payload, timeout=5)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - network failures are environment-specific
        return str(exc)
    return None
