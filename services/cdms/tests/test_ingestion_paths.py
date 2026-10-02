from datetime import UTC, datetime
import unittest

from cdms.adapters.memory import MemoryDatabase, MemoryUnitOfWork
from cdms.domain import IncomingProductObservation
from cdms.normalization import normalize_vietful_product
from cdms.process_change import ProcessProductObservation


class IngestionPathTests(unittest.TestCase):
    def test_different_paths_share_content_deduplication(self) -> None:
        database = MemoryDatabase()
        processor = ProcessProductObservation(MemoryUnitOfWork(database))
        snapshot = normalize_vietful_product(
            {
                "productId": 7,
                "sku": "SKU-007",
                "partnerSKU": "PARTNER-007",
                "productName": "Shared Product",
                "units": ["EACH"],
                "categories": [],
            }
        )

        polling = processor.execute(
            IncomingProductObservation(
                ingestion_source="polling",
                delivery_id="poll-1",
                observed_at=datetime.now(UTC),
                snapshot=snapshot,
            )
        )
        webhook = processor.execute(
            IncomingProductObservation(
                ingestion_source="webhook",
                delivery_id="webhook-1",
                observed_at=datetime.now(UTC),
                snapshot=snapshot,
            )
        )

        self.assertEqual("stored", polling.status)
        self.assertEqual("unchanged", webhook.status)
        self.assertEqual(1, len(database.changes))


if __name__ == "__main__":
    unittest.main()
