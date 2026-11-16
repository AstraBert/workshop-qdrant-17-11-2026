from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from qdrant_client import AsyncQdrantClient

from self_hosted_qdrant import embeddings, store
from self_hosted_qdrant.config import Settings, get_settings
from self_hosted_qdrant.schemas import Info, SearchRequest, SearchResponse, Timings

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    app.state.qdrant = store.create_client(settings.qdrant_url)
    async with embeddings.create_client(settings.openrouter_api_key) as client:
        app.state.http = client
        yield
    await app.state.qdrant.close()


def get_qdrant(request: Request) -> AsyncQdrantClient:
    return request.app.state.qdrant


def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


app = FastAPI(title="PubMed search with self-hosted Qdrant", lifespan=lifespan)

Qdrant = Annotated[AsyncQdrantClient, Depends(get_qdrant)]
Http = Annotated[httpx.AsyncClient, Depends(get_http)]
Config = Annotated[Settings, Depends(get_settings)]


@app.get("/api/info")
async def info(qdrant: Qdrant, settings: Config) -> Info:
    return Info(documents=await store.count_articles(qdrant, settings.collection))


@app.post("/api/search")
async def search(
    request: SearchRequest, qdrant: Qdrant, http: Http, settings: Config
) -> SearchResponse:
    collection = settings.collection
    start = perf_counter()
    embedding_ms = None

    if request.mode == "keyword":
        # Keyword search needs no embedding, so we skip the OpenRouter call.
        hits = await store.search_keyword(
            qdrant, collection, request.query, request.limit
        )
    else:
        vector = await embeddings.embed(http, request.query)
        embedding_ms = (perf_counter() - start) * 1000
        if request.mode == "dense":
            hits = await store.search_dense(qdrant, collection, vector, request.limit)
        else:
            hits = await store.search_hybrid(
                qdrant, collection, request.query, vector, request.limit
            )

    total_ms = (perf_counter() - start) * 1000
    return SearchResponse(
        hits=hits,
        timings=Timings(
            embedding_ms=embedding_ms, search_ms=total_ms - (embedding_ms or 0)
        ),
    )


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
