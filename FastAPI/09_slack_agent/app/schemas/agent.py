from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.news import Source


class AgentRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    thread_id: str | None = Field(default=None, max_length=255)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be blank")
        return stripped


class AgentResponse(BaseModel):
    run_id: UUID
    thread_id: str
    answer: str
    sources: list[Source]


class ErrorDetail(BaseModel):
    run_id: UUID | None = None
    code: str
    message: str
    retryable: bool


class ErrorResponse(BaseModel):
    detail: ErrorDetail


class QueryPlan(BaseModel):
    needs_search: bool
    search_query: str = Field(min_length=1, max_length=300)
    analysis_focus: str = Field(min_length=1, max_length=500)


class EconomicAnalysis(BaseModel):
    title: str
    core_news: list[str] = Field(min_length=1, max_length=5)
    fact_summary: list[str] = Field(min_length=1, max_length=5)
    macro_impacts: list[str] = Field(min_length=1, max_length=5)
    industry_impacts: list[str] = Field(min_length=1, max_length=5)
    upside_factors: list[str] = Field(min_length=1, max_length=5)
    downside_risks: list[str] = Field(min_length=1, max_length=5)
    caveats: list[str] = Field(default_factory=list, max_length=3)


class AgentErrorState(BaseModel):
    code: Literal[
        "search_unavailable",
        "no_sources",
        "planning_failed",
        "analysis_failed",
        "invalid_state",
    ]
    message: str
    retryable: bool = False
