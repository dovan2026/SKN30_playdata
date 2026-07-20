"""콘텐츠 생성 과정을 순차 실행하는 LangGraph 그래프."""

from collections.abc import Callable
from typing import NotRequired, TypedDict


class ContentInput(TypedDict):
    topic: str

class ContentState(TypedDict):
    """노드 사이에서 공유하는 콘텐츠 생성 상태."""



AgentRunner = Callable[[str, str], str]


def create_graph(agent_runner: AgentRunner = ):
    """기획→작성→편집→번역 순서의 컴파일된 그래프를 생성합니다."""

    def planner_node(state: ContentState) -> dict[str, str]:

        return 
    

    def writer_node(state: ContentState) -> dict[str, str]:

        return
    

    def editor_node(state: ContentState) -> dict[str, str]:

        return 
    

    def translator_node(state: ContentState) -> dict[str, str]:

        return 
    

    builder = 


 

    return 

content_graph = 
