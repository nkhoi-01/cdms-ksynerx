import unittest

import httpx

from cdms.adapters.memory import MemoryChangeQuery, MemoryDatabase, MemoryUnitOfWork
from cdms.api import create_app
from cdms.polling import PollReport
from cdms.process_change import ProcessProductObservation


class StubPoller:
    def run_once(self) -> PollReport:
        return PollReport(processed=0, stored=0, unchanged=0, duplicate=0)


class CdmsApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        database = MemoryDatabase()
        processor = ProcessProductObservation(MemoryUnitOfWork(database))
        app = create_app(
            processor,
            MemoryChangeQuery(database),
            StubPoller(),
            database_backend="memory",
        )
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://cdms.test",
        )
        self.webhook = {
            "id": "webhook-001",
            "event": "PRODUCT_CHANGED",
            "product": {
                "productId": 1,
                "sku": "SKU-001",
                "partnerSKU": "PARTNER-001",
                "productName": "Demo Product",
                "units": ["EACH"],
                "categories": [],
            },
        }

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_webhook_is_idempotent_and_query_returns_one_change(self) -> None:
        first = await self.client.post("/webhooks/products", json=self.webhook)
        duplicate = await self.client.post("/webhooks/products", json=self.webhook)
        changes = await self.client.get("/products/PARTNER-001/changes")

        self.assertEqual("stored", first.json()["status"])
        self.assertEqual("duplicate", duplicate.json()["status"])
        self.assertEqual(1, len(changes.json()))
        self.assertEqual(1, changes.json()[0]["version"])

    async def test_rejects_webhook_without_delivery_id(self) -> None:
        response = await self.client.post(
            "/webhooks/products",
            json={"product": self.webhook["product"]},
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual("webhook id is required", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
