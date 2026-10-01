"""Mutable source-of-truth state exposed by the inventory emulator."""

from collections.abc import Iterable

from .domain import EmulatedProduct, ProductMutation


class ProductStore:
    def list_page(self, page_index: int, page_size: int) -> Iterable[EmulatedProduct]:
        # TODO: Return stable ordering and correct pagination behavior.
        raise NotImplementedError

    def get(self, partner_sku: str) -> EmulatedProduct | None:
        # TODO: Look up a product by the V1 path identity.
        raise NotImplementedError

    def create(self, products: Iterable[EmulatedProduct]) -> list[ProductMutation]:
        # TODO: Enforce source-side SKU identity and return resulting mutations.
        raise NotImplementedError

    def update(self, product_id: int, product: EmulatedProduct) -> ProductMutation:
        # TODO: Replace the documented mutable fields and increment source version.
        raise NotImplementedError

