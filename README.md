# From prototype to production with Qdrant

This repository holds three versions of one search app. The app searches PubMed abstracts. Each version uses more data and more Qdrant features than the one before.

Every version has a FastAPI server, a small web page for search, and a script that loads the data. The web page grows with each version. Each version is a separate uv package, so you can read and run it alone.

## The three steps

1. `prototype-with-edge`: 10,000 abstracts. Qdrant Edge stores the vectors inside the Python process. Search is dense only.
2. `self-hosted-qdrant`: 100,000 abstracts. Docker Compose runs the app and a Qdrant server. Search can also be keyword (BM25) or hybrid.
3. `qdrant-cloud`: 1,000,000 abstracts. A Qdrant Cloud cluster stores the vectors. Qdrant Cloud embeds the query for you. Search adds full-text search and filters.

Steps 1 and 2 call OpenRouter from the app to embed the query. Step 3 does not, because Qdrant Cloud Inference calls OpenRouter for you.

## The data

The data comes from the Hugging Face dataset `Qdrant/PubMed-MV`. Each row is one PubMed abstract with a dense vector from the BGE-M3 model. A dense vector is a list of 1024 numbers that describes the meaning of the text.

The dataset also holds sparse and multi-vector embeddings. We do not read them. Each step reads the first N rows, and the rows are always in the same order. This means that the 10,000 abstracts of step 1 are also in step 2 and step 3.

The dataset does not hold BM25 vectors. Step 2 makes them with Qdrant. Step 3 does not need them, because it uses a full-text index.

## Before you start

You need these tools:

- uv, to install the Python packages.
- Docker, for step 2.
- An OpenRouter API key.

Create a file named `.env` in the root of this repository and add your key:

```
OPENROUTER_API_KEY=your-key-here
```

Run every command from the root of this repository. Each package README lists its own commands and settings.

## Code check

Install all packages, then format, lint, and type check the code:

```bash
uv sync --all-packages
uv run ruff format
uv run ruff check --fix
uv run ty check packages/*/src
```

Each package has its own copy of `dataset.py`. We did this on purpose, so that a step does not depend on the other steps.
