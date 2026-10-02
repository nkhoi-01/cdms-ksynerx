"""Scheduled ingestion orchestration for VietFul-compatible product pages."""

from dataclasses import dataclass
from datetime import UTC, datetime

from .domain import IncomingProductObservation
from .normalization import canonical_content_hash, normalize_vietful_product
from .ports import ObservationSink, ProductSource


@dataclass(frozen=True, slots=True)
class PollReport:
    processed: int
    stored: int
    unchanged: int
    duplicate: int

    def to_dict(self) -> dict[str, int]:
        return {
            "processed": self.processed,
            "stored": self.stored,
            "unchanged": self.unchanged,
            "duplicate": self.duplicate,
        }


class PollProducts:
    def __init__(self, source: ProductSource, sink: ObservationSink) -> None:
        self._source = source
        self._sink = sink

    def run_once(self) -> PollReport:
        counts = {"processed": 0, "stored": 0, "unchanged": 0, "duplicate": 0}
        for page in self._source.iter_product_pages():
            for raw_product in page:
                snapshot = normalize_vietful_product(raw_product)
                content_hash = canonical_content_hash(snapshot)
                result = self._sink.process(
                    IncomingProductObservation(
                        ingestion_source="polling",
                        delivery_id=(
                            f"poll:{snapshot.key.source_system}:"
                            f"{snapshot.key.partner_sku}:{content_hash}"
                        ),
                        observed_at=datetime.now(UTC),
                        snapshot=snapshot,
                    )
                )
                counts["processed"] += 1
                counts[result.status] += 1
        return PollReport(**counts)
