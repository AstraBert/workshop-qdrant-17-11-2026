# Build from the repository root: the uv workspace lives there.
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY packages ./packages
RUN uv sync --frozen --no-dev --package self-hosted-qdrant

ENV PATH="/app/.venv/bin:$PATH" HOST=0.0.0.0 PORT=8000
EXPOSE 8000
CMD ["self-hosted-qdrant"]
