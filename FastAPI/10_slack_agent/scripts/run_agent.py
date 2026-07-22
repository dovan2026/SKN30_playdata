from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.agent.graph import create_graph
from app.agent.model import OpenAIAgentModel
from app.core.config import get_settings
from app.services.agent_service import AgentService
from app.tools.news_search import TavilyNewsSearch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="경제 뉴스 LangGraph 에이전트 실행")
    parser.add_argument("query", help="분석할 경제 뉴스 주제")
    parser.add_argument("--thread-id", default=None, help="후속 대화용 thread_id")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    missing = [
        name
        for name in ("OPENAI_API_KEY", "TAVILY_API_KEY")
        if name in settings.missing_agent_settings()
    ]
    if missing:
        raise SystemExit(f"필수 환경변수가 없습니다: {', '.join(missing)}")

    checkpoint_path = Path(settings.checkpoint_db_path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
        await checkpointer.setup()
        graph = create_graph(
            model=OpenAIAgentModel(
                api_key=settings.openai_api_key.get_secret_value(),  # type: ignore[union-attr]
                model=settings.openai_model,
            ),
            news_provider=TavilyNewsSearch(
                api_key=settings.tavily_api_key.get_secret_value(),  # type: ignore[union-attr]
                max_attempts=settings.search_max_attempts,
            ),
            news_limit=settings.news_limit,
            news_days=settings.news_days,
            checkpointer=checkpointer,
        )
        result = await AgentService(graph).run(args.query, thread_id=args.thread_id)
        print(result.answer)
        print(f"\nthread_id: {result.thread_id}")
        print(f"run_id: {result.run_id}")


if __name__ == "__main__":
    asyncio.run(main())

