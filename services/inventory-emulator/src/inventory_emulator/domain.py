"""In-memory/product-state types owned by the emulator service."""

from dataclasses import dataclass


@dataclass(slots=True)
class EmulatedProduct:
    # TODO: Define only fields needed by the supported V1 endpoint subset.
    pass


@dataclass(frozen=True, slots=True)
class ProductMutation:
    # TODO: Define the change information needed to construct a callback.
    pass

