from __future__ import annotations

from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# LangGraph의 모든 노드가 함께 읽고 갱신하는 상태 저장소
class AgentState(TypedDict, total=False):
    query: str
    run_id: str
    messages: Annotated[list[AnyMessage], add_messages]
    plan: dict[str, Any]
    search_results: list[dict[str, Any]]
    analysis: dict[str, Any]
    sources: list[dict[str, Any]]
    final_answer: str
    error: dict[str, Any] | None

