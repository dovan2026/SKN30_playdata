from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.model import AgentModel
from app.agent.nodes import create_nodes
from app.agent.state import AgentState
from app.tools.news_search import NewsSearchProvider

# 계획 노드 이후 검색, 기존 출처 분석, 오류 처리 중 다른 경로 선택
def _after_plan(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    return "search_news" if state.get("plan", {}).get("needs_search", True) else "analyze_economy"

# 검색 또는 분석 노드 이후 오류가 있으면 오류 처리 경로로 전환
def _after_work(state: AgentState) -> str:
    return "handle_error" if state.get("error") else "continue"


def create_graph(
    *,
    model: AgentModel,
    news_provider: NewsSearchProvider,
    news_limit: int = 5,
    news_days: int = 7,
    checkpointer: Any | None = None,
):
    # 모델과 검색 제공자를 주입하여 실제 노드 함수들을 생성
    nodes = create_nodes(
        model=model,
        news_provider=news_provider,
        news_limit=news_limit,
        news_days=news_days,
    )

    builder = StateGraph(AgentState)
    for name, node in nodes.items():
        builder.add_node(name, node)

    # 워크플로우는 항상 검색 계획 단계에서 시작함.
    builder.add_edge(START, "plan_query")
    # 계획 결과에 따라 새 뉴스 검색, 기존 결과 분석 또는 오류 처리로 분기함.
    builder.add_conditional_edges(
        "plan_query",
        _after_plan,
        {
            "search_news": "search_news",
            "analyze_economy": "analyze_economy",
            "handle_error": "handle_error",
        },
    )

    # 검색에 성공하면 분석하고, 실패하면 오류 응답을 만든다.
    builder.add_conditional_edges(
        "search_news",
        _after_work,
        {"continue": "analyze_economy", "handle_error": "handle_error"},
    )

    # 분석에 성공하면 답변을 포맷하고, 실패하면 오류 응답을 만든다.
    builder.add_conditional_edges(
        "analyze_economy",
        _after_work,
        {"continue": "format_answer", "handle_error": "handle_error"},
    )
    # 정상 답변과 오류 답변은 모두 워크플로우 종료.
    builder.add_edge("format_answer", END)
    builder.add_edge("handle_error", END)

    # checkpointer가 있으면 대화 스레드별 상태를 저장할 수 있도록 함께 컴파일.
    return builder.compile(checkpointer=checkpointer)from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.model import AgentModel
from app.agent.nodes import create_nodes
from app.agent.state import AgentState
from app.tools.news_search import NewsSearchProvider


def _after_plan(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    return "search_news" if state.get("plan", {}).get("needs_search", True) else "analyze_economy"


def _after_work(state: AgentState) -> str:
    return "handle_error" if state.get("error") else "continue"


def create_graph(
    *,
    model: AgentModel,
    news_provider: NewsSearchProvider,
    news_limit: int = 5,
    news_days: int = 7,
    checkpointer: Any | None = None,
):
    nodes = create_nodes(
        model=model,
        news_provider=news_provider,
        news_limit=news_limit,
        news_days=news_days,
    )
    builder = StateGraph(AgentState)
    for name, node in nodes.items():
        builder.add_node(name, node)

    # 워크플로우는 항상 검색 계획 단계에서 시작함.
    builder.add_edge(START, "plan_query")
    # 계획 결과에 따라 
    builder.add_conditional_edges(
        "plan_query",
        _after_plan,
        {
            "search_news": "search_news",
            "analyze_economy": "analyze_economy",
            "handle_error": "handle_error",
        },
    )
    builder.add_conditional_edges(
        "search_news",
        _after_work,
        {"continue": "analyze_economy", "handle_error": "handle_error"},
    )
    builder.add_conditional_edges(
        "analyze_economy",
        _after_work,
        {"continue": "format_answer", "handle_error": "handle_error"},
    )
    builder.add_edge("format_answer", END)
    builder.add_edge("handle_error", END)
    return builder.compile(checkpointer=checkpointer)

