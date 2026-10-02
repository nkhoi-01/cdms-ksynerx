"""PostgreSQL implementation of transactions and change queries."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from ..domain import ProductChange, ProductKey, ProductSnapshot, StoredProductCursor


ConnectionFactory = Callable[[], psycopg.Connection]


def create_connection_factory(database_url: str) -> ConnectionFactory:
    return lambda: psycopg.connect(database_url, row_factory=dict_row)


class PostgresChangeTransaction:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def claim_delivery(self, source: str, delivery_id: str) -> bool:
        row = self._connection.execute(
            """
            INSERT INTO ingestion_receipts (ingestion_source, delivery_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            RETURNING delivery_id
            """,
            (source, delivery_id),
        ).fetchone()
        return row is not None

    def lock_cursor(self, key: ProductKey) -> StoredProductCursor | None:
        lock_identity = f"{key.source_system}:{key.partner_sku}"
        self._connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (lock_identity,),
        )
        row = self._connection.execute(
            """
            SELECT version, content_hash, snapshot
            FROM product_cursors
            WHERE source_system = %s AND partner_sku = %s
            FOR UPDATE
            """,
            (key.source_system, key.partner_sku),
        ).fetchone()
        if row is None:
            return None
        return StoredProductCursor(
            key=key,
            version=row["version"],
            content_hash=row["content_hash"],
            snapshot=ProductSnapshot.from_dict(row["snapshot"]),
        )

    def append_change(self, change: ProductChange) -> None:
        self._connection.execute(
            """
            INSERT INTO product_changes (
                source_system, partner_sku, version, change_type,
                changed_fields, content_hash, snapshot,
                ingestion_source, delivery_id, observed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                change.key.source_system,
                change.key.partner_sku,
                change.version,
                change.change_type,
                list(change.changed_fields),
                change.content_hash,
                Jsonb(change.snapshot.to_dict()),
                change.ingestion_source,
                change.delivery_id,
                change.observed_at,
            ),
        )

    def save_cursor(self, cursor: StoredProductCursor) -> None:
        self._connection.execute(
            """
            INSERT INTO product_cursors (
                source_system, partner_sku, version, content_hash, snapshot
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (source_system, partner_sku) DO UPDATE SET
                version = EXCLUDED.version,
                content_hash = EXCLUDED.content_hash,
                snapshot = EXCLUDED.snapshot,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                cursor.key.source_system,
                cursor.key.partner_sku,
                cursor.version,
                cursor.content_hash,
                Jsonb(cursor.snapshot.to_dict()),
            ),
        )


class PostgresUnitOfWork:
    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    @contextmanager
    def transaction(self) -> Iterator[PostgresChangeTransaction]:
        connection = self._connection_factory()
        try:
            with connection.transaction():
                yield PostgresChangeTransaction(connection)
        finally:
            connection.close()


class PostgresChangeQuery:
    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def list_changes(self, key: ProductKey) -> list[ProductChange]:
        connection = self._connection_factory()
        try:
            rows = connection.execute(
                """
                SELECT version, change_type, changed_fields, content_hash,
                       snapshot, ingestion_source, delivery_id, observed_at
                FROM product_changes
                WHERE source_system = %s AND partner_sku = %s
                ORDER BY version
                """,
                (key.source_system, key.partner_sku),
            ).fetchall()
        finally:
            connection.close()
        return [
            ProductChange(
                key=key,
                version=row["version"],
                change_type=row["change_type"],
                changed_fields=tuple(row["changed_fields"]),
                content_hash=row["content_hash"],
                snapshot=ProductSnapshot.from_dict(row["snapshot"]),
                ingestion_source=row["ingestion_source"],
                delivery_id=row["delivery_id"],
                observed_at=row["observed_at"],
            )
            for row in rows
        ]


def apply_migrations(
    connection_factory: ConnectionFactory,
    migration_directory: Path | None = None,
) -> None:
    directory = migration_directory or Path(__file__).parents[3] / "migrations"
    connection = connection_factory()
    try:
        with connection.transaction():
            for migration in sorted(directory.glob("*.sql")):
                connection.execute(migration.read_text(encoding="utf-8"))
    finally:
        connection.close()
