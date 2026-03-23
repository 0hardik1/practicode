from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def validate_custom_script(
    workspace_dir: Path,
    script_name: str,
    test_case: dict[str, Any],
    process_result: dict[str, Any],
) -> tuple[bool, str, Any, Any]:
    script_path = workspace_dir / script_name
    payload = {"test_case": test_case, "process_result": process_result}
    process = subprocess.run(
        [sys.executable, str(script_path)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        cwd=str(workspace_dir),
    )
    if process.returncode != 0:
        return False, "Custom validator exited with a non-zero status.", None, None

    response = json.loads(process.stdout.strip() or "{}")
    return (
        bool(response.get("passed")),
        response.get("message", ""),
        response.get("actual"),
        response.get("expected"),
    )

