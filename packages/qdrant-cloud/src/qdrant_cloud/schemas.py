from typing import Literal

from pydantic import BaseModel, Field

Mode = Literal["dense", "keyword", "hybrid"]


class Filters(BaseModel):
    title_contains: str = ""
    abstract_excludes: str = ""
    pmid_min: int | None = None
    pmid_max: int | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: Mode = "hybrid"
    limit: int = Field(default=10, ge=1, le=50)
    filters: Filters = Field(default_factory=Filters)


class Hit(BaseModel):
    score: float
    pmid: int
    title: str
    content: str


class SearchResponse(BaseModel):
    hits: list[Hit]
    # Cloud Inference embeds the query inside the search call, so there is one timing.
    search_ms: float


class Info(BaseModel):
    documents: int
