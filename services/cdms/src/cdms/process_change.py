"""Central use case for idempotent product-change processing."""

from .domain import IncomingProductObservation, ProcessingResult
from .ports import UnitOfWork


class ProcessProductObservation:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        # TODO: Store only dependencies required by the business use case.
        raise NotImplementedError

    def execute(self, observation: IncomingProductObservation) -> ProcessingResult:
        # TODO: Start one database transaction.
        # TODO: Claim the source delivery and stop if it is a retry.
        # TODO: Lock the product cursor to serialize concurrent changes.
        # TODO: Hash canonical business data and stop if it is unchanged.
        # TODO: Build and append exactly one ordered ProductChange.
        # TODO: Update the cursor in the same transaction.
        # TODO: Return an explainable processing result.
        raise NotImplementedError

