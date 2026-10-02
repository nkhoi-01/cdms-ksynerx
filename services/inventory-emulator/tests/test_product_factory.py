import unittest

from inventory_emulator.product_factory import ProductFactory


class ProductFactoryTests(unittest.TestCase):
    def test_same_seed_and_number_are_reproducible(self) -> None:
        first = ProductFactory(2604).build(1)
        second = ProductFactory(2604).build(1)

        self.assertEqual(first, second)

    def test_product_identity_is_stable_and_unique(self) -> None:
        products = ProductFactory(2604).build_many(3)

        self.assertEqual(
            ["SKU-00001", "SKU-00002", "SKU-00003"],
            [product.sku for product in products],
        )
        self.assertEqual(3, len({product.partner_sku for product in products}))

    def test_generation_does_not_depend_on_call_order(self) -> None:
        factory = ProductFactory(2604)

        product_three = factory.build(3)
        factory.build(1)
        factory.build(2)

        self.assertEqual(product_three, factory.build(3))


if __name__ == "__main__":
    unittest.main()
