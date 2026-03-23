import httpx

from app.config import Settings


class ExecutorClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.executor_base_url.rstrip("/")

    async def execute(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{self._base_url}/execute", json=payload)
            response.raise_for_status()
            return response.json()

