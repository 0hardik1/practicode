from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Problem, TestCase


PROBLEM_FILE = "problem.yaml"
KNOWN_TEST_FIELDS = {
    "id",
    "name",
    "input",
    "expected",
    "is_hidden",
    "is_sample",
    "ordinal",
    "validation_type",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(_read_text(path))


def _read_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(_read_text(path))
    return loaded or {}


def _load_problem_bundle(problem_dir: Path) -> dict[str, Any]:
    problem_meta = _read_yaml(problem_dir / PROBLEM_FILE)
    services_file = problem_meta.get("services_file")
    services = []
    if services_file:
        services_payload = _read_yaml(problem_dir / services_file)
        services = services_payload.get("services", [])

    starter_code: dict[str, str] = {}
    for language, relative_path in (problem_meta.get("starter_code") or {}).items():
        starter_code[language] = _read_text(problem_dir / relative_path)

    return {
        "id": problem_meta["id"],
        "slug": problem_meta.get("slug", problem_meta["id"]),
        "title": problem_meta["title"],
        "difficulty": problem_meta["difficulty"],
        "tags": problem_meta.get("tags", []),
        "description": _read_text(problem_dir / problem_meta["description_file"]),
        "api_docs": _read_text(problem_dir / problem_meta["api_docs_file"])
        if problem_meta.get("api_docs_file")
        else None,
        "starter_code": starter_code,
        "challenge_services": services,
        "time_limit_seconds": problem_meta.get("time_limit_seconds", 30),
        "memory_limit_mb": problem_meta.get("memory_limit_mb", 256),
        "tests": _read_json(problem_dir / problem_meta["test_cases_file"]),
    }


def iter_problem_dirs(problems_dir: Path) -> list[Path]:
    if not problems_dir.exists():
        return []
    return sorted(problem_file.parent for problem_file in problems_dir.glob(f"*/{PROBLEM_FILE}"))


def find_problem_dir(problems_dir: Path, identifier: str) -> Path | None:
    for problem_dir in iter_problem_dirs(problems_dir):
        bundle = _load_problem_bundle(problem_dir)
        if identifier in {bundle["id"], bundle["slug"]}:
            return problem_dir
    return None


async def _upsert_problem_bundle(session: AsyncSession, bundle: dict[str, Any]) -> None:
    problem = await session.get(Problem, bundle["id"])

    if problem is None:
        problem = Problem(id=bundle["id"], slug=bundle["slug"])
        session.add(problem)

    problem.slug = bundle["slug"]
    problem.title = bundle["title"]
    problem.difficulty = bundle["difficulty"]
    problem.tags = bundle["tags"]
    problem.description = bundle["description"]
    problem.api_docs = bundle["api_docs"]
    problem.starter_code = bundle["starter_code"]
    problem.challenge_services = bundle["challenge_services"]
    problem.time_limit_seconds = bundle["time_limit_seconds"]
    problem.memory_limit_mb = bundle["memory_limit_mb"]

    await session.flush()
    await session.execute(delete(TestCase).where(TestCase.problem_id == problem.id))

    for index, raw_test in enumerate(bundle["tests"], start=1):
        validation_config = {
            key: value
            for key, value in raw_test.items()
            if key not in KNOWN_TEST_FIELDS
        }
        session.add(
            TestCase(
                id=raw_test.get("id"),
                problem_id=problem.id,
                name=raw_test.get("name", raw_test.get("id", f"test-{index}")),
                input=raw_test.get("input", {}),
                expected=raw_test.get("expected"),
                is_hidden=raw_test.get("is_hidden", False),
                is_sample=raw_test.get("is_sample", False),
                ordinal=raw_test.get("ordinal", index),
                validation_type=raw_test.get("validation_type", "exact_match"),
                validation_config=validation_config,
            )
        )


async def seed_problem_from_dir(session: AsyncSession, problem_dir: Path) -> None:
    await _upsert_problem_bundle(session, _load_problem_bundle(problem_dir))
    await session.commit()


async def seed_problems(session: AsyncSession, problems_dir: Path) -> int:
    if not problems_dir.exists():
        return 0

    loaded_count = 0

    for problem_dir in iter_problem_dirs(problems_dir):
        await _upsert_problem_bundle(session, _load_problem_bundle(problem_dir))
        loaded_count += 1

    await session.commit()
    return loaded_count
