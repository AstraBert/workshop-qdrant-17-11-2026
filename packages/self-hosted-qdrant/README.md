# Step 2: self-hosted Qdrant with hybrid search

This step searches 100,000 PubMed abstracts. Docker Compose runs two containers: the Python app and a Qdrant server. The web page has three search modes.

- Semantic: dense vectors only.
- Keyword: BM25 only. BM25 ranks documents by the words that they share with the query.
- Hybrid: both of the above, joined into one list.

## Run it

Build and start the containers:

```bash
docker compose -f packages/self-hosted-qdrant/compose.yaml up -d --build
```

Load the data. This takes a few minutes. You can run the command again if it stops, because it is safe to repeat.

```bash
docker compose -f packages/self-hosted-qdrant/compose.yaml run --rm app self-hosted-qdrant-ingest
```

Open http://localhost:8000 for the app. Open http://localhost:6333/dashboard for the Qdrant dashboard.

If a port is already in use, set `APP_PORT` or `QDRANT_PORT` before the command. For example, `APP_PORT=8080 docker compose ...`.

## Run without the app container

If you want to edit the code, start only Qdrant in Docker and run the app with uv:

```bash
docker compose -f packages/self-hosted-qdrant/compose.yaml up -d qdrant
uv run --package self-hosted-qdrant self-hosted-qdrant-ingest
uv run --package self-hosted-qdrant self-hosted-qdrant
```

## How a search works

Each point in the collection has two vectors. The `dense` vector comes from the dataset. The `bm25` vector is a sparse vector that Qdrant computes from the title and the abstract. A sparse vector holds a weight for each word that the text contains.

The collection sets the IDF modifier on the `bm25` vector. With this modifier, Qdrant gives a higher weight to rare words at query time.

In hybrid mode, the server does these steps:

1. The server sends the query text to OpenRouter and gets a dense vector. This is a separate step, as in step 1.
2. The server sends one Qdrant request with two prefetches. One prefetch searches the `dense` vector. The other prefetch searches the `bm25` vector with the query text.
3. Qdrant joins the two lists with reciprocal rank fusion (RRF). RRF scores a document by its rank in each list, so it does not need to compare the scores of the two lists.

Keyword mode skips OpenRouter, because BM25 needs no dense vector.

## Settings

- `OPENROUTER_API_KEY`: Your OpenRouter key. This value is required.
- `NUM_DOCS`: The number of abstracts to load. The default is 100000.
- `QDRANT_URL`: The address of Qdrant. The default is http://localhost:6333. Compose sets it to the Qdrant container.
- `COLLECTION`: The name of the collection. The default is `pubmed`.

## Files

- `store.py`: Creates the collection, fills it, and runs the three kinds of search.
- `ingest.py`: The script that loads the data.
- `api.py`: The FastAPI server. It also serves the web page in `static/`.
- `Dockerfile` and `compose.yaml`: Build and run the containers. The build context is the root of the repository.
