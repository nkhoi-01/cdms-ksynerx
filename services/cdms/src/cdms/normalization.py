"""Translate input-specific records into deterministic canonical products."""

from collections.abc import Mapping
from typing import Any

from .domain import ProductChange, ProductSnapshot, StoredProductCursor


def normalize_vietful_product(raw: Mapping[str, Any]) -> ProductSnapshot:
    # TODO: Map the V1 Product response into the canonical CDMS model.
    raise NotImplementedError


def normalize_excel_product(raw: Mapping[str, Any]) -> ProductSnapshot:
    # TODO: Map one spreadsheet row into the same canonical CDMS model.
    raise NotImplementedError


def canonical_content_hash(snapshot: ProductSnapshot) -> str:
    # TODO: Serialize stable business fields and calculate a deterministic hash.
    raise NotImplementedError


def build_change(
    previous: StoredProductCursor | None,
    current: ProductSnapshot,
) -> ProductChange:
    # TODO: Produce a create or minimal update from the previous/current state.
    raise NotImplementedError

