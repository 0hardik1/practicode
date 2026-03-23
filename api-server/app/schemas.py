from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ProblemSummary(BaseModel):
    id: str
    slug: str
    title: str
    difficulty: str
    tags: list[str]
    time_limit_seconds: int
    memory_limit_mb: int

    model_config = ConfigDict(from_attributes=True)


class TestCaseView(BaseModel):
    id: str
    name: str
    input: Any
    expected: Any
    is_sample: bool
    ordinal: int
    validation_type: str

    model_config = ConfigDict(from_attributes=True)


class ProblemDetail(ProblemSummary):
    description: str
    starter_code: dict[str, str]
    api_docs: str | None = None
    visible_tests: list[TestCaseView] = Field(default_factory=list)


class ProblemApiDocs(BaseModel):
    problem_id: str
    api_docs: str | None = None


class ProblemFileNode(BaseModel):
    name: str
    path: str
    kind: Literal["file", "directory"]
    editable: bool = False
    is_binary: bool = False
    mime_type: str | None = None
    size: int | None = None
    children: list["ProblemFileNode"] = Field(default_factory=list)


class ProblemFileTreeResponse(BaseModel):
    problem_id: str
    root: ProblemFileNode


class ProblemFileContent(BaseModel):
    problem_id: str
    path: str
    name: str
    editable: bool
    is_binary: bool
    mime_type: str | None = None
    size: int
    text_content: str | None = None
    base64_content: str | None = None


class ProblemFileUpdateRequest(BaseModel):
    content: str


class ProblemFileCreateRequest(BaseModel):
    name: str
    kind: Literal["file", "directory"]
    parent_path: str | None = None


class ProblemFileCreateResponse(BaseModel):
    problem_id: str
    path: str
    kind: Literal["file", "directory"]


class CodePosition(BaseModel):
    line: int = Field(ge=1)
    column: int = Field(ge=1)


class IntellisenseTextEdit(BaseModel):
    start_line: int = Field(ge=1)
    start_column: int = Field(ge=1)
    end_line: int = Field(ge=1)
    end_column: int = Field(ge=1)
    text: str


class PythonCompletionItem(BaseModel):
    label: str
    kind: str
    detail: str | None = None
    documentation: str | None = None
    insert_text: str | None = None
    sort_text: str | None = None
    additional_text_edits: list[IntellisenseTextEdit] = Field(default_factory=list)


class PythonCompletionRequest(BaseModel):
    code: str
    path: str = "solution.py"
    position: CodePosition


class PythonCompletionResponse(BaseModel):
    items: list[PythonCompletionItem] = Field(default_factory=list)


class PythonHoverRequest(BaseModel):
    code: str
    path: str = "solution.py"
    position: CodePosition


class PythonHoverResponse(BaseModel):
    contents: list[str] = Field(default_factory=list)


class CodeSubmissionRequest(BaseModel):
    code: str
    language: str = "python"
    input: Any | None = None


class SubmissionResult(BaseModel):
    test_id: str
    name: str
    passed: bool
    duration_ms: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    exit_code: int | None = None
    message: str | None = None
    error: str | None = None
    actual: Any | None = None
    expected: Any | None = None


class QueuedSubmissionResponse(BaseModel):
    id: str
    status: str
    problem_id: str


class SubmissionDetail(BaseModel):
    id: str
    problem_id: str
    language: str
    status: str
    is_submit: bool
    results: list[SubmissionResult] | None = None
    stdout: str | None = None
    stderr: str | None = None
    duration_ms: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionCallback(BaseModel):
    submission_id: str
    status: str
    results: list[SubmissionResult]
    stdout: str | None = None
    stderr: str | None = None
    duration_ms: int | None = None


ProblemFileNode.model_rebuild()
