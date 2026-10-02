import unittest

from inventory_emulator.domain import EmulatedProduct
from inventory_emulator.product_factory import ProductFactory
from inventory_emulator.store import ProductStore


class ProductStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = ProductStore(ProductFactory(2604).build_many(3))

    def test_paginates_in_product_id_order(self) -> None:
        page = self.store.list_page(page_index=2, page_size=2)

        self.assertEqual([3], [product.product_id for product in page])

    def test_update_increments_source_version_and_delivery_identity(self) -> None:
        current = self.store.get_by_id(1)
        assert current is not None

        mutation = self.store.update(
            1,
            current.with_updates({"productName": "Updated Product"}),
        )

        self.assertEqual(2, mutation.product.source_version)
        self.assertEqual("emulator:1:2:updated", mutation.delivery_id)

    def test_invalid_create_batch_is_atomic(self) -> None:
        first = EmulatedProduct(4, "SKU-004", "DUPLICATE", "First")
        second = EmulatedProduct(5, "SKU-005", "DUPLICATE", "Second")

        with self.assertRaisesRegex(ValueError, "duplicate partner SKUs"):
            self.store.create([first, second])

        self.assertIsNone(self.store.get("DUPLICATE"))


if __name__ == "__main__":
    unittest.main()
