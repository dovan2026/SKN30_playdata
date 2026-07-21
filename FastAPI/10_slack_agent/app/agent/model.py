from __future__ import annotations

from typing import Protocol, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agent.prompts import ANALYSIS_SYSTEM_PROMPT, PLANNER_SYSTEM_PROMPT
from app.schemas.agent import EconomicAnalysis, QueryPlan
from app.schemas.news import NewsItem


class AgentModel(Protocol):
    async def plan(
        self,
        query: str,
        messages: Sequence[BaseMessage],
        has_sources: bool,
    ) -> QueryPlan: ...

    async def analyze(
        self,
        query: str,
        messages: Sequence[BaseMessage],
        sources: list[NewsItem],
        focus: str,
    ) -> EconomicAnalysis: ...


class OpenAIAgentModel:
    def __init__(self, api_key: str, model: str = "gpt-5.6-terra") -> None:
        llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            use_responses_api=True,
            max_retries=2,
            timeout=60,
        )
        self._planner = llm.with_structured_output(QueryPlan, method="json_schema")
        self._analyzer = llm.with_structured_output(
            EconomicAnalysis,
            method="json_schema",
        )

    async def plan(
        self,
        query: str,
        messages: Sequence[BaseMessage],
        has_sources: bool,
    ) -> QueryPlan:
        history = "\n".join(
            f"{message.type}: {message.content}" for message in messages[-6:]
        )
        result = await self._planner.ainvoke(
            [
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"기존 출처 존재: {has_sources}\n"
                        f"최근 대화:\n{history}\n\n현재 질문: {query}"
                    )
                ),
            ]
        )
        return QueryPlan.model_validate(result)

    async def analyze(
        self,
        query: str,
        messages: Sequence[BaseMessage],
        sources: list[NewsItem],
        focus: str,
    ) -> EconomicAnalysis:
        source_text = "\n\n".join(
            f"[{index}] 제목: {item.title}\nURL: {item.url}\n내용: {item.content}"
            for index, item in enumerate(sources, start=1)
        )
        history = "\n".join(
            f"{message.type}: {message.content}" for message in messages[-6:]
        )
        result = await self._analyzer.ainvoke(
            [
                SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"최근 대화:\n{history}\n\n"
                        f"사용자 질문: {query}\n분석 초점: {focus}\n\n"
                        f"뉴스 출처:\n{source_text}"
                    )
                ),
            ]
        )
        return EconomicAnalysis.model_validate(result)
