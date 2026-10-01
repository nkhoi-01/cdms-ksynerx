"""Framework-independent handlers for the emulated V1 Products subset."""

from typing import Any


def list_products(query: dict[str, Any], store) -> dict[str, Any]:
    # TODO: Implement GET /api/v1/Products filtering and pagination semantics.
    raise NotImplementedError


def get_product(partner_sku: str, store) -> dict[str, Any]:
    # TODO: Implement GET /api/v1/Products/{partnerSKU} and not-found behavior.
    raise NotImplementedError


def create_products(payload: list[dict[str, Any]], store, callbacks) -> list[dict]:
    # TODO: Validate the documented array request and persist new products.
    # TODO: Publish a callback only after source mutation succeeds.
    raise NotImplementedError


def update_product(product_id: int, payload: dict[str, Any], store, callbacks) -> None:
    # TODO: Validate a full Product update and publish the resulting mutation.
    raise NotImplementedError

