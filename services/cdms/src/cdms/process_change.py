"""Central use case for idempotent product-change processing."""

from .domain import IncomingProductObservation, ProcessingResult, StoredProductCursor
from .normalization import build_change, canonical_content_hash
from .ports import UnitOfWork


class ProcessProductObservation:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def execute(self, observation: IncomingProductObservation) -> ProcessingResult:
        with self._unit_of_work.transaction() as transaction:
            claimed = transaction.claim_delivery(
                observation.ingestion_source,
                observation.delivery_id,
            )
            if not claimed:
                return ProcessingResult(
                    status="duplicate",
                    key=observation.snapshot.key,
                    version=None,
                )

            previous = transaction.lock_cursor(observation.snapshot.key)
            content_hash = canonical_content_hash(observation.snapshot)
            if previous is not None and previous.content_hash == content_hash:
                return ProcessingResult(
                    status="unchanged",
                    key=observation.snapshot.key,
                    version=previous.version,
                )

            change = build_change(previous, observation, content_hash)
            transaction.append_change(change)
            transaction.save_cursor(
                StoredProductCursor(
                    key=change.key,
                    version=change.version,
                    content_hash=change.content_hash,
                    snapshot=change.snapshot,
                )
            )
            return ProcessingResult(
                status="stored",
                key=change.key,
                version=change.version,
                changed_fields=change.changed_fields,
            )

    def process(self, observation: IncomingProductObservation) -> ProcessingResult:
        """Implement the ObservationSink port used by every ingestion adapter."""
        return self.execute(observation)
