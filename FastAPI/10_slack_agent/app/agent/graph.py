from __future__ import annotations

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

    builder.add_edge(START, "plan_query")
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

