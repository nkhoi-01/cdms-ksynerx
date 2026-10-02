import unittest

import httpx

from inventory_emulator.api import create_app
from inventory_emulator.callbacks import CallbackPublisher
from inventory_emulator.product_factory import ProductFactory
from inventory_emulator.store import ProductStore


class InventoryApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        store = ProductStore(ProductFactory(2604).build_many(3))
        app = create_app(store, CallbackPublisher(None))
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://inventory.test",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_lists_vietful_products_with_pagination(self) -> None:
        response = await self.client.get(
            "/api/v1/Products",
            params={"PageIndex": 2, "PageSize": 2},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual([3], [item["productId"] for item in response.json()])

    async def test_gets_product_by_partner_sku(self) -> None:
        response = await self.client.get("/api/v1/Products/PARTNER-00001")

        self.assertEqual(200, response.status_code)
        self.assertEqual("SKU-00001", response.json()["sku"])

    async def test_mutates_product_for_repeatable_demo(self) -> None:
        response = await self.client.post(
            "/internal/products/1/mutate",
            params={"callback_copies": 0},
            json={"productName": "Interview Demo Product"},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("emulator:1:2:updated", response.json()["deliveryId"])
        self.assertEqual("Interview Demo Product", response.json()["product"]["productName"])


if __name__ == "__main__":
    unittest.main()
