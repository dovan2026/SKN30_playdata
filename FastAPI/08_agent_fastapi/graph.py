"""콘텐츠 생성 과정을 순차 실행하는 LangGraph 그래프."""

from collections.abc import Callable
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from agents import(
    PLANNER_SYSTEM_PROMPT,
    WRITER_SYSTEM_PROMPT,
    EDITOR_SYSTEM_PROMPT,
    TRANSLATOR_SYSTEM_PROMPT,
    run_agent
)

from tasks import (
    build_plan_task,
    build_edit_task,
    build_write_task,
    build_translate_task
)

class ContentInput(TypedDict):
    topic: str

class ContentState(TypedDict):
    """노드 사이에서 공유하는 콘텐츠 생성 상태."""

    topic: str
    plan: str
    draft: str
    edited_content: str
    final_content: str

AgentRunner = Callable[[str, str], str]


def create_graph(agent_runner: AgentRunner = run_agent):
    """기획→작성→편집→번역 순서의 컴파일된 그래프를 생성합니다."""

    def planner_node(state: ContentState) -> dict[str, str]:
        """topic을 읽어 상세 기획안을 만들고 plan 필드만 갱신."""
    
        return {
            "plan": agent_runner(
                PLANNER_SYSTEM_PROMPT,
                build_plan_task(state["topic"])
            )
        }

    def writer_node(state: ContentState) -> dict[str, str]:
        """topic과 plan을 읽어 초안을 만들고 draft 필드를 추가"""

        # 이 노드는 planner 뒤에만 실행되므로 state["plan"]이 존재함.
        return {
            "draft": agent_runner(
                WRITER_SYSTEM_PROMPT,
                build_write_task(state['topic'], state['plan'])
            )
        }
    
    def editor_node(state: ContentState) -> dict[str, str]:
        """작성된 draft를 교정하고 edited_content를 생성함"""
        return {
            "edited_content": agent_runner(
                EDITOR_SYSTEM_PROMPT,
                build_edit_task(state['topic'], state['draft'])
            )
        }
    
    def translator_node(state: ContentState) -> dict[str, str]:
        """편집 결과를 최종 한국어 콘텐츠로 변환함."""
        return {
            "final_content": agent_runner(
                TRANSLATOR_SYSTEM_PROMPT,
                build_translate_task(state['topic'], state['edited_content'])
            )
        }
    
    # 아직 이 시점에는 그래프의 구조만 정의하며 실제 LLM 호출은 complie 이후 invoke()할 때 발생. 
    builder = StateGraph(
        ContentState,
        input_schema=ContentInput
        )
    
    builder.add_node("planner", planner_node)
    builder.add_node("writer", writer_node)
    builder.add_node("editor", editor_node)
    builder.add_node("translator", translator_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "writer")
    builder.add_edge("writer", "editor")
    builder.add_edge("editor", "translator")
    builder.add_edge("translator", END) 

    # compile()은 노드/엣지 정의를 검증하고 invoke 가능한 실행 객체를 반환함.
    return builder.compile()

# 그래프 구조는 요청마다 달라지지 않으므로 모듈 import 시 한 번만 컴파일함.
# 실제 모델 호출은 여기서 일어나지 않고 main.py가 content_graph.invoke()를 호출할 때 시작함. 
content_graph = create_graph()
