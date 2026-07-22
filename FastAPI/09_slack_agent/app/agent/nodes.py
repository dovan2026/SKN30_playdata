from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage

from app.agent.model import AgentModel
from app.agent.state import AgentState
from app.schemas.agent import AgentErrorState, EconomicAnalysis, QueryPlan
from app.schemas.news import NewsItem, Source
from app.tools.news_search import (
    NewsSearchError,
    NewsSearchProvider,
    NoNewsResultsError,
    search_news,
)


def _error(code: str, message: str, retryable: bool) -> dict[str, Any]:
    return AgentErrorState(
        code=code,
        message=message,
        retryable=retryable,
    ).model_dump()


# 문자열 목록을 Slack에서 읽기 쉬운 bullets 목록으로 만듦
def _bullets(items: list[str]) -> str:
    return "\n".join(f"• {item}" for item in items)



def format_analysis(analysis: EconomicAnalysis, sources: list[Source]) -> str:
    # 모든 응답에서 공통으로 보여 줄 분석 항목을 순서대로 구성
    sections = [
        f"📊 *{analysis.title}*",
        f"*1. 핵심 뉴스*\n{_bullets(analysis.core_news)}",
        f"*2. 사실 요약*\n{_bullets(analysis.fact_summary)}",
        f"*3. 거시경제 영향*\n{_bullets(analysis.macro_impacts)}",
        f"*4. 산업 영향*\n{_bullets(analysis.industry_impacts)}",
        f"*5. 상방 요인*\n{_bullets(analysis.upside_factors)}",
        f"*6. 하방 위험*\n{_bullets(analysis.downside_risks)}",
    ]
    if analysis.caveats:
        sections.append(f"*분석 한계*\n{_bullets(analysis.caveats)}")
    # Slack 링크 문법인 <URL|표시할 제목> 형식으로 출처를 만든다.
    source_lines = [
        f"[{index}] <{source.url}|{source.title.replace('|', ' ')}>"
        for index, source in enumerate(sources, start=1)
    ]
    sections.append("*7. 참고 출처*\n" + "\n".join(source_lines))
    return "\n\n".join(sections)


def create_nodes(
    *,
    model: AgentModel,
    news_provider: NewsSearchProvider,
    news_limit: int = 5,
    news_days: int = 7,
) -> dict[str, Callable[..., Any]]:
    # 첫 질문은 검색을 강제하고, 출처가 있는 후속 질문은 모델에게 계획을 맡긴다.
    async def plan_query(state: AgentState) -> dict[str, Any]:
        query = state.get("query", "").strip()
        if not query:
            return {
                "error": _error("invalid_state", "질문이 비어 있습니다.", False)
            }
        has_sources = bool(state.get("search_results"))
        if not has_sources:
            # 최초 질문에는 참고할 출처가 없으므로 사용자 질문을 그대로 검색
            plan = QueryPlan(
                needs_search=True,
                search_query=query,
                analysis_focus=query,
            )
            return {"plan": plan.model_dump(), "error": None}
        try:
            # 기존 출처가 있으면 재검색할지, 기존 자료를 재사용할지 LLM이 판단
            plan = await model.plan(
                query=query,
                messages=state.get("messages", []),
                has_sources=has_sources,
            )
            return {"plan": plan.model_dump(), "error": None}
        except Exception:
            return {
                "error": _error(
                    "planning_failed",
                    "후속 질문의 검색 계획을 만들지 못했습니다.",
                    True,
                )
            }
    
    # 계획 에이전트에서 만든 검색어로 뉴스를 수집하고 분석용 데이터와 출처를 저장 
    async def search_news_node(state: AgentState) -> dict[str, Any]:
        try:
            plan = QueryPlan.model_validate(state.get("plan"))
            items = await search_news(
                plan.search_query,
                limit=news_limit,
                days=news_days,
                provider=news_provider,
            )
            return {
                "search_results": [item.model_dump(mode="json") for item in items],
                "sources": [
                    Source(
                        title=item.title,
                        url=item.url,
                        published_at=item.published_at,
                    ).model_dump(mode="json")
                    for item in items
                ],
                "error": None,
            }
        except NoNewsResultsError as exc:
            return {"error": _error(exc.code, str(exc), exc.retryable)}
        except NewsSearchError as exc:
            return {"error": _error(exc.code, str(exc), exc.retryable)}
        except Exception:
            return {
                "error": _error(
                    "search_unavailable",
                    "뉴스 검색 결과를 처리하지 못했습니다.",
                    True,
                )
            }
        
    # 검색 결과를 모델에게 전달하여 구조화된 경제 분석을 생성
    async def analyze_economy(state: AgentState) -> dict[str, Any]:
        try:
            results = [
                NewsItem.model_validate(item) for item in state.get("search_results", [])
            ]
            # 근거 자료가 없다면 LLM을 호출하지 않고 분석을 중단.
            if not results:
                return {
                    "error": _error(
                        "no_sources",
                        "분석에 사용할 뉴스 출처가 없습니다.",
                        False,
                    )
                }
            plan = QueryPlan.model_validate(state.get("plan"))
            # 모델에는 원래 질문과 대화 내역, 뉴스 출처를 전달한다
            analysis = await model.analyze(
                query=state["query"],
                messages=state.get("messages", []),
                sources=results,
                focus=plan.analysis_focus,
            )
            return {"analysis": analysis.model_dump(), "error": None}
        except Exception:
            return {
                "error": _error(
                    "analysis_failed",
                    "뉴스를 바탕으로 경제 분석을 생성하지 못했습니다.",
                    True,
                )
            }
        
    # Pydantic 분석 데이터를 사용자에게 보여 줄 Slack 메시지로 변환
    async def format_answer(state: AgentState) -> dict[str, Any]:
        try:
            analysis = EconomicAnalysis.model_validate(state.get("analysis"))
            sources = [Source.model_validate(item) for item in state.get("sources", [])]
            answer = format_analysis(analysis, sources)
            return {
                "final_answer": answer,
                "messages": [AIMessage(content=answer)],
            }
        except Exception:
            return {
                "error": _error(
                    "invalid_state",
                    "분석 결과를 응답 형식으로 변환하지 못했습니다.",
                    False,
                ),
                "final_answer": "분석 결과를 표시할 수 없습니다.",
            }

    async def handle_error(state: AgentState) -> dict[str, Any]:
        error = AgentErrorState.model_validate(state.get("error"))
        return {
            "final_answer": (
                "⚠️ 신뢰할 수 있는 뉴스 근거를 확보하지 못해 분석을 중단했습니다.\n"
                f"사유: {error.message}\n"
                f"오류 코드: `{error.code}`"
            )
        }

    return {
        "plan_query": plan_query,
        "search_news": search_news_node,
        "analyze_economy": analyze_economy,
        "format_answer": format_answer,
        "handle_error": handle_error,
    }