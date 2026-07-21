from __future__ import annotations

import argparse
import asyncio
import json

from app.core.config import get_settings
from app.tools.news_search import TavilyNewsSearch


async def main() -> None:
    parser = argparse.ArgumentParser(description="Tavily 뉴스 검색 smoke test")
    parser.add_argument("query")
    args = parser.parse_args()
    settings = get_settings()
    if settings.tavily_api_key is None:
        raise SystemExit("TAVILY_API_KEY가 필요합니다.")
    provider = TavilyNewsSearch(
        api_key=settings.tavily_api_key.get_secret_value(),
        max_attempts=settings.search_max_attempts,
    )
    items = await provider.search(
        args.query,
        limit=settings.news_limit,
        days=settings.news_days,
    )
    print(json.dumps([item.model_dump(mode="json") for item in items], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

