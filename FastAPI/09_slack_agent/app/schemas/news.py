from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    content: str = ""
    published_at: datetime | None = None
    score: float | None = None


class Source(BaseModel):
    title: str
    url: str
    published_at: datetime | None = None

