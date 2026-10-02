"""Interfaces the CDMS core expects infrastructure adapters to implement."""

from collections.abc import Iterable, Iterator
from contextlib import AbstractContextManager
from typing import Protocol

from .domain import (
    IncomingProductObservation,
    ProductChange,
    ProductKey,
    ProcessingResult,
    StoredProductCursor,
)


class ChangeTransaction(Protocol):
    def claim_delivery(self, source: str, delivery_id: str) -> bool:
        """Atomically claim a delivery; return False when it already exists."""
        ...

    def lock_cursor(self, key: ProductKey) -> StoredProductCursor | None:
        """Load and lock the product cursor for the current transaction."""
        ...

    def append_change(self, change: ProductChange) -> None:
        """Append one accepted business change."""
        ...

    def save_cursor(self, cursor: StoredProductCursor) -> None:
        """Persist the latest version, canonical hash, and snapshot."""
        ...


class UnitOfWork(Protocol):
    def transaction(self) -> AbstractContextManager[ChangeTransaction]:
        """Return one atomic transaction boundary."""
        ...


class ProductSource(Protocol):
    def iter_product_pages(self) -> Iterator[Iterable[dict]]:
        """Yield source product pages without leaking HTTP into the core."""
        ...


class ChangeQuery(Protocol):
    def list_changes(self, key: ProductKey) -> Iterable[ProductChange]:
        """Return changes in deterministic version order."""
        ...


class ObservationSink(Protocol):
    def process(self, observation: IncomingProductObservation) -> ProcessingResult:
        """Process one canonical observation through the central use case."""
        ...
