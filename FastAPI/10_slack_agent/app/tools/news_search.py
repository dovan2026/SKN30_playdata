from __future__ import annotations

import asyncio
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Protocol
from urllib.parse import urldefrag

from tavily import AsyncTavilyClient

from app.schemas.news import NewsItem


class NewsSearchError(RuntimeError):
    code = "search_unavailable"
    retryable = True


class NoNewsResultsError(NewsSearchError):
    code = "no_sources"
    retryable = False


class NewsSearchProvider(Protocol):
    async def search(
        self,
        query: str,
        limit: int = 5,
        days: int = 7,
    ) -> list[NewsItem]: ...


class TavilyClientProtocol(Protocol):
    async def search(self, query: str, **kwargs: Any) -> dict[str, Any]: ...


def _parse_date(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    cleaned = value.strip()
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError:
        try:
            return parsedate_to_datetime(cleaned)
        except (TypeError, ValueError, OverflowError):
            return None


def _normalize_results(payload: dict[str, Any], limit: int) -> list[NewsItem]:
    """Tavily 응답을 애플리케이션의 NewsItem 목록으로 변환함."""
    items: list[NewsItem] = []
    seen_urls: set[str] = set()  # 동일 url이면 여러 번 포함되는 것을 방지
    for raw in payload.get("results") or []:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "").strip()

        # URL의 #fragment 부분 제거.
        # 예: https://example.com/news#section -> https://example.com/news
        url = urldefrag(str(raw.get("url") or "").strip())[0]

        # 제목이나 URL이 없거나 이미 처리한 URL이면 제외
        if not title or not url or url in seen_urls:
            continue
        seen_urls.add(url)
        items.append(
            NewsItem(
                title=title,
                url=url,
                content=str(raw.get("content") or "").strip(),
                published_at=_parse_date(
                    raw.get("published_date") or raw.get("published_at")
                ),
                score=raw.get("score") if isinstance(raw.get("score"), (int, float)) else None,
            )
        )

        # 요청한 최대 갯수에 도달하면 처리를 종료
        if len(items) >= limit:
            break
    return items


class TavilyNewsSearch:
    """Tavily API를 사용하는 뉴스 검색 제공자."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        client: TavilyClientProtocol | None = None,
        max_attempts: int = 2,
    ) -> None:
        if client is None and not api_key:
            raise ValueError("TAVILY_API_KEY is required")

        # 전달받은 클라이언트가 있으면 사용하고, 없으면 API 키를 사용해 실제 Tavily클라이언트를 생성.
        self._client = client or AsyncTavilyClient(api_key=api_key)
        self._max_attempts = max_attempts

    # 뉴스 검색 메서드
    async def search(
        self,
        query: str,
        limit: int = 5,
        days: int = 7,
    ) -> list[NewsItem]:
        """Tavily에서 최근 뉴스를 검색함."""
        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                payload = await self._client.search(
                    query=query,
                    topic="news",  # 뉴스 검색 모드
                    days=days,  # 최근 몇 일 이내의 뉴스인지
                    max_results=limit,  # 최대 검색 결과 개수
                    search_depth="basic",
                    include_answer=False,
                    include_raw_content=False,
                    include_images=False,
                )
                items = _normalize_results(payload, limit)
                if not items:
                    raise NoNewsResultsError(
                        "검색 결과에서 분석 가능한 출처를 찾지 못했습니다."
                    )
                return items
            except NoNewsResultsError:
                raise
            except Exception as exc:  # SDK exposes provider-specific error classes.
                last_error = exc
                if attempt < self._max_attempts:
                    await asyncio.sleep(0.25 * attempt)
        raise NewsSearchError("뉴스 검색 서비스 호출에 실패했습니다.") from last_error


async def search_news(
    query: str,
    limit: int = 5,
    days: int = 7,
    *,
    provider: NewsSearchProvider,
) -> list[NewsItem]:
    """Provider-independent news search tool interface."""

    return await provider.search(query=query, limit=limit, days=days)
