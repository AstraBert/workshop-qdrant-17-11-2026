from itertools import batched

from tqdm import tqdm

from qdrant_cloud.config import get_settings
from qdrant_cloud.dataset import iter_articles
from qdrant_cloud.store import create_collection, create_sync_client, upload_articles

CHUNK_SIZE = 5_000


def main() -> None:
    settings = get_settings()
    client = create_sync_client(settings.qdrant_url, settings.qdrant_api_key)
    # Point IDs are stable, so running this script again is safe.
    if not client.collection_exists(settings.collection):
        create_collection(client, settings.collection)

    articles = iter_articles(settings.num_docs, workers=8)
    with tqdm(total=settings.num_docs, unit="doc") as progress:
        for chunk in batched(articles, CHUNK_SIZE):
            upload_articles(client, settings.collection, chunk)
            progress.update(len(chunk))


if __name__ == "__main__":
    main()
