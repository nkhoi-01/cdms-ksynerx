"""Canonical CDMS data types with no HTTP or database dependencies."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class ProductKey:
    source_system: str
    partner_sku: str

    def __post_init__(self) -> None:
        if not self.source_system.strip():
            raise ValueError("source_system is required")
        if not self.partner_sku.strip():
            raise ValueError("partner_sku is required")

    def to_dict(self) -> dict[str, str]:
        return {
            "sourceSystem": self.source_system,
            "partnerSKU": self.partner_sku,
        }


@dataclass(frozen=True, slots=True)
class ProductSnapshot:
    key: ProductKey
    product_id: int | None
    sku: str
    product_name: str
    asset_type: str
    has_serial: bool
    has_expiration: bool
    color: str | None
    size: str | None
    description: str | None
    is_active: bool
    units: tuple[str, ...]
    categories: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.key.to_dict(),
            "productId": self.product_id,
            "sku": self.sku,
            "productName": self.product_name,
            "assetType": self.asset_type,
            "hasSerial": self.has_serial,
            "hasExpiration": self.has_expiration,
            "color": self.color,
            "size": self.size,
            "description": self.description,
            "isActive": self.is_active,
            "units": list(self.units),
            "categories": list(self.categories),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ProductSnapshot":
        return cls(
            key=ProductKey(
                source_system=value["sourceSystem"],
                partner_sku=value["partnerSKU"],
            ),
            product_id=value.get("productId"),
            sku=value["sku"],
            product_name=value["productName"],
            asset_type=value["assetType"],
            has_serial=value["hasSerial"],
            has_expiration=value["hasExpiration"],
            color=value.get("color"),
            size=value.get("size"),
            description=value.get("description"),
            is_active=value["isActive"],
            units=tuple(value.get("units", ())),
            categories=tuple(value.get("categories", ())),
        )


@dataclass(frozen=True, slots=True)
class IncomingProductObservation:
    ingestion_source: str
    delivery_id: str
    observed_at: datetime
    snapshot: ProductSnapshot

    def __post_init__(self) -> None:
        if not self.ingestion_source.strip():
            raise ValueError("ingestion_source is required")
        if not self.delivery_id.strip():
            raise ValueError("delivery_id is required")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class StoredProductCursor:
    key: ProductKey
    version: int
    content_hash: str
    snapshot: ProductSnapshot


@dataclass(frozen=True, slots=True)
class ProductChange:
    key: ProductKey
    version: int
    change_type: Literal["created", "updated"]
    changed_fields: tuple[str, ...]
    content_hash: str
    snapshot: ProductSnapshot
    ingestion_source: str
    delivery_id: str
    observed_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.key.to_dict(),
            "version": self.version,
            "changeType": self.change_type,
            "changedFields": list(self.changed_fields),
            "contentHash": self.content_hash,
            "snapshot": self.snapshot.to_dict(),
            "ingestionSource": self.ingestion_source,
            "deliveryId": self.delivery_id,
            "observedAt": self.observed_at.isoformat(),
        }


ProcessingStatus = Literal["stored", "unchanged", "duplicate"]


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    status: ProcessingStatus
    key: ProductKey
    version: int | None
    changed_fields: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            **self.key.to_dict(),
            "version": self.version,
            "changedFields": list(self.changed_fields),
        }
