"""Canonical CDMS data types with no HTTP or database dependencies."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductKey:
    # TODO: Define the stable, tenant-aware identity of a product.
    pass


@dataclass(frozen=True, slots=True)
class ProductSnapshot:
    # TODO: Define the canonical product and inventory fields CDMS compares.
    pass


@dataclass(frozen=True, slots=True)
class IncomingProductObservation:
    # TODO: Define source, delivery identity, observation time, and snapshot.
    pass


@dataclass(frozen=True, slots=True)
class StoredProductCursor:
    # TODO: Define the latest accepted version, canonical hash, and latest state
    # needed to calculate a minimal field-level change.
    pass


@dataclass(frozen=True, slots=True)
class ProductChange:
    # TODO: Define an accepted create/update/activation/inventory change.
    pass


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    # TODO: Describe whether an observation was stored, unchanged, or duplicate.
    pass
