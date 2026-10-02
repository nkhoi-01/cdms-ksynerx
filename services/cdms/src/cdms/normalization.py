"""Translate input-specific records into deterministic canonical products."""

from collections.abc import Iterable, Mapping
import hashlib
import json
from typing import Any

from .domain import (
    IncomingProductObservation,
    ProductChange,
    ProductKey,
    ProductSnapshot,
    StoredProductCursor,
)


def _required_text(value: Any, field: str) -> str:
    normalized = str(value).strip() if value is not None else ""
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _canonical_items(
    values: Iterable[Any] | None,
    preferred_keys: tuple[str, ...],
) -> tuple[str, ...]:
    normalized: set[str] = set()
    for item in values or ():
        if isinstance(item, Mapping):
            candidate = next(
                (
                    value
                    for key in preferred_keys
                    if (value := _optional_text(item.get(key))) is not None
                ),
                None,
            )
            if candidate is None:
                candidate = json.dumps(
                    dict(item), ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
        else:
            candidate = _optional_text(item)
        if candidate is not None:
            normalized.add(candidate)
    return tuple(sorted(normalized))


def normalize_vietful_product(
    raw: Mapping[str, Any],
    source_system: str = "vietful-emulator",
) -> ProductSnapshot:
    sku = _required_text(raw.get("sku"), "sku")
    partner_sku = _optional_text(raw.get("partnerSKU")) or sku
    product_id = raw.get("productId")
    if product_id is not None:
        product_id = int(product_id)

    return ProductSnapshot(
        key=ProductKey(source_system=source_system, partner_sku=partner_sku),
        product_id=product_id,
        sku=sku,
        product_name=_required_text(raw.get("productName"), "productName"),
        asset_type=_optional_text(raw.get("assetType")) or "Single",
        has_serial=bool(raw.get("hasSerial", False)),
        has_expiration=bool(raw.get("hasExpiration", False)),
        color=_optional_text(raw.get("color")),
        size=_optional_text(raw.get("size")),
        description=_optional_text(raw.get("description")),
        is_active=bool(raw.get("isActive", True)),
        units=_canonical_items(raw.get("units"), ("unitCode", "code", "name")),
        categories=_canonical_items(
            raw.get("categories"),
            (
                "partnerCategoryCode",
                "categoryCode",
                "code",
                "categoryName",
                "name",
                "categoryId",
            ),
        ),
    )


def normalize_excel_product(
    raw: Mapping[str, Any],
    source_system: str = "vietful-emulator",
) -> ProductSnapshot:
    categories = str(raw.get("categories") or "").split(",")
    units = str(raw.get("units") or "").split(",")
    return normalize_vietful_product(
        {**raw, "categories": categories, "units": units},
        source_system=source_system,
    )


def canonical_content_hash(snapshot: ProductSnapshot) -> str:
    encoded = json.dumps(
        snapshot.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_change(
    previous: StoredProductCursor | None,
    observation: IncomingProductObservation,
    content_hash: str,
) -> ProductChange:
    current = observation.snapshot
    current_fields = current.to_dict()
    if previous is None:
        changed_fields = tuple(sorted(current_fields))
        version = 1
        change_type = "created"
    else:
        previous_fields = previous.snapshot.to_dict()
        changed_fields = tuple(
            sorted(
                field
                for field, value in current_fields.items()
                if previous_fields.get(field) != value
            )
        )
        version = previous.version + 1
        change_type = "updated"

    return ProductChange(
        key=current.key,
        version=version,
        change_type=change_type,
        changed_fields=changed_fields,
        content_hash=content_hash,
        snapshot=current,
        ingestion_source=observation.ingestion_source,
        delivery_id=observation.delivery_id,
        observed_at=observation.observed_at,
    )
