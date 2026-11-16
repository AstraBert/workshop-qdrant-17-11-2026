import uvicorn

from prototype_with_edge.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run("prototype_with_edge.api:app", host=settings.host, port=settings.port)
