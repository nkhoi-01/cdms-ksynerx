"""HTTP adapter for the V1 VietFul-compatible Products API."""

from collections.abc import Iterable, Iterator


class VietfulProductClient:
    def __init__(self, base_url: str) -> None:
        # TODO: Accept an injected HTTP client, credentials, retry policy, and timeout.
        raise NotImplementedError

    def iter_product_pages(self) -> Iterator[Iterable[dict]]:
        # TODO: Call GET /api/v1/Products until all pages are consumed.
        # TODO: Fail explicitly on malformed responses; never silently skip a page.
        raise NotImplementedError

