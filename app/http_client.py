import httpx

from app.config import ClientConfig


class HttpClient:
    def __init__(self, config: ClientConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout
        )

    async def post(self, url: str, json: dict):
        response = await self.client.post(
            url,
            json=json
        )

        return response

    async def delete(self, url: str, json: dict):
        response = await self.client.delete(
            url,
            json=json
        )

        return response

    async def close(self):
        await self.client.aclose()