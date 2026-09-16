import httpx

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.config import ClientConfig


class HttpClient:

    def __init__(self, config: ClientConfig):
        self.client = httpx.AsyncClient(
            timeout=config.timeout
        )


    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=5
        ),
        retry=retry_if_exception_type(
            (
                httpx.TimeoutException,
                httpx.NetworkError
            )
        ),
        reraise=True
    )
    async def post(
        self,
        url: str,
        json: dict
    ):

        return await self.client.post(
            url,
            json=json
        )


    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=5
        ),
        retry=retry_if_exception_type(
            (
                httpx.TimeoutException,
                httpx.NetworkError
            )
        ),
        reraise=True
    )
    async def delete(
        self,
        url: str,
        json: dict
    ):

        return await self.client.delete(
            url,
            json=json
        )


    async def close(self):

        await self.client.aclose()