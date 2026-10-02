"""HTTP adapter for the V1 VietFul-compatible Products API."""

from collections.abc import Iterable, Iterator

import httpx


class VietfulProductClient:
    def __init__(
        self,
        base_url: str,
        *,
        client: httpx.Client | None = None,
        page_size: int = 100,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._page_size = page_size
        self._owns_client = client is None

    def iter_product_pages(self) -> Iterator[Iterable[dict]]:
        page_index = 1
        while True:
            response = self._client.get(
                f"{self._base_url}/api/v1/Products",
                params={"PageIndex": page_index, "PageSize": self._page_size},
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("VietFul Products response must be an array")
            if not payload:
                return
            yield payload
            if len(payload) < self._page_size:
                return
            page_index += 1

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
