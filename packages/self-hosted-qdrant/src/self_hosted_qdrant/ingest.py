from itertools import batched

from tqdm import tqdm

from self_hosted_qdrant.config import get_settings
from self_hosted_qdrant.dataset import iter_articles
from self_hosted_qdrant.store import (
    create_collection,
    create_sync_client,
    upsert_articles,
)

BATCH_SIZE = 256


def main() -> None:
    settings = get_settings()
    client = create_sync_client(settings.qdrant_url)
    # Point IDs are stable, so running this script again is safe.
    if not client.collection_exists(settings.collection):
        create_collection(client, settings.collection)

    articles = iter_articles(settings.num_docs)
    with tqdm(total=settings.num_docs, unit="doc") as progress:
        for batch in batched(articles, BATCH_SIZE):
            upsert_articles(client, settings.collection, batch)
            progress.update(len(batch))


if __name__ == "__main__":
    main()
