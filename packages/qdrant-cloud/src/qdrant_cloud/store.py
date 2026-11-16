from collections.abc import Iterable

from qdrant_client import AsyncQdrantClient, QdrantClient, models
from qdrant_client.http.models import QueryResponse

from qdrant_cloud.dataset import Article
from qdrant_cloud.schemas import Filters, Hit, Mode

DENSE = "dense"
TITLE = "title"
CONTENT = "content"
PMID = "pmid"
VECTOR_SIZE = 1024  # Output size of BGE-M3
EMBEDDING_MODEL = "openrouter/baai/bge-m3"
PREFETCH_LIMIT = 50  # Candidates that each retriever sends to the fusion step


def create_client(url: str, api_key: str) -> AsyncQdrantClient:
    return AsyncQdrantClient(url=url, api_key=api_key, cloud_inference=True)


def create_sync_client(url: str, api_key: str) -> QdrantClient:
    return QdrantClient(url=url, api_key=api_key, timeout=120)


def create_collection(client: QdrantClient, collection: str) -> None:
    client.create_collection(
        collection,
        vectors_config={
            DENSE: models.VectorParams(
                size=VECTOR_SIZE, distance=models.Distance.COSINE, datatype=models.Datatype.TURBO8
            )
        },
    )
    # Create the indexes before the upload, so Qdrant builds them while it ingests.
    for field in (TITLE, CONTENT):
        client.create_payload_index(
            collection,
            field,
            models.TextIndexParams(
                type=models.TextIndexType.TEXT,
                tokenizer=models.TokenizerType.WORD,
                lowercase=True,
                stemmer=models.SnowballParams(
                    type=models.Snowball.SNOWBALL,
                    language=models.SnowballLanguage.ENGLISH,
                ),
                stopwords=models.Language.ENGLISH,
                scoring=True,  # Turns the full-text index into a BM25 index
            ),
        )
    client.create_payload_index(collection, PMID, models.PayloadSchemaType.INTEGER)


def upload_articles(
    client: QdrantClient, collection: str, articles: Iterable[Article]
) -> None:
    points = (
        models.PointStruct(
            id=article["id"],
            vector={DENSE: article["embedding"]},
            payload={
                PMID: article["pmid"],
                TITLE: article["title"],
                CONTENT: article["content"],
            },
        )
        for article in articles
    )
    client.upload_points(collection, points, batch_size=256, parallel=4, wait=True)


def build_filter(filters: Filters) -> models.Filter | None:
    must: list[models.Condition] = []
    must_not: list[models.Condition] = []
    if filters.title_contains:
        must.append(
            models.FieldCondition(
                key=TITLE, match=models.MatchText(text=filters.title_contains)
            )
        )
    if filters.abstract_excludes:
        must_not.append(
            models.FieldCondition(
                key=CONTENT,
                match=models.MatchTextAny(text_any=filters.abstract_excludes),
            )
        )
    if filters.pmid_min is not None or filters.pmid_max is not None:
        must.append(
            models.FieldCondition(
                key=PMID, range=models.Range(gte=filters.pmid_min, lte=filters.pmid_max)
            )
        )
    if not must and not must_not:
        return None
    return models.Filter(must=must, must_not=must_not)


def dense_query(text: str, openrouter_api_key: str) -> models.Document:
    """Qdrant Cloud calls OpenRouter to embed this text. Our code never sees the vector."""
    return models.Document(
        text=text,
        model=EMBEDDING_MODEL,
        options={"openrouter-api-key": openrouter_api_key},
    )


def _lexical_prefetches(text: str, flt: models.Filter | None) -> list[models.Prefetch]:
    # A text query ranks points with BM25 over the full-text index of a field.
    return [
        models.Prefetch(
            query=models.TextQuery(text=text),
            using=field,
            filter=flt,
            limit=PREFETCH_LIMIT,
        )
        for field in (TITLE, CONTENT)
    ]


def _to_hits(response: QueryResponse) -> list[Hit]:
    return [Hit(score=point.score, **point.payload) for point in response.points]


async def count_articles(client: AsyncQdrantClient, collection: str) -> int:
    return (await client.get_collection(collection)).points_count or 0


async def search(
    client: AsyncQdrantClient,
    collection: str,
    mode: Mode,
    text: str,
    filters: Filters,
    limit: int,
    openrouter_api_key: str,
) -> list[Hit]:
    flt = build_filter(filters)
    if mode == "dense":
        response = await client.query_points(
            collection,
            query=dense_query(text, openrouter_api_key),
            using=DENSE,
            query_filter=flt,
            limit=limit,
            with_payload=True,
        )
    elif mode == "keyword":
        response = await client.query_points(
            collection,
            prefetch=_lexical_prefetches(text, flt),
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True,
        )
    else:
        dense = models.Prefetch(
            query=dense_query(text, openrouter_api_key),
            using=DENSE,
            filter=flt,
            limit=PREFETCH_LIMIT,
        )
        response = await client.query_points(
            collection,
            prefetch=[dense, *_lexical_prefetches(text, flt)],
            # The dense ranking counts as much as the title and abstract rankings together.
            query=models.RrfQuery(rrf=models.Rrf(weights=[2.0, 1.0, 1.0])),
            limit=limit,
            with_payload=True,
        )
    return _to_hits(response)
