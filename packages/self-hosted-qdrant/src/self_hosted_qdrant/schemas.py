from typing import Literal

from pydantic import BaseModel, Field

Mode = Literal["dense", "keyword", "hybrid"]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: Mode = "hybrid"
    limit: int = Field(default=10, ge=1, le=50)


class Hit(BaseModel):
    score: float
    pmid: int
    title: str
    content: str


class Timings(BaseModel):
    embedding_ms: float | None
    search_ms: float


class SearchResponse(BaseModel):
    hits: list[Hit]
    timings: Timings


class Info(BaseModel):
    documents: int
