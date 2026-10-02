"""In-memory product-state types owned by the emulator service."""

from dataclasses import dataclass
from typing import Any


def _text(value: Any, field: str) -> str:
    normalized = str(value).strip() if value is not None else ""
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized


@dataclass(frozen=True, slots=True)
class EmulatedProduct:
    product_id: int
    sku: str
    partner_sku: str
    product_name: str
    asset_type: str = "Single"
    has_serial: bool = False
    has_expiration: bool = False
    color: str | None = None
    size: str | None = None
    description: str | None = None
    is_active: bool = True
    units: tuple[str, ...] = ("EACH",)
    categories: tuple[str, ...] = ("GENERAL",)
    source_version: int = 1

    def to_vietful_dict(self) -> dict[str, Any]:
        return {
            "productId": self.product_id,
            "sku": self.sku,
            "partnerSKU": self.partner_sku,
            "productName": self.product_name,
            "assetType": self.asset_type,
            "hasSerial": self.has_serial,
            "hasExpiration": self.has_expiration,
            "color": self.color,
            "size": self.size,
            "description": self.description,
            "isActive": self.is_active,
            "units": list(self.units),
            "categories": [
                {"categoryCode": category} for category in self.categories
            ],
        }

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        product_id: int,
        source_version: int = 1,
    ) -> "EmulatedProduct":
        sku = _text(payload.get("sku"), "sku")
        partner_sku = str(payload.get("partnerSKU") or sku).strip()
        raw_categories = payload.get("categories") or ()
        categories = tuple(
            sorted(
                {
                    str(
                        category.get("categoryCode")
                        or category.get("code")
                        or category.get("name")
                    ).strip()
                    if isinstance(category, dict)
                    else str(category).strip()
                    for category in raw_categories
                    if category
                }
            )
        ) or ("GENERAL",)
        raw_units = payload.get("units") or payload.get("productUnits") or ("EACH",)
        units = tuple(
            sorted(
                {
                    str(unit.get("unitCode") or unit.get("code") or unit.get("name")).strip()
                    if isinstance(unit, dict)
                    else str(unit).strip()
                    for unit in raw_units
                    if unit
                }
            )
        ) or (str(payload.get("unitCode") or "EACH"),)

        return cls(
            product_id=product_id,
            sku=sku,
            partner_sku=partner_sku,
            product_name=_text(payload.get("productName"), "productName"),
            asset_type=str(payload.get("assetType") or "Single"),
            has_serial=bool(payload.get("hasSerial", False)),
            has_expiration=bool(payload.get("hasExpiration", False)),
            color=payload.get("color"),
            size=payload.get("size"),
            description=payload.get("description"),
            is_active=bool(payload.get("isActive", True)),
            units=units,
            categories=categories,
            source_version=source_version,
        )

    def with_updates(self, updates: dict[str, Any]) -> "EmulatedProduct":
        merged = {**self.to_vietful_dict(), **updates}
        return self.from_payload(
            merged,
            product_id=self.product_id,
            source_version=self.source_version + 1,
        )


@dataclass(frozen=True, slots=True)
class ProductMutation:
    delivery_id: str
    mutation_type: str
    product: EmulatedProduct

    def webhook_payload(self) -> dict[str, Any]:
        return {
            "id": self.delivery_id,
            "event": "PRODUCT_CHANGED",
            "mutationType": self.mutation_type,
            "product": self.product.to_vietful_dict(),
        }
