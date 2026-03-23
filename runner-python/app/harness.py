from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from utils import aggregate_output, determine_status, post_results
from validators.custom_script import validate_custom_script
from validators.exact_match import validate_exact_match
from validators.http_validator import validate_http_validation
from validators.program_output import validate_program_output


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _workspace_dir() -> Path:
    return Path(os.environ.get("WORKSPACE_DIR", Path.cwd()))


def _validate_result(
    workspace_dir: Path,
    test_case: dict[str, Any],
    stdout: str,
    process_result: dict[str, Any],
) -> tuple[bool, str, Any, Any]:
    validation_type = test_case.get("validation_type", "exact_match")
    if validation_type == "exact_match":
        return validate_exact_match(stdout, test_case.get("expected"))
    if validation_type == "program_output":
        return validate_program_output(stdout)
    if validation_type == "http_validation":
        endpoint = test_case.get("validation_endpoint")
        if not endpoint:
            raise ValueError("http_validation requires validation_endpoint")
        return validate_http_validation(endpoint, test_case["id"])
    if validation_type == "custom_script":
        script_name = test_case.get("validator_script") or test_case.get("validation_script")
        if not script_name:
            raise ValueError("custom_script requires validator_script")
        return validate_custom_script(workspace_dir, script_name, test_case, process_result)
    raise ValueError(f"Unsupported validation type: {validation_type}")


def _run_test(
    workspace_dir: Path,
    solution_path: Path,
    config: dict[str, Any],
    test_case: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {"test_id": test_case["id"], "name": test_case["name"]}
    started_at = time.time()
    env = os.environ.copy()
    env.update({key: str(value) for key, value in config.get("env", {}).items()})
    env["TEST_INPUT"] = json.dumps(test_case.get("input", {}))

    try:
        process = subprocess.run(
            [sys.executable, str(solution_path)],
            input=json.dumps(test_case.get("input", {})),
            capture_output=True,
            text=True,
            timeout=config["time_limit_seconds"],
            cwd=str(workspace_dir),
            env=env,
        )

        result["stdout"] = process.stdout
        result["stderr"] = process.stderr
        result["exit_code"] = process.returncode
        result["duration_ms"] = int((time.time() - started_at) * 1000)

        if process.returncode != 0:
            result["passed"] = False
            result["error"] = f"Process exited with code {process.returncode}"
            result["expected"] = test_case.get("expected")
            return result

        passed, message, actual, expected = _validate_result(
            workspace_dir=workspace_dir,
            test_case=test_case,
            stdout=process.stdout,
            process_result=result,
        )
        result["passed"] = passed
        result["message"] = message
        result["actual"] = actual
        result["expected"] = expected
        return result
    except subprocess.TimeoutExpired as exc:
        result["passed"] = False
        result["error"] = "Time Limit Exceeded"
        result["stdout"] = exc.stdout or ""
        result["stderr"] = exc.stderr or ""
        result["duration_ms"] = int((time.time() - started_at) * 1000)
        result["expected"] = test_case.get("expected")
        return result
    except Exception as exc:
        result["passed"] = False
        result["error"] = str(exc)
        result["duration_ms"] = int((time.time() - started_at) * 1000)
        result["expected"] = test_case.get("expected")
        return result


def main() -> None:
    workspace_dir = _workspace_dir()
    solution_path = workspace_dir / "solution.py"
    tests = _load_json(workspace_dir / "tests.json")
    config = _load_json(workspace_dir / "config.json")

    results = [_run_test(workspace_dir, solution_path, config, test_case) for test_case in tests]
    payload = {
        "submission_id": os.environ.get("SUBMISSION_ID", config.get("submission_id", "")),
        "status": determine_status(results),
        "results": results,
        "stdout": aggregate_output(results, "stdout"),
        "stderr": aggregate_output(results, "stderr"),
        "duration_ms": sum(result.get("duration_ms", 0) for result in results),
    }

    callback_error = post_results(os.environ.get("CALLBACK_URL", ""), payload)
    if callback_error:
        payload["stderr"] = "\n".join(filter(None, [payload.get("stderr"), callback_error]))

    print(json.dumps(payload))


if __name__ == "__main__":
    main()
