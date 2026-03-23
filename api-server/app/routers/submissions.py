from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import async_session_maker, get_session
from app.models import Problem, Submission, TestCase
from app.schemas import (
    CodeSubmissionRequest,
    ExecutionCallback,
    QueuedSubmissionResponse,
    SubmissionDetail,
)
from app.services.executor_client import ExecutorClient


router = APIRouter(prefix="/api", tags=["submissions"])
TERMINAL_STATUSES = {"passed", "failed", "error", "timeout"}


async def _get_problem(identifier: str, session: AsyncSession) -> Problem:
    result = await session.execute(
        select(Problem).where(or_(Problem.id == identifier, Problem.slug == identifier))
    )
    problem = result.scalar_one_or_none()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


def _build_challenge_env(
    services: list[dict[str, Any]],
    execution_environment: str,
) -> dict[str, str]:
    env: dict[str, str] = {}
    for service in services or []:
        env.update(service.get("env", {}))
        selected_env = service.get(f"{execution_environment}_env", {})
        env.update(selected_env)
        if execution_environment == "cluster":
            if service.get("service_url_env") and service.get("service_url"):
                env[service["service_url_env"]] = service["service_url"]
        else:
            if service.get("local_url_env") and service.get("local_url"):
                env[service["local_url_env"]] = service["local_url"]
            elif service.get("service_url_env") and service.get("service_url"):
                env[service["service_url_env"]] = service["service_url"]
    return env


def _serialize_test(
    test: TestCase,
    execution_environment: str,
) -> dict[str, Any]:
    payload = {
        "id": test.id,
        "name": test.name,
        "input": test.input,
        "expected": test.expected,
        "validation_type": test.validation_type,
    }
    validation_config = dict(test.validation_config or {})
    if execution_environment == "cluster":
        cluster_endpoint = validation_config.pop("validation_endpoint_service", None)
        if cluster_endpoint:
            validation_config["validation_endpoint"] = cluster_endpoint
    else:
        local_endpoint = validation_config.pop("validation_endpoint_local", None)
        if local_endpoint:
            validation_config["validation_endpoint"] = local_endpoint
    payload.update(validation_config)
    return payload


async def _queue_submission(
    problem: Problem,
    submission_request: CodeSubmissionRequest,
    tests: list[TestCase] | list[dict[str, Any]],
    is_submit: bool,
    session: AsyncSession,
) -> QueuedSubmissionResponse:
    submission = Submission(
        problem_id=problem.id,
        code=submission_request.code,
        language=submission_request.language,
        status="queued",
        is_submit=is_submit,
    )
    session.add(submission)
    await session.commit()
    await session.refresh(submission)

    execution_environment = get_settings().execution_environment
    payload = {
        "submission_id": submission.id,
        "problem_id": problem.id,
        "code": submission.code,
        "language": submission.language,
        "test_cases": [
            _serialize_test(test, execution_environment=execution_environment)
            if isinstance(test, TestCase)
            else test
            for test in tests
        ],
        "time_limit_seconds": problem.time_limit_seconds,
        "memory_limit_mb": problem.memory_limit_mb,
        "challenge_services": _build_challenge_env(
            problem.challenge_services or [],
            execution_environment=execution_environment,
        ),
    }

    try:
        settings = get_settings()
        await ExecutorClient(settings).execute(payload)
    except Exception as exc:
        submission.status = "error"
        submission.stderr = f"Executor request failed: {exc}"
        await session.commit()
        raise HTTPException(status_code=502, detail="Failed to dispatch execution") from exc

    return QueuedSubmissionResponse(
        id=submission.id,
        status=submission.status,
        problem_id=problem.id,
    )


async def _load_problem_tests(
    problem_id: str,
    session: AsyncSession,
    include_hidden: bool,
) -> list[TestCase]:
    query = (
        select(TestCase)
        .where(TestCase.problem_id == problem_id)
        .order_by(TestCase.ordinal)
    )
    if not include_hidden:
        query = query.where(TestCase.is_hidden.is_(False))
    return list((await session.execute(query)).scalars().all())


async def _build_program_run_test(
    problem_id: str,
    request: CodeSubmissionRequest,
    session: AsyncSession,
) -> list[dict[str, Any]]:
    sample_input = request.input
    if sample_input is None:
        visible_tests = await _load_problem_tests(problem_id, session, include_hidden=False)
        sample_input = visible_tests[0].input if visible_tests else {}

    return [
        {
            "id": "__program_output__",
            "name": "Program output",
            "input": sample_input,
            "expected": None,
            "validation_type": "program_output",
        }
    ]


@router.post("/problems/{problem_id}/run", response_model=QueuedSubmissionResponse)
async def run_visible_tests(
    problem_id: str,
    request: CodeSubmissionRequest,
    session: AsyncSession = Depends(get_session),
) -> QueuedSubmissionResponse:
    problem = await _get_problem(problem_id, session)
    tests = await _load_problem_tests(problem.id, session, include_hidden=False)
    return await _queue_submission(problem, request, tests=tests, is_submit=False, session=session)


@router.post("/problems/{problem_id}/execute", response_model=QueuedSubmissionResponse)
async def run_program_once(
    problem_id: str,
    request: CodeSubmissionRequest,
    session: AsyncSession = Depends(get_session),
) -> QueuedSubmissionResponse:
    problem = await _get_problem(problem_id, session)
    tests = await _build_program_run_test(problem.id, request, session)
    return await _queue_submission(problem, request, tests=tests, is_submit=False, session=session)


@router.post("/problems/{problem_id}/submit", response_model=QueuedSubmissionResponse)
async def submit_all_tests(
    problem_id: str,
    request: CodeSubmissionRequest,
    session: AsyncSession = Depends(get_session),
) -> QueuedSubmissionResponse:
    problem = await _get_problem(problem_id, session)
    tests = await _load_problem_tests(problem.id, session, include_hidden=True)
    return await _queue_submission(problem, request, tests=tests, is_submit=True, session=session)


@router.get("/submissions/{submission_id}", response_model=SubmissionDetail)
async def get_submission(
    submission_id: str,
    session: AsyncSession = Depends(get_session),
) -> SubmissionDetail:
    submission = await session.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return SubmissionDetail.model_validate(submission)


@router.get("/submissions/{submission_id}/stream")
async def stream_submission(submission_id: str) -> StreamingResponse:
    async def event_stream():
        previous_payload = None
        while True:
            async with async_session_maker() as session:
                submission = await session.get(Submission, submission_id)
                if submission is None:
                    yield "event: error\ndata: {\"detail\": \"Submission not found\"}\n\n"
                    return

                payload = SubmissionDetail.model_validate(submission).model_dump(mode="json")
                encoded = json.dumps(payload)
                if encoded != previous_payload:
                    yield f"data: {encoded}\n\n"
                    previous_payload = encoded

                if submission.status in TERMINAL_STATUSES:
                    return

            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/internal/results")
async def receive_execution_results(
    callback: ExecutionCallback,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    submission = await session.get(Submission, callback.submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    submission.status = callback.status
    submission.results = [result.model_dump(mode="json") for result in callback.results]
    submission.stdout = callback.stdout
    submission.stderr = callback.stderr
    submission.duration_ms = callback.duration_ms

    await session.commit()
    return {"ok": True}
