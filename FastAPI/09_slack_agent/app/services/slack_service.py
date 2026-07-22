from __future__ import annotations

from typing import Any, Awaitable, Callable
from uuid import uuid4

from app.db.repository import RunMetadata, RunRepository
from app.services.job_service import AgentJob, JobService, SlackMessageClient

Ack = Callable[..., Awaitable[Any]]


class SlackHandlers:
    def __init__(self, job_service: JobService, repository: RunRepository) -> None:
        self.job_service = job_service
        self.repository = repository

    async def botto_command(
        self,
        *,
        ack: Ack,
        command: dict[str, Any],
        client: SlackMessageClient,
    ) -> None:
        query = str(command.get("text") or "").strip()
        if not query:
            await ack("사용법: `/botto 반도체 수출`처럼 분석할 주제를 입력해 주세요.")
            return
        await ack()

        channel_id = str(command["channel_id"])
        user_id = str(command.get("user_id") or "") or None
        external_id = str(command.get("trigger_id") or "") or None
        if external_id and await self.repository.event_seen(external_id):
            return

        progress = await client.chat_postMessage(
            channel=channel_id,
            text=f"🔍 `{query}` 관련 경제 뉴스를 분석하고 있습니다.",
        )
        thread_ts = str(progress["ts"])
        thread_id = f"slack:{channel_id}:{thread_ts}"
        run_id = uuid4()
        created = await self.repository.create_if_missing(
            run_id=run_id,
            thread_id=thread_id,
            query=query,
            metadata=RunMetadata(
                user_id=user_id,
                channel_id=channel_id,
                thread_ts=thread_ts,
                external_event_id=external_id,
            ),
        )
        if not created:
            return
        await self.job_service.enqueue(
            AgentJob(
                run_id=run_id,
                query=query,
                thread_id=thread_id,
                channel_id=channel_id,
                response_thread_ts=thread_ts,
                user_id=user_id,
                external_event_id=external_id,
            )
        )

    async def message_event(
        self,
        *,
        event: dict[str, Any],
        body: dict[str, Any],
        client: SlackMessageClient,
    ) -> None:
        if event.get("bot_id") or event.get("subtype"):
            return
        channel_id = str(event.get("channel") or "")
        thread_ts = str(event.get("thread_ts") or "")
        query = str(event.get("text") or "").strip()
        if not channel_id or not thread_ts or not query:
            return
        if not await self.repository.thread_exists(channel_id, thread_ts):
            return

        external_id = str(
            body.get("event_id") or event.get("client_msg_id") or event.get("ts") or ""
        )
        if external_id and await self.repository.event_seen(external_id):
            return

        run_id = uuid4()
        thread_id = f"slack:{channel_id}:{thread_ts}"
        created = await self.repository.create_if_missing(
            run_id=run_id,
            thread_id=thread_id,
            query=query,
            metadata=RunMetadata(
                user_id=str(event.get("user") or "") or None,
                channel_id=channel_id,
                thread_ts=thread_ts,
                external_event_id=external_id or None,
            ),
        )
        if not created:
            return
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="🔄 후속 질문을 분석하고 있습니다.",
        )
        await self.job_service.enqueue(
            AgentJob(
                run_id=run_id,
                query=query,
                thread_id=thread_id,
                channel_id=channel_id,
                response_thread_ts=thread_ts,
                user_id=str(event.get("user") or "") or None,
                external_event_id=external_id or None,
            )
        )

