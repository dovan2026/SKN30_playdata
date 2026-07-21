from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from langchain_core.messages import HumanMessage

from app.db.repository import RunMetadata, RunRepository
from app.schemas.agent import AgentErrorState, AgentResponse
from app.schemas.news import Source
from app.services.errors import AgentExecutionError


@dataclass(slots=True)
class AgentRunContext:
    user_id: str | None = None
    channel_id: str | None = None
    thread_ts: str | None = None
    external_event_id: str | None = None


class AgentService:
    def __init__(self, graph: Any, repository: RunRepository | None = None) -> None:
        self.graph = graph
        self.repository = repository

    async def run(
        self,
        query: str,
        thread_id: str | None = None,
        *,
        run_id: UUID | None = None,
        context: AgentRunContext | None = None,
    ) -> AgentResponse:
        run_id = run_id or uuid4()
        thread_id = thread_id or str(uuid4())
        context = context or AgentRunContext()
        if self.repository is not None:
            await self.repository.create_if_missing(
                run_id=run_id,
                thread_id=thread_id,
                query=query,
                metadata=RunMetadata(
                    user_id=context.user_id,
                    channel_id=context.channel_id,
                    thread_ts=context.thread_ts,
                    external_event_id=context.external_event_id,
                ),
            )
            await self.repository.mark_running(run_id)
        try:
            # graph.invoke
            result = 


            if result.get("error"):
                error = AgentErrorState.model_validate(result["error"])
                raise AgentExecutionError(
                    run_id=run_id,
                    code=error.code,
                    message=error.message,
                    retryable=error.retryable,
                )
            
            # AgentResponse
            response = 


            
            if self.repository is not None:
                await self.repository.mark_success(run_id, response.answer)
            return response
        except AgentExecutionError as exc:
            if self.repository is not None:
                await self.repository.mark_failed(
                    run_id,
                    code=exc.code,
                    message=exc.message,
                )
            raise
        except Exception as exc:
            wrapped = AgentExecutionError(
                run_id=run_id,
                code="analysis_failed",
                message="에이전트 실행 중 예상하지 못한 오류가 발생했습니다.",
                retryable=True,
            )
            if self.repository is not None:
                await self.repository.mark_failed(
                    run_id,
                    code=wrapped.code,
                    message=wrapped.message,
                )
            raise wrapped from exc
