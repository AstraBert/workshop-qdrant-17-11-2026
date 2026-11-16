import uvicorn

from self_hosted_qdrant.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run("self_hosted_qdrant.api:app", host=settings.host, port=settings.port)
