from dataclasses import replace
import unittest

from cdms.normalization import canonical_content_hash, normalize_vietful_product


PRODUCT = {
    "productId": 1,
    "sku": " SKU-001 ",
    "partnerSKU": "PARTNER-001",
    "productName": " Demo Product ",
    "assetType": "Single",
    "hasSerial": False,
    "hasExpiration": False,
    "color": " Blue ",
    "size": None,
    "description": "A demo product",
    "isActive": True,
    "units": ["BOX", "EACH", "BOX"],
    "categories": [
        {"categoryCode": "HOME"},
        {"categoryCode": "DEMO"},
    ],
    "transportTimestamp": 123,
}


class NormalizationTests(unittest.TestCase):
    def test_normalizes_and_sorts_unordered_fields(self) -> None:
        reordered = {
            **PRODUCT,
            "units": ["EACH", "BOX"],
            "categories": list(reversed(PRODUCT["categories"])),
            "transportTimestamp": 999,
        }

        first = normalize_vietful_product(PRODUCT)
        second = normalize_vietful_product(reordered)

        self.assertEqual(("BOX", "EACH"), first.units)
        self.assertEqual(("DEMO", "HOME"), first.categories)
        self.assertEqual(canonical_content_hash(first), canonical_content_hash(second))

    def test_business_change_changes_hash(self) -> None:
        original = normalize_vietful_product(PRODUCT)
        renamed = replace(original, product_name="Renamed Product")

        self.assertNotEqual(
            canonical_content_hash(original),
            canonical_content_hash(renamed),
        )

    def test_uses_sku_when_partner_sku_is_missing(self) -> None:
        snapshot = normalize_vietful_product({**PRODUCT, "partnerSKU": None})

        self.assertEqual("SKU-001", snapshot.key.partner_sku)

    def test_rejects_missing_identity(self) -> None:
        with self.assertRaisesRegex(ValueError, "sku is required"):
            normalize_vietful_product({**PRODUCT, "sku": None, "partnerSKU": None})


if __name__ == "__main__":
    unittest.main()
