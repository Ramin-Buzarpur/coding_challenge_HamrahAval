import httpx
from app.exceptions import APIRequestException
from app.retry import retry_policy
from app.config import ClientConfig

@retry_policy()
async def post(self, url: str, json: dict):

    try:
        response = await self.client.post(
            url,
            json=json
        )

        response.raise_for_status()

        return response

    except Exception as exc:
        raise APIRequestException(str(exc))
    
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