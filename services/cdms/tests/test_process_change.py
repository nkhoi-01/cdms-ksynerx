from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
import unittest

from cdms.adapters.memory import MemoryChangeTransaction, MemoryDatabase, MemoryUnitOfWork
from cdms.domain import IncomingProductObservation
from cdms.normalization import normalize_vietful_product
from cdms.process_change import ProcessProductObservation


def observation(delivery_id: str, name: str = "Demo Product") -> IncomingProductObservation:
    return IncomingProductObservation(
        ingestion_source="test",
        delivery_id=delivery_id,
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        snapshot=normalize_vietful_product(
            {
                "productId": 1,
                "sku": "SKU-001",
                "partnerSKU": "PARTNER-001",
                "productName": name,
                "units": ["EACH"],
                "categories": [{"categoryCode": "DEMO"}],
            }
        ),
    )


class FailingTransaction(MemoryChangeTransaction):
    def append_change(self, change) -> None:
        raise RuntimeError("simulated insert failure")


class FailingUnitOfWork(MemoryUnitOfWork):
    @contextmanager
    def transaction(self):
        with self.database.lock:
            receipts_before = set(self.database.receipts)
            try:
                yield FailingTransaction(self.database)
            except Exception:
                self.database.receipts = receipts_before
                raise


class ProcessProductObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = MemoryDatabase()
        self.processor = ProcessProductObservation(MemoryUnitOfWork(self.database))

    def test_first_observation_is_version_one(self) -> None:
        result = self.processor.execute(observation("delivery-1"))

        self.assertEqual("stored", result.status)
        self.assertEqual(1, result.version)
        self.assertEqual(1, len(self.database.changes))

    def test_repeated_delivery_is_duplicate(self) -> None:
        self.processor.execute(observation("delivery-1"))

        result = self.processor.execute(observation("delivery-1"))

        self.assertEqual("duplicate", result.status)
        self.assertEqual(1, len(self.database.changes))

    def test_new_delivery_with_same_content_is_unchanged(self) -> None:
        self.processor.execute(observation("delivery-1"))

        result = self.processor.execute(observation("delivery-2"))

        self.assertEqual("unchanged", result.status)
        self.assertEqual(1, result.version)
        self.assertEqual(1, len(self.database.changes))

    def test_changed_content_creates_next_version(self) -> None:
        self.processor.execute(observation("delivery-1"))

        result = self.processor.execute(observation("delivery-2", "Renamed Product"))

        self.assertEqual("stored", result.status)
        self.assertEqual(2, result.version)
        self.assertEqual(("productName",), result.changed_fields)
        self.assertEqual(2, len(self.database.changes))

    def test_failure_rolls_back_delivery_receipt(self) -> None:
        database = MemoryDatabase()
        failing = ProcessProductObservation(FailingUnitOfWork(database))

        with self.assertRaisesRegex(RuntimeError, "simulated insert failure"):
            failing.execute(observation("retryable-delivery"))

        self.assertNotIn(("test", "retryable-delivery"), database.receipts)
        successful = ProcessProductObservation(MemoryUnitOfWork(database)).execute(
            observation("retryable-delivery")
        )
        self.assertEqual("stored", successful.status)

    def test_concurrent_duplicate_spike_stores_one_change(self) -> None:
        shared_observation = observation("spike-delivery")

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(
                executor.map(
                    lambda _: self.processor.execute(shared_observation),
                    range(50),
                )
            )

        statuses = [result.status for result in results]
        self.assertEqual(1, statuses.count("stored"))
        self.assertEqual(49, statuses.count("duplicate"))
        self.assertEqual(1, len(self.database.changes))


if __name__ == "__main__":
    unittest.main()
