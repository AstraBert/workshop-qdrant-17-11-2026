import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from qdrant_edge import EdgeShard

from prototype_with_edge import embeddings, store
from prototype_with_edge.config import get_settings
from prototype_with_edge.schemas import Info, SearchRequest, SearchResponse, Timings

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    app.state.shard = store.load_shard(settings.shard_path)
    async with embeddings.create_client(settings.openrouter_api_key) as client:
        app.state.http = client
        yield
    app.state.shard.close()


def get_shard(request: Request) -> EdgeShard:
    return request.app.state.shard


def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


app = FastAPI(title="PubMed search with Qdrant Edge", lifespan=lifespan)


@app.get("/api/info")
async def info(shard: Annotated[EdgeShard, Depends(get_shard)]) -> Info:
    return Info(documents=await asyncio.to_thread(store.count_articles, shard))


@app.post("/api/search")
async def search(
    request: SearchRequest,
    shard: Annotated[EdgeShard, Depends(get_shard)],
    http: Annotated[httpx.AsyncClient, Depends(get_http)],
) -> SearchResponse:
    start = perf_counter()
    vector = await embeddings.embed(http, request.query)
    embedded = perf_counter()
    hits = await asyncio.to_thread(store.search, shard, vector, request.limit)
    done = perf_counter()
    return SearchResponse(
        hits=hits,
        timings=Timings(
            embedding_ms=(embedded - start) * 1000, search_ms=(done - embedded) * 1000
        ),
    )


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
