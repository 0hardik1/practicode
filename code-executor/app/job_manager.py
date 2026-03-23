from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from app.config import Settings
from app.schemas import ExecutionRequest, ExecutionStatus


class ExecutionStore:
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    def set(self, submission_id: str, payload: dict[str, Any]) -> None:
        self._data[submission_id] = payload

    def get(self, submission_id: str) -> dict[str, Any] | None:
        return self._data.get(submission_id)


class LocalJobManager:
    def __init__(self, settings: Settings, store: ExecutionStore) -> None:
        self._settings = settings
        self._store = store

    async def dispatch(self, request: ExecutionRequest) -> ExecutionStatus:
        initial = {"submission_id": request.submission_id, "status": "queued"}
        self._store.set(request.submission_id, initial)
        asyncio.create_task(self._run(request))
        return ExecutionStatus(**initial)

    async def _run(self, request: ExecutionRequest) -> None:
        workspace = Path(tempfile.mkdtemp(prefix=f"practicode-{request.submission_id[:8]}-"))
        self._store.set(request.submission_id, {"submission_id": request.submission_id, "status": "running"})

        try:
            self._write_workspace(request, workspace)
            env = os.environ.copy()
            env.update({key: str(value) for key, value in request.challenge_services.items()})
            env["SUBMISSION_ID"] = request.submission_id
            env["CALLBACK_URL"] = self._settings.api_callback_url
            env["WORKSPACE_DIR"] = str(workspace)

            process = await asyncio.create_subprocess_exec(
                self._settings.runner_python_bin,
                str(self._settings.runner_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(workspace),
                env=env,
            )
            timeout_seconds = max(10, request.time_limit_seconds * max(len(request.test_cases), 1) + 15)
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)

            payload = self._parse_harness_payload(
                request.submission_id,
                stdout.decode(),
                stderr.decode(),
            )
            self._store.set(request.submission_id, payload)
        except TimeoutError:
            self._store.set(
                request.submission_id,
                {
                    "submission_id": request.submission_id,
                    "status": "timeout",
                    "stderr": "Executor timed out waiting for harness completion.",
                    "results": [],
                },
            )
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def _write_workspace(self, request: ExecutionRequest, workspace: Path) -> None:
        (workspace / "solution.py").write_text(request.code, encoding="utf-8")
        (workspace / "tests.json").write_text(
            json.dumps([test.model_dump(mode="json") for test in request.test_cases], indent=2),
            encoding="utf-8",
        )
        (workspace / "config.json").write_text(
            json.dumps(
                {
                    "submission_id": request.submission_id,
                    "time_limit_seconds": request.time_limit_seconds,
                    "memory_limit_mb": request.memory_limit_mb,
                    "env": request.challenge_services,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def _parse_harness_payload(
        self,
        submission_id: str,
        stdout_text: str,
        stderr_text: str,
    ) -> dict[str, Any]:
        payload_text = stdout_text.strip()
        if not payload_text:
            return {
                "submission_id": submission_id,
                "status": "error",
                "stderr": stderr_text or "Harness produced no output.",
                "results": [],
            }

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            return {
                "submission_id": submission_id,
                "status": "error",
                "stdout": stdout_text,
                "stderr": stderr_text or "Harness output was not valid JSON.",
                "results": [],
            }

        payload.setdefault("submission_id", submission_id)
        if stderr_text:
            existing = payload.get("stderr") or ""
            payload["stderr"] = f"{existing}\n{stderr_text}".strip()
        return payload

