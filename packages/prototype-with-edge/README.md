# Step 1: prototype with Qdrant Edge

This step searches 10,000 PubMed abstracts with dense vectors. It needs no server and no Docker.

Qdrant Edge is a Qdrant library that runs inside your own process. It stores the data in a local folder. That folder is called a shard.

## Run it

Load the data into a new shard. This takes about 15 seconds.

```bash
uv run --package prototype-with-edge prototype-with-edge-ingest
```

Start the server:

```bash
uv run --package prototype-with-edge prototype-with-edge
```

Open http://127.0.0.1:8000 in your browser.

If you want to load the data again, delete the folder `data/edge-shard` first.

## How a search works

The server does two separate steps for each search.

1. The server sends the query text to OpenRouter. OpenRouter runs the `baai/bge-m3` model and returns a dense vector.
2. The server sends that vector to the Edge shard. The shard returns the closest abstracts.

The web page shows the time of each step. The first step is slow because it is a network call. The second step is fast because the data is local.

The vectors in the dataset and the vectors from OpenRouter come from the same model. This is why they can be compared.

## Settings

You can set these values in `.env` or as environment variables:

- `OPENROUTER_API_KEY`: Your OpenRouter key. This value is required.
- `NUM_DOCS`: The number of abstracts to load. The default is 10000.
- `SHARD_PATH`: The folder of the shard. The default is `data/edge-shard`.
- `HOST` and `PORT`: The address of the server. The defaults are 127.0.0.1 and 8000.

## Files

- `dataset.py`: Reads abstracts and vectors from Hugging Face.
- `embeddings.py`: Calls OpenRouter.
- `store.py`: Creates, fills, and searches the Edge shard.
- `ingest.py`: The script that loads the data.
- `api.py`: The FastAPI server. It also serves the web page in `static/`.

Edge has no background optimizer. The ingest script calls `shard.optimize()` at the end to build the HNSW index. HNSW is the index that makes vector search fast. Without this call, Edge does not build the index.
