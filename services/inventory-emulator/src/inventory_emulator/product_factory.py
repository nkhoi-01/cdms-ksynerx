"""Deterministic Faker-backed inventory product generation."""

from .domain import EmulatedProduct


class ProductFactory:
    def __init__(self, seed: int) -> None:
        # TODO: Construct and seed an isolated Faker instance.
        raise NotImplementedError

    def build(self, product_number: int) -> EmulatedProduct:
        # TODO: Build a reproducible V1-compatible product with a stable SKU.
        # TODO: Keep identity deterministic instead of relying on fake.unique.
        raise NotImplementedError

    def build_many(self, count: int) -> list[EmulatedProduct]:
        # TODO: Generate a requested dataset without hidden global random state.
        raise NotImplementedError

