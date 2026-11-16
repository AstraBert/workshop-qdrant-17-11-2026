from collections.abc import Iterable
from pathlib import Path

from qdrant_edge import (
    CountRequest,
    Distance,
    EdgeConfig,
    EdgeShard,
    EdgeVectorParams,
    Point,
    Query,
    QueryRequest,
    UpdateOperation,
)

from prototype_with_edge.dataset import Article
from prototype_with_edge.schemas import Hit

VECTOR_NAME = "dense"
VECTOR_SIZE = 1024  # Output size of BGE-M3


def create_shard(path: Path) -> EdgeShard:
    path.mkdir(parents=True, exist_ok=True)
    config = EdgeConfig(
        vectors={
            VECTOR_NAME: EdgeVectorParams(size=VECTOR_SIZE, distance=Distance.Cosine)
        }
    )
    return EdgeShard.create(str(path), config)


def load_shard(path: Path) -> EdgeShard:
    return EdgeShard.load(str(path))


def upsert_articles(shard: EdgeShard, articles: Iterable[Article]) -> None:
    points = [
        Point(
            id=article["id"],
            vector={VECTOR_NAME: article["embedding"]},
            payload={
                "pmid": article["pmid"],
                "title": article["title"],
                "content": article["content"],
            },
        )
        for article in articles
    ]
    shard.update(UpdateOperation.upsert_points(points))


def count_articles(shard: EdgeShard) -> int:
    return shard.count(CountRequest(exact=True))


def search(shard: EdgeShard, vector: list[float], limit: int) -> list[Hit]:
    points = shard.query(
        QueryRequest(
            query=Query.Nearest(vector, using=VECTOR_NAME),
            limit=limit,
            with_vector=False,
            with_payload=True,
        )
    )
    return [Hit(score=point.score, **point.payload) for point in points]
