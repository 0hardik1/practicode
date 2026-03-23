from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    difficulty: Mapped[str] = mapped_column(String(20))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    description: Mapped[str] = mapped_column(Text)
    starter_code: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    api_docs: Mapped[str | None] = mapped_column(Text, nullable=True)
    challenge_services: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    time_limit_seconds: Mapped[int] = mapped_column(Integer, default=30)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="TestCase.ordinal",
    )


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    problem_id: Mapped[str] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), default="")
    input: Mapped[Any] = mapped_column(JSON)
    expected: Mapped[Any] = mapped_column(JSON)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    validation_type: Mapped[str] = mapped_column(String(50), default="exact_match")
    validation_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    problem: Mapped[Problem] = relationship(back_populates="test_cases")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    problem_id: Mapped[str] = mapped_column(ForeignKey("problems.id"), index=True)
    code: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(20), default="python")
    status: Mapped[str] = mapped_column(String(30), default="queued")
    is_submit: Mapped[bool] = mapped_column(Boolean, default=False)
    results: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

