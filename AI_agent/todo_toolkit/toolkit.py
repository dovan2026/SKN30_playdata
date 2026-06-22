# todo_toolkits/toolkit.py

from typing import List
from langchain_core.tools import BaseTool
from .tools import AddTodoTool, ViewTodosTool, CompleteTodoTool

class TodoToolkit:
    """할 일 관리를 위한 툴킷입니다."""

    def get_tools(self) -> List[BaseTool]:
        """툴킷에 포함된 도구들의 리스트를 반환합니다."""
        return [AddTodoTool(), ViewTodosTool(), CompleteTodoTool()]
