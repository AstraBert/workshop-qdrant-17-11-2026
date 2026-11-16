import uvicorn

from qdrant_cloud.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run("qdrant_cloud.api:app", host=settings.host, port=settings.port)
