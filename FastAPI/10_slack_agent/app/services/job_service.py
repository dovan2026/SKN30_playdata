from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from app.services.agent_service import AgentRunContext, AgentService
from app.services.errors import AgentExecutionError

logger = logging.getLogger(__name__)


class SlackMessageClient(Protocol):
    async def chat_postMessage(self, **kwargs: Any) -> Any: ...


@dataclass(slots=True)
class AgentJob:
    run_id: UUID
    query: str
    thread_id: str
    channel_id: str
    response_thread_ts: str
    user_id: str | None = None
    external_event_id: str | None = None


class JobService:
    def __init__(self, agent_service: AgentService, slack_client: SlackMessageClient) -> None:
        self.agent_service = agent_service
        self.slack_client = slack_client
        self.queue: asyncio.Queue[AgentJob] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None

    @property
    def ready(self) -> bool:
        return self._worker is not None and not self._worker.done()

    async def start(self) -> None:
        if not self.ready:
            self._worker = asyncio.create_task(self._run_worker(), name="agent-job-worker")

    async def stop(self) -> None:
        if self._worker is None:
            return
        self._worker.cancel()
        try:
            await self._worker
        except asyncio.CancelledError:
            pass
        self._worker = None

    async def enqueue(self, job: AgentJob) -> None:
        await self.queue.put(job)

    async def _run_worker(self) -> None:
        while True:
            job = await self.queue.get()
            try:
                result = await self.agent_service.run(
                    query=job.query,
                    thread_id=job.thread_id,
                    run_id=job.run_id,
                    context=AgentRunContext(
                        user_id=job.user_id,
                        channel_id=job.channel_id,
                        thread_ts=job.response_thread_ts,
                        external_event_id=job.external_event_id,
                    ),
                )
                await self.slack_client.chat_postMessage(
                    channel=job.channel_id,
                    thread_ts=job.response_thread_ts,
                    text=result.answer,
                )
            except AgentExecutionError as exc:
                await self.slack_client.chat_postMessage(
                    channel=job.channel_id,
                    thread_ts=job.response_thread_ts,
                    text=(
                        "⚠️ 뉴스 근거를 확보하거나 분석하는 데 실패했습니다.\n"
                        f"사유: {exc.message}\n오류 코드: `{exc.code}`\n"
                        f"실행 ID: `{exc.run_id}`"
                    ),
                )
            except Exception:
                logger.exception("Unhandled job failure", extra={"run_id": str(job.run_id)})
                repository = self.agent_service.repository
                if repository is not None:
                    await repository.mark_failed(
                        job.run_id,
                        code="job_failed",
                        message="백그라운드 작업 처리 중 오류가 발생했습니다.",
                    )
                await self.slack_client.chat_postMessage(
                    channel=job.channel_id,
                    thread_ts=job.response_thread_ts,
                    text=(
                        "⚠️ 백그라운드 작업 처리 중 오류가 발생했습니다.\n"
                        f"실행 ID: `{job.run_id}`"
                    ),
                )
            finally:
                self.queue.task_done()
