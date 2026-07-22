from __future__ import annotations

from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# LangGraph의 모든 노드가 함께 읽고 갱신하는 상태 저장소
class AgentState(TypedDict, total=False):
    # 사용자가 현재 요청한 질문과 실행을 식별하는 값
    query: str
    run_id: str

    # add_messages(기존 메시지와 새 메시지를 병합하는) 리듀서가 각 노드에서 반환한 메시지를 기존 목록에 누적함.
    # reducer : 노드가 반환한 새 값과 기존 상태 값을 어떻게 합칠지 결정하는 함수
    # 없다면 일반적으로 새 값이 기존 값을 덮어씀. 
    # human 메시지 -> AI 메시지 => 최종 상태에 AI 메시지만 남고 기존 메시지가 사라짐
    messages: Annotated[list[AnyMessage], add_messages]

    # 계획 -> 검색 -> 분석 단계에서 차례로 생성되는 중간 결과
    plan: dict[str, Any]
    search_results: list[dict[str, Any]]
    analysis: dict[str, Any]
    sources: list[dict[str, Any]]

    # 워크플로우가 사용자에게 전달할 최종 결과 또는 오류 정보
    final_answer: str
    error: dict[str, Any] | Nonefrom __future__ import annotations

from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# LangGraph의 모든 노드가 함께 읽고 갱신하는 상태 저장소
class AgentState(TypedDict, total=False):
    # 사용자가 현재 요청한 질문과 실행을 식별하는 값
    query: str
    run_id: str

    # add_messages 리듀서가 각 노드에 반환한 메시지를 기존 목록에 누적함.
    # reducer : 노드가 반환한 새 값과 기존 상태 값을 어떻게 합칠지 결정하는 함수.
    # 없다면 일반적으로 새 값이 기존 값을 덮어씀.
    # human 메시지 -> AI 메시지 -> 최종 상태에 AI 메시지만 남고 기존 메시지가 사라짐.
    messages: Annotated[list[AnyMessage], add_messages]
    
    # 계획 -> 검색 -> 분석 단계에서 차례로 생성되는 중간 결과
    plan: dict[str, Any]
    search_results: list[dict[str, Any]]
    analysis: dict[str, Any]
    sources: list[dict[str, Any]]
    
    # 워크플로우가 사용자에게 전달할 최종 결과 또는 오류 정보
    final_answer: str
    error: dict[str, Any] | None

