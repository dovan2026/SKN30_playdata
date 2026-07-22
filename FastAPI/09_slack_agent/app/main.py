from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_sdk.web.async_client import AsyncWebClient

from app.agent.graph import create_graph
from app.agent.model import OpenAIAgentModel
from app.api.agent import router as agent_router
from app.api.health import router as health_router
from app.api.slack import router as slack_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.repository import RunRepository
from app.schemas.agent import ErrorDetail, ErrorResponse
from app.services.agent_service import AgentService
from app.services.errors import AgentExecutionError
from app.services.job_service import JobService
from app.services.slack_service import SlackHandlers
from app.slack_app import create_slack_app
from app.tools.news_search import TavilyNewsSearch


def create_app(
    *,
    settings: Settings | None = None,
    agent_service: AgentService | Any | None = None,
    repository: RunRepository | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(resolved_settings.log_level)
        app.state.settings = resolved_settings
        app.state.worker_ready = False
        app.state.slack_request_handler = None

        owned_repository = repository is None
        run_repository = repository or RunRepository.from_url(
            resolved_settings.run_database_url
        )
        await run_repository.setup()        # 실행 기록을 저장할 DB 테이블 등 준비
        app.state.run_repository = run_repository

        checkpoint_context = None
        job_service: JobService | None = None
        service = agent_service
        try:
            if (
                service is None
                and resolved_settings.openai_api_key is not None
                and resolved_settings.tavily_api_key is not None
            ):
                checkpoint_path = Path(resolved_settings.checkpoint_db_path)
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                checkpoint_context = AsyncSqliteSaver.from_conn_string(
                    str(checkpoint_path)
                )
                checkpointer = await checkpoint_context.__aenter__()
                await checkpointer.setup()
                model = OpenAIAgentModel(
                    api_key=resolved_settings.openai_api_key.get_secret_value(),  # type: ignore[union-attr]
                    model=resolved_settings.openai_model,
                )
                news_provider = TavilyNewsSearch(
                    api_key=resolved_settings.tavily_api_key.get_secret_value(),  # type: ignore[union-attr]
                    max_attempts=resolved_settings.search_max_attempts,
                )
                graph = create_graph(
                    model=model,
                    news_provider=news_provider,
                    news_limit=resolved_settings.news_limit,
                    news_days=resolved_settings.news_days,
                    checkpointer=checkpointer,
                )
                service = AgentService(graph, repository=run_repository)

            app.state.agent_service = service
            app.state.worker_ready = service is not None

            if service is not None and resolved_settings.slack_configured:
                slack_client = AsyncWebClient(
                    token=resolved_settings.slack_bot_token.get_secret_value()  # type: ignore[union-attr]
                )
                job_service = JobService(service, slack_client)
                await job_service.start()
                handlers = SlackHandlers(job_service, run_repository)
                slack_app = create_slack_app(
                    resolved_settings,
                    handlers,
                    client=slack_client,
                )
                app.state.slack_request_handler = AsyncSlackRequestHandler(slack_app)
                app.state.job_service = job_service

            yield
        # 서버 종료 시 자원 정리
        finally:
            app.state.worker_ready = False
            if job_service is not None:
                await job_service.stop()
            if checkpoint_context is not None:
                await checkpoint_context.__aexit__(None, None, None)
            if owned_repository:
                await run_repository.close()

    # FastAPI 애플리케이션 객체를 만들고 세 종류의 API 라우터를 등록
    application = FastAPI(
        title = "slack 에이전트 챗봇",
        version = "0.1.0",
        lifespan=lifespan   # FastAPI 서버가 시작되고 종료될 때 실행할 초기화호, 정리 함수를 등록하는 코드
    )

    # 기능별 API 라우터를 application에 등록
    application.include_router(health_router)
    application.include_router(agent_router)
    application.include_router(slack_router)

    # AgentExecutionError가 발생했을 때 실행되는 예외 처리 handler
    @application.exception_handler(AgentExecutionError)
    async def handle_agent_error(
        request: Request,
        exc: AgentExecutionError,
    ) -> JSONResponse:
        payload = ErrorResponse(
            detail=ErrorDetail(
                run_id=exc.run_id,
                code=exc.code,
                message=exc.message,
                retryable=exc.retryable,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=payload.model_dump(mode="json"),
        )

    return application


app = create_app()