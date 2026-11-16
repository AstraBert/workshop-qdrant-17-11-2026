# Step 3: Qdrant Cloud with Cloud Inference, full-text search, and filters

This step searches 1,000,000 PubMed abstracts on a Qdrant Cloud cluster. The app does not embed the query. Qdrant Cloud Inference does it inside the search request, and it calls OpenRouter for the `baai/bge-m3` model.

The web page has the three search modes of step 2 and a filter panel.

## Create the cluster

1. Open the Qdrant Cloud console and create a dedicated cluster with 4 vCPUs, 16 GiB of RAM, and 64 GiB of disk.
2. Open the Inference tab of the cluster. If Cloud Inference is off, turn it on.
3. Create an API key for the cluster.
4. Add the cluster URL and the key to the `.env` file in the root of this repository:

```
QDRANT_URL=https://your-cluster-id.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-key
```

## Run it

Load the data. The script reads about 6 GB from Hugging Face, so start it well before the workshop. You can run the command again if it stops, because it is safe to repeat.

```bash
uv run --package qdrant-cloud qdrant-cloud-ingest
```

Start the server:

```bash
uv run --package qdrant-cloud qdrant-cloud
```

Open http://127.0.0.1:8000 in your browser.

## How a search works

The app sends one request to Qdrant. The request holds the query text and the name of the model, `openrouter/baai/bge-m3`. It also holds your OpenRouter key, because Qdrant does not store keys. Qdrant Cloud calls OpenRouter, gets the vector, and searches with it.

Because of this, the web page shows one time for the whole search. The time includes the embedding.

## Full-text search

The collection has a full-text index on the `title` field and on the `content` field. Both indexes have scoring on, which means that Qdrant ranks the matches with BM25. The indexes use English stemming and English stopwords. A stemmer reduces a word to its root, and stopwords are common words such as "the" that Qdrant ignores.

Keyword mode runs a text query on each field and joins the two lists with RRF. Hybrid mode adds the dense search as a third list. The dense list has a weight of 2, so it counts as much as the two text lists together.

## Filters

The filter panel has four inputs:

- Title contains all of: The title must hold all of these words.
- Abstract contains none of: The abstract must hold none of these words.
- PMID from and PMID to: The PubMed ID must be in this range. A higher PMID usually means a newer article.

The first two filters use the full-text indexes. The PMID filter uses an integer index. The app creates all three indexes before it loads the data.

The app adds the filter to each prefetch of a hybrid query. A filter on the main query alone would not reach the prefetches.

## Settings

- `OPENROUTER_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY`: These values are required.
- `NUM_DOCS`: The number of abstracts to load. The default is 1000000.
- `COLLECTION`: The name of the collection. The default is `pubmed`.
- `HOST` and `PORT`: The address of the server. The defaults are 127.0.0.1 and 8000.

## Files

- `store.py`: Creates the collection and the indexes, loads the points, and runs the searches.
- `ingest.py`: The script that loads the data.
- `api.py`: The FastAPI server. It also serves the web page in `static/`.
