"""LangGraph 기반 콘텐츠 생성 워크플로를 제공하는 FastAPI 애플리케이션."""

import asyncio
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph import ContentInput, content_graph


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="blog maker Agent",
    version='1.0.0',
    description="topic을 기반으로 LangGraph 에이전트를 사용해 콘텐츠를 생성하는 API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TopicInput(BaseModel):
    topic: str

class ContentOutput(BaseModel):
    """그래프가 생성한 중간 산출물과 최종 결과물의 응답 스키마"""

    # 중간 결과까지 응답에 포함하므로 Swagger에서 각 노드의 결과를 확인할 수 있고,
    # 브라우저 UI는 이 중 final_content만 화면에 표시
    topic : str
    plan : str
    draft : str
    edited_content : str
    final_content : str


@app.post("/langgraph", response_model=ContentOutput)
async def langgraph_endpoint(input_data: TopicInput) -> ContentOutput:
    try:
        result = await asyncio.to_thread(
            content_graph.invoke,
            {"topic": input_data.topic},
        )
        return ContentOutput(**result)
    except Exception as error:
        logger.exception("LangGraph 엔드포인트 실행 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail=str(error)) from error

@app.get("/")
async def root():
    return {
        "message": "LangGraph Blog Maker API",
        "docs": "/docs"
    }

# python main.py 로 직접 실행했을 때 동작
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000)
