"""Webhook delivery behavior, including controlled retries and failures."""

from .domain import ProductMutation


class CallbackPublisher:
    def publish(self, mutation: ProductMutation) -> None:
        # TODO: Build a stable delivery ID and send the configured callback.
        # TODO: Retry with bounded backoff while preserving the delivery ID.
        # TODO: Support deliberate delay/duplication/failure test modes.
        raise NotImplementedError

