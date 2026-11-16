from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from itertools import islice
from typing import TypedDict

import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem

DATA_DIR = "datasets/Qdrant/PubMed-MV/data"
# Each file also holds sparse and multi-vector columns. We read only these four.
COLUMNS = ["PMID", "title", "content", "bge_m3_dense_embedding"]


class Article(TypedDict):
    id: int
    pmid: int
    title: str
    content: str
    embedding: list[float]


def _list_files(fs: HfFileSystem) -> Iterator[str]:
    for directory in sorted(fs.ls(DATA_DIR, detail=False)):
        yield from sorted(fs.ls(directory, detail=False))


def _read_file(fs: HfFileSystem, path: str) -> list[dict]:
    with fs.open(path) as file:
        return pq.ParquetFile(file).read(columns=COLUMNS).to_pylist()


def iter_articles(limit: int, workers: int = 4) -> Iterator[Article]:
    """Yield the first `limit` articles. The same limit always gives the same articles."""
    fs = HfFileSystem()
    files = _list_files(fs)
    count = 0
    with ThreadPoolExecutor(workers) as pool:
        while paths := list(islice(files, workers)):
            for rows in pool.map(partial(_read_file, fs), paths):
                for row in rows:
                    if count == limit:
                        return
                    yield Article(
                        id=count,
                        pmid=row["PMID"],
                        title=row["title"],
                        content=row["content"],
                        embedding=row["bge_m3_dense_embedding"],
                    )
                    count += 1
