import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1"
MODEL = "baai/bge-m3"


def create_client(api_key: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )


async def embed(client: httpx.AsyncClient, text: str) -> list[float]:
    response = await client.post("/embeddings", json={"model": MODEL, "input": text})
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]
