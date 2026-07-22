from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(255), index=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    thread_ts: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    query: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), index=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_event_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

