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
        # TODO: Atomically claim a delivery; return False when already claimed.
        ...

    def lock_cursor(self, key: ProductKey) -> StoredProductCursor | None:
        # TODO: Load and lock the current product cursor for concurrent safety.
        ...

    def append_change(self, change: ProductChange) -> None:
        # TODO: Append one accepted business change.
        ...

    def save_cursor(self, cursor: StoredProductCursor) -> None:
        # TODO: Persist the latest entity version and canonical hash.
        ...


class UnitOfWork(Protocol):
    def transaction(self) -> AbstractContextManager[ChangeTransaction]:
        # TODO: Return one atomic database transaction boundary.
        ...


class ProductSource(Protocol):
    def iter_product_pages(self) -> Iterator[Iterable[dict]]:
        # TODO: Fetch every source page without leaking HTTP details to the core.
        ...


class SpreadsheetReader(Protocol):
    def read_rows(self, content: bytes) -> Iterable[dict]:
        # TODO: Yield validated row dictionaries from an uploaded workbook.
        ...


class ChangeQuery(Protocol):
    def list_changes(self, key: ProductKey) -> Iterable[ProductChange]:
        # TODO: Return ordered changes for the query API.
        ...


class ObservationSink(Protocol):
    def process(self, observation: IncomingProductObservation) -> ProcessingResult:
        # TODO: Accept one canonical observation through the central use case.
        ...
