from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from qdrant_client import AsyncQdrantClient

from qdrant_cloud import store
from qdrant_cloud.config import Settings, get_settings
from qdrant_cloud.schemas import Info, SearchRequest, SearchResponse

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    app.state.qdrant = store.create_client(settings.qdrant_url, settings.qdrant_api_key)
    yield
    await app.state.qdrant.close()


def get_qdrant(request: Request) -> AsyncQdrantClient:
    return request.app.state.qdrant


app = FastAPI(title="PubMed search with Qdrant Cloud", lifespan=lifespan)

Qdrant = Annotated[AsyncQdrantClient, Depends(get_qdrant)]
Config = Annotated[Settings, Depends(get_settings)]


@app.get("/api/info")
async def info(qdrant: Qdrant, settings: Config) -> Info:
    return Info(documents=await store.count_articles(qdrant, settings.collection))


@app.post("/api/search")
async def search(
    request: SearchRequest, qdrant: Qdrant, settings: Config
) -> SearchResponse:
    start = perf_counter()
    hits = await store.search(
        qdrant,
        settings.collection,
        request.mode,
        request.query,
        request.filters,
        request.limit,
        settings.openrouter_api_key,
    )
    return SearchResponse(hits=hits, search_ms=(perf_counter() - start) * 1000)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
