from collections.abc import Iterable

from qdrant_client import AsyncQdrantClient, QdrantClient, models
from qdrant_client.http.models import QueryResponse

from self_hosted_qdrant.dataset import Article
from self_hosted_qdrant.schemas import Hit

DENSE = "dense"
BM25 = "bm25"
BM25_MODEL = "qdrant/bm25"
VECTOR_SIZE = 1024  # Output size of BGE-M3
PREFETCH_LIMIT = 50  # Candidates that each retriever sends to the fusion step


def create_client(url: str) -> AsyncQdrantClient:
    # Qdrant computes the BM25 vectors. This flag sends text to the server as is.
    return AsyncQdrantClient(url=url, cloud_inference=True)


def create_sync_client(url: str) -> QdrantClient:
    return QdrantClient(url=url, cloud_inference=True, timeout=120)


def create_collection(client: QdrantClient, collection: str) -> None:
    client.create_collection(
        collection,
        vectors_config={
            DENSE: models.VectorParams(
                size=VECTOR_SIZE, distance=models.Distance.COSINE
            )
        },
        # The IDF modifier makes Qdrant weight rare words higher at query time.
        sparse_vectors_config={
            BM25: models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )


def upsert_articles(
    client: QdrantClient, collection: str, articles: Iterable[Article]
) -> None:
    points = [
        models.PointStruct(
            id=article["id"],
            vector={
                DENSE: article["embedding"],
                BM25: models.Document(
                    text=f"{article['title']}\n{article['content']}", model=BM25_MODEL
                ),
            },
            payload={
                "pmid": article["pmid"],
                "title": article["title"],
                "content": article["content"],
            },
        )
        for article in articles
    ]
    client.upsert(collection, points, wait=True)


def _to_hits(response: QueryResponse) -> list[Hit]:
    return [Hit(score=point.score, **point.payload) for point in response.points]


async def count_articles(client: AsyncQdrantClient, collection: str) -> int:
    return (await client.count(collection)).count


async def search_dense(
    client: AsyncQdrantClient, collection: str, vector: list[float], limit: int
) -> list[Hit]:
    response = await client.query_points(
        collection, query=vector, using=DENSE, limit=limit, with_payload=True
    )
    return _to_hits(response)


async def search_keyword(
    client: AsyncQdrantClient, collection: str, text: str, limit: int
) -> list[Hit]:
    response = await client.query_points(
        collection,
        query=models.Document(text=text, model=BM25_MODEL),
        using=BM25,
        limit=limit,
        with_payload=True,
    )
    return _to_hits(response)


async def search_hybrid(
    client: AsyncQdrantClient,
    collection: str,
    text: str,
    vector: list[float],
    limit: int,
) -> list[Hit]:
    response = await client.query_points(
        collection,
        prefetch=[
            models.Prefetch(query=vector, using=DENSE, limit=PREFETCH_LIMIT),
            models.Prefetch(
                query=models.Document(text=text, model=BM25_MODEL),
                using=BM25,
                limit=PREFETCH_LIMIT,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=limit,
        with_payload=True,
    )
    return _to_hits(response)
