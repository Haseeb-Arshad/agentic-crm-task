from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .error_handler import ApiError
from .logger import get_logger


logger = get_logger(__name__)


class AsyncApiClient:
    def __init__(self, base_url: str, default_headers: Optional[Dict[str, str]] = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.timeout = httpx.Timeout(timeout)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        await self.ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def ensure_session(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _merge_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        merged = dict(self.default_headers)
        if headers:
            merged.update(headers)
        return merged

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
    )
    async def request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> Any:
        client = await self.ensure_session()
        merged_headers = self._merge_headers(headers)
        url = path if path.startswith("/") else f"/{path}"
        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=merged_headers,
                params=params,
                json=json,
            )
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    body: Any = response.json()
                except ValueError:
                    body = response.text
            else:
                body = response.text

            if 200 <= response.status_code < 300:
                return body

            logger.error(
                "HTTP error",
                extra={"status": response.status_code, "url": response.request.url, "body": body},
            )
            raise ApiError(response.status_code, "HTTP request failed", details=body)
        except (httpx.HTTPError, asyncio.TimeoutError) as exc:
            logger.warning(
                "Transient HTTP exception, will retry if attempts remain",
                extra={"error": str(exc), "url": f"{self.base_url}{url}"},
            )
            raise

    async def get(self, path: str, **kwargs) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Any:
        return await self.request("POST", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> Any:
        return await self.request("PATCH", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Any:
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Any:
        return await self.request("DELETE", path, **kwargs)
