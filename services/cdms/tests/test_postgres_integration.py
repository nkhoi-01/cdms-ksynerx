from datetime import UTC, datetime
from concurrent.futures import ThreadPoolExecutor
import os
import unittest

from cdms.adapters.postgres import (
    PostgresChangeQuery,
    PostgresUnitOfWork,
    apply_migrations,
    create_connection_factory,
)
from cdms.domain import IncomingProductObservation, ProductKey
from cdms.normalization import normalize_vietful_product
from cdms.process_change import ProcessProductObservation


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@unittest.skipUnless(TEST_DATABASE_URL, "TEST_DATABASE_URL is not configured")
class PostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        assert TEST_DATABASE_URL is not None
        cls.connection_factory = staticmethod(
            create_connection_factory(TEST_DATABASE_URL)
        )
        apply_migrations(cls.connection_factory)

    def setUp(self) -> None:
        connection = self.connection_factory()
        try:
            with connection.transaction():
                connection.execute(
                    "TRUNCATE product_changes, product_cursors, ingestion_receipts"
                )
        finally:
            connection.close()

    @staticmethod
    def observation(delivery_id: str, name: str) -> IncomingProductObservation:
        return IncomingProductObservation(
            ingestion_source="postgres-test",
            delivery_id=delivery_id,
            observed_at=datetime.now(UTC),
            snapshot=normalize_vietful_product(
                {
                    "productId": 1,
                    "sku": "SKU-PG-001",
                    "partnerSKU": "PARTNER-PG-001",
                    "productName": name,
                    "units": ["EACH"],
                    "categories": [],
                }
            ),
        )

    def test_migration_and_idempotent_version_flow(self) -> None:
        processor = ProcessProductObservation(
            PostgresUnitOfWork(self.connection_factory)
        )

        first = processor.execute(self.observation("delivery-1", "First"))
        duplicate = processor.execute(self.observation("delivery-1", "First"))
        unchanged = processor.execute(self.observation("delivery-2", "First"))
        updated = processor.execute(self.observation("delivery-3", "Second"))
        changes = PostgresChangeQuery(self.connection_factory).list_changes(
            ProductKey("vietful-emulator", "PARTNER-PG-001")
        )

        self.assertEqual("stored", first.status)
        self.assertEqual("duplicate", duplicate.status)
        self.assertEqual("unchanged", unchanged.status)
        self.assertEqual("stored", updated.status)
        self.assertEqual([1, 2], [change.version for change in changes])
        self.assertEqual(("productName",), changes[1].changed_fields)

    def test_concurrent_duplicate_delivery_commits_once(self) -> None:
        processor = ProcessProductObservation(
            PostgresUnitOfWork(self.connection_factory)
        )
        shared = self.observation("concurrent-delivery", "Concurrent Product")

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: processor.execute(shared), range(20)))

        statuses = [result.status for result in results]
        changes = PostgresChangeQuery(self.connection_factory).list_changes(
            ProductKey("vietful-emulator", "PARTNER-PG-001")
        )
        self.assertEqual(1, statuses.count("stored"))
        self.assertEqual(19, statuses.count("duplicate"))
        self.assertEqual(1, len(changes))


if __name__ == "__main__":
    unittest.main()
