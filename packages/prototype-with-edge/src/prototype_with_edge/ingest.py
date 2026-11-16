from itertools import batched

from tqdm import tqdm

from prototype_with_edge.config import get_settings
from prototype_with_edge.dataset import iter_articles
from prototype_with_edge.store import create_shard, upsert_articles

BATCH_SIZE = 500


def main() -> None:
    settings = get_settings()
    if settings.shard_path.exists() and any(settings.shard_path.iterdir()):
        raise SystemExit(
            f"{settings.shard_path} is not empty. Delete it to start over."
        )

    shard = create_shard(settings.shard_path)
    articles = iter_articles(settings.num_docs)
    with tqdm(total=settings.num_docs, unit="doc") as progress:
        for batch in batched(articles, BATCH_SIZE):
            upsert_articles(shard, batch)
            progress.update(len(batch))

    # Edge has no background optimizer. This call builds the HNSW index.
    shard.optimize()
    shard.close()


if __name__ == "__main__":
    main()
