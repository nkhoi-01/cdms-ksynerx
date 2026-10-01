"""Framework-independent entry points for HTTP adapters."""

from typing import Any

from .domain import ProcessingResult
from .ports import ChangeQuery, ObservationSink, SpreadsheetReader


def receive_webhook(
    payload: dict[str, Any],
    delivery_id: str,
    sink: ObservationSink,
) -> ProcessingResult:
    # TODO: Validate the webhook envelope and normalize its product payload.
    # TODO: Delegate to the same processing use case used by polling and Excel.
    raise NotImplementedError


def upload_spreadsheet(
    content: bytes,
    upload_id: str,
    reader: SpreadsheetReader,
    sink: ObservationSink,
) -> list[ProcessingResult]:
    # TODO: Read rows and derive stable per-row delivery identifiers.
    # TODO: Normalize and process each row without duplicating business logic.
    raise NotImplementedError


def query_product_changes(raw_key: str, query: ChangeQuery) -> list[dict]:
    # TODO: Validate the external key, query ordered changes, and serialize output.
    raise NotImplementedError

