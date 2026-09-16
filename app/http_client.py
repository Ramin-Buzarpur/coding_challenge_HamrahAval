import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from app.config import ClientConfig
from app.exceptions import TransientAPIError
from app.logger import get_logger

logger = get_logger(__name__)

# Errors that are worth retrying: the request never got a real answer, or the
# node answered with a 5xx, which the task description says can happen for
# unknown reasons.
RETRYABLE = (
    httpx.TimeoutException,
    httpx.NetworkError,
    TransientAPIError,
)


class HttpClient:
    """Thin wrapper around httpx that adds timeouts and retries.

    It knows nothing about groups; it only speaks HTTP. That keeps the
    retry logic in one place and makes the cluster logic easy to test.
    """

    def __init__(self, config: ClientConfig, client: httpx.AsyncClient | None = None):
        self.config = config
        self.client = client or httpx.AsyncClient(timeout=config.timeout)

    async def post(self, url: str, payload: dict) -> httpx.Response:
        return await self._request("POST", url, payload)

    async def delete(self, url: str, payload: dict) -> httpx.Response:
        # httpx.AsyncClient.delete() does not accept a body, so the generic
        # request() method is used instead.
        return await self._request("DELETE", url, payload)

    async def get(self, url: str) -> httpx.Response:
        return await self._request("GET", url, None)

    async def _request(self, method: str, url: str, payload: dict | None) -> httpx.Response:
        retryer = AsyncRetrying(
            stop=stop_after_attempt(self.config.max_attempts),
            wait=(
                wait_exponential(
                    multiplier=self.config.backoff_multiplier,
                    max=self.config.backoff_max,
                )
                # A little jitter so all nodes do not retry at the same moment.
                + wait_random(0, 0.3)
            ),
            retry=retry_if_exception_type(RETRYABLE),
            reraise=True,
        )

        async for attempt in retryer:
            with attempt:
                number = attempt.retry_state.attempt_number

                if number > 1:
                    logger.warning("retrying %s %s (attempt %s)", method, url, number)

                response = await self.client.request(method, url, json=payload)

                if response.status_code >= 500:
                    raise TransientAPIError(
                        f"{method} {url} returned {response.status_code}"
                    )

                return response

    async def close(self) -> None:
        await self.client.aclose()
