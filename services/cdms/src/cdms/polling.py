"""Scheduled ingestion orchestration for VietFul-compatible product pages."""

from .ports import ObservationSink, ProductSource


class PollProducts:
    def __init__(self, source: ProductSource, sink: ObservationSink) -> None:
        # TODO: Store source and processing dependencies.
        raise NotImplementedError

    def run_once(self) -> None:
        # TODO: Iterate every page and normalize each source record.
        # TODO: Construct a stable delivery identity for each polling observation.
        # TODO: Send every observation through the central processing use case.
        # TODO: Persist/checkpoint paging progress only after successful processing.
        raise NotImplementedError

