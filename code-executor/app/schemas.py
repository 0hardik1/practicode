from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecutionTestCase(BaseModel):
    id: str
    name: str
    input: Any = Field(default_factory=dict)
    expected: Any = None
    validation_type: str = "exact_match"

    model_config = ConfigDict(extra="allow")


class ExecutionRequest(BaseModel):
    submission_id: str
    problem_id: str
    code: str
    language: str = "python"
    test_cases: list[ExecutionTestCase]
    time_limit_seconds: int = 30
    memory_limit_mb: int = 256
    challenge_services: dict[str, str] = Field(default_factory=dict)


class ExecutionStatus(BaseModel):
    submission_id: str
    status: str
    results: list[dict[str, Any]] | None = None
    stdout: str | None = None
    stderr: str | None = None
    duration_ms: int | None = None

