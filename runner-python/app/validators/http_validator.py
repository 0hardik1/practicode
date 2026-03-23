from __future__ import annotations

from typing import Any

import requests


def validate_http_validation(
    endpoint: str,
    test_id: str,
) -> tuple[bool, str, Any, Any]:
    response = requests.get(endpoint, params={"test_id": test_id}, timeout=5)
    response.raise_for_status()
    payload = response.json()
    return (
        bool(payload.get("passed")),
        payload.get("message", ""),
        payload.get("actual"),
        payload.get("expected"),
    )

