# todo_toolkits/tools.py

from typing import List, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

todo_list: List[str] = []

class AddTodoInput(BaseModel):
    item: str = Field(description="추가할 할 일 항목")

class AddTodoTool(BaseTool):
    name: str = "add_todo"
    description: str = "할 일 목록에 새 항목을 추가합니다."
    args_schema: Type[BaseModel] = AddTodoInput

    def _run(self, item: str) -> str:
        todo_list.append(item)
        return f"'{item}'이(가) 할 일 목록에 추가되었습니다."

    async def _arun(self, item: str) -> str:
        return self._run(item)

class ViewTodosTool(BaseTool):
    name: str = "view_todos"
    description: str = "현재 할 일 목록 전체를 보여줍니다."

    def _run(self) -> str:
        if not todo_list:
            return "할 일 목록이 비어있습니다."
        items_str = "\n".join(f"- {item}" for item in todo_list)
        return f"현재 할 일 목록:\n{items_str}"

    async def _arun(self) -> str:
        return self._run()

class CompleteTodoInput(BaseModel):
    item_number: int = Field(description="완료할 할 일 항목의 번호")

class CompleteTodoTool(BaseTool):
    name: str = "complete_todo"
    description: str = "지정된 번호의 할 일을 완료 처리합니다."
    args_schema: Type[BaseModel] = CompleteTodoInput

    def _run(self, item_number: int) -> str:
        try:
            if 0 < item_number <= len(todo_list):
                removed_item = todo_list.pop(item_number - 1)
                return f"'{removed_item}' 항목이 완료되었습니다."
            else:
                return "잘못된 항목 번호입니다."
        except IndexError:
            return "잘못된 항목 번호입니다."
        except Exception as e:
            return f"오류 발생: {e}"
        
# # <<< 새로운 삭제 도구 추가 >>>

class DeleteTodoInput(BaseModel):
    """삭제할 할 일 항목의 입력을 정의합니다."""
    item_number: int = Field(description="삭제할 할 일 항목의 번호 (목록에서 보이는 순서대로 1부터 시작)")

class DeleteTodoTool(BaseTool):
    """지정된 할 일 항목을 목록에서 삭제하는 도구입니다."""
    name: str = "delete_todo"
    description: str = "지정된 번호의 할 일을 목록에서 삭제합니다."
    args_schema: Type[BaseModel] = DeleteTodoInput

    def _run(self, item_number: int) -> str:
        try:
            if not todo_list:
                return "삭제할 할 일 목록이 이미 비어있습니다."
            if 0 < item_number <= len(todo_list):
                removed_item = todo_list.pop(item_number - 1)  # 1-based index to 0-based
                return f"'{removed_item}' 항목이 성공적으로 삭제되었습니다."
            else:
                return f"잘못된 항목 번호입니다: {item_number}. 'view_todos'로 현재 목록을 확인하세요."
        except IndexError: # pop 중에 item_number가 범위를 벗어난 경우 (이론상 위의 조건문에서 걸러짐)
            return "잘못된 항목 번호입니다. 목록 범위를 벗어났습니다."
        except Exception as e:
            return f"삭제 중 오류 발생: {e}"

    async def _arun(self, item_number: int) -> str:
        # 비동기 구현이 필요하면 여기에 작성, 간단한 경우 _run 호출
        return self._run(item_number)

# # <<< 삭제 도구 추가 완료 >>>    


        