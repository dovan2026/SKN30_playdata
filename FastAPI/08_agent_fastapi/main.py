"""LangGraph 기반 콘텐츠 생성 워크플로를 제공하는 FastAPI 애플리케이션."""

import asyncio
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph import ContentInput, content_graph


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = 


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



@app.post("/langgraph", response_model=)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000)
