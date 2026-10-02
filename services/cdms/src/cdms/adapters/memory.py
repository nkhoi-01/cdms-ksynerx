"""Thread-safe in-memory adapter for local demos and fast correctness tests."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import RLock

from ..domain import ProductChange, ProductKey, StoredProductCursor


@dataclass(slots=True)
class MemoryDatabase:
    receipts: set[tuple[str, str]] = field(default_factory=set)
    cursors: dict[ProductKey, StoredProductCursor] = field(default_factory=dict)
    changes: list[ProductChange] = field(default_factory=list)
    lock: RLock = field(default_factory=RLock)


class MemoryChangeTransaction:
    def __init__(self, database: MemoryDatabase) -> None:
        self._database = database

    def claim_delivery(self, source: str, delivery_id: str) -> bool:
        identity = (source, delivery_id)
        if identity in self._database.receipts:
            return False
        self._database.receipts.add(identity)
        return True

    def lock_cursor(self, key: ProductKey) -> StoredProductCursor | None:
        return self._database.cursors.get(key)

    def append_change(self, change: ProductChange) -> None:
        self._database.changes.append(change)

    def save_cursor(self, cursor: StoredProductCursor) -> None:
        self._database.cursors[cursor.key] = cursor


class MemoryUnitOfWork:
    def __init__(self, database: MemoryDatabase) -> None:
        self.database = database

    @contextmanager
    def transaction(self) -> Iterator[MemoryChangeTransaction]:
        with self.database.lock:
            receipts_before = set(self.database.receipts)
            cursors_before = dict(self.database.cursors)
            changes_before = list(self.database.changes)
            try:
                yield MemoryChangeTransaction(self.database)
            except Exception:
                self.database.receipts = receipts_before
                self.database.cursors = cursors_before
                self.database.changes = changes_before
                raise


class MemoryChangeQuery:
    def __init__(self, database: MemoryDatabase) -> None:
        self._database = database

    def list_changes(self, key: ProductKey) -> list[ProductChange]:
        with self._database.lock:
            return [change for change in self._database.changes if change.key == key]
