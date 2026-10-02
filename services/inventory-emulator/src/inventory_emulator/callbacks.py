"""Webhook delivery behavior with stable retry identities."""

import time

import httpx

from .domain import ProductMutation


class CallbackPublisher:
    def __init__(
        self,
        callback_url: str | None,
        *,
        attempts: int = 3,
        timeout_seconds: float = 2.0,
    ) -> None:
        self._callback_url = callback_url
        self._attempts = attempts
        self._timeout_seconds = timeout_seconds

    def publish(self, mutation: ProductMutation) -> bool:
        if not self._callback_url:
            return False
        for attempt in range(1, self._attempts + 1):
            try:
                response = httpx.post(
                    self._callback_url,
                    json=mutation.webhook_payload(),
                    timeout=self._timeout_seconds,
                )
                if response.is_success:
                    return True
            except httpx.HTTPError:
                pass
            if attempt < self._attempts:
                time.sleep(0.1 * attempt)
        return False
