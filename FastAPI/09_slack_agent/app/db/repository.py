from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import AgentRun, Base


@dataclass(slots=True)
class RunMetadata:
    user_id: str | None = None
    channel_id: str | None = None
    thread_ts: str | None = None
    external_event_id: str | None = None


class RunRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
        self._sessions = async_sessionmaker(engine, expire_on_commit=False)

    @classmethod
    def from_url(cls, url: str) -> "RunRepository":
        if url.startswith("sqlite") and "///" in url:
            raw_path = url.split("///", 1)[1]
            if raw_path and raw_path != ":memory:":
                Path(raw_path).parent.mkdir(parents=True, exist_ok=True)
        return cls(create_async_engine(url))

    async def setup(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with self._sessions() as session:
            await session.execute(
                update(AgentRun)
                .where(AgentRun.status.in_(["queued", "running"]))
                .values(
                    status="interrupted",
                    error_code="process_restarted",
                    error_message="프로세스 재시작으로 작업이 중단되었습니다.",
                    completed_at=datetime.now(UTC),
                )
            )
            await session.commit()

    async def close(self) -> None:
        await self.engine.dispose()

    async def create_if_missing(
        self,
        *,
        run_id: UUID,
        thread_id: str,
        query: str,
        metadata: RunMetadata | None = None,
    ) -> bool:
        metadata = metadata or RunMetadata()
        async with self._sessions() as session:
            session.add(
                AgentRun(
                    run_id=str(run_id),
                    thread_id=thread_id,
                    query=query,
                    status="queued",
                    user_id=metadata.user_id,
                    channel_id=metadata.channel_id,
                    thread_ts=metadata.thread_ts,
                    external_event_id=metadata.external_event_id,
                )
            )
            try:
                await session.commit()
                return True
            except IntegrityError:
                await session.rollback()
                return False

    async def mark_running(self, run_id: UUID) -> None:
        await self._update(run_id, status="running")

    async def mark_success(self, run_id: UUID, answer: str) -> None:
        await self._update(
            run_id,
            status="success",
            answer=answer,
            completed_at=datetime.now(UTC),
        )

    async def mark_failed(
        self,
        run_id: UUID,
        *,
        code: str,
        message: str,
    ) -> None:
        await self._update(
            run_id,
            status="failed",
            error_code=code,
            error_message=message,
            completed_at=datetime.now(UTC),
        )

    async def _update(self, run_id: UUID, **values: object) -> None:
        async with self._sessions() as session:
            await session.execute(
                update(AgentRun).where(AgentRun.run_id == str(run_id)).values(**values)
            )
            await session.commit()

    async def thread_exists(self, channel_id: str, thread_ts: str) -> bool:
        async with self._sessions() as session:
            result = await session.scalar(
                select(AgentRun.run_id)
                .where(
                    AgentRun.channel_id == channel_id,
                    AgentRun.thread_ts == thread_ts,
                )
                .limit(1)
            )
            return result is not None

    async def event_seen(self, external_event_id: str) -> bool:
        async with self._sessions() as session:
            result = await session.scalar(
                select(AgentRun.run_id)
                .where(AgentRun.external_event_id == external_event_id)
                .limit(1)
            )
            return result is not None

