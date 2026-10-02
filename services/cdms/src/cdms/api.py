"""HTTP API and framework-independent ingestion functions."""

import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query

from .domain import IncomingProductObservation, ProcessingResult, ProductKey
from .normalization import normalize_vietful_product
from .polling import PollProducts
from .ports import ChangeQuery, ObservationSink


def receive_webhook(
    payload: dict[str, Any],
    delivery_id: str,
    sink: ObservationSink,
) -> ProcessingResult:
    raw_product = payload.get("product")
    if not isinstance(raw_product, dict):
        raise ValueError("webhook payload must contain a product object")
    snapshot = normalize_vietful_product(raw_product)
    return sink.process(
        IncomingProductObservation(
            ingestion_source="webhook",
            delivery_id=delivery_id,
            observed_at=datetime.now(UTC),
            snapshot=snapshot,
        )
    )


def query_product_changes(
    partner_sku: str,
    query: ChangeQuery,
    source_system: str = "vietful-emulator",
) -> list[dict[str, Any]]:
    key = ProductKey(source_system=source_system, partner_sku=partner_sku)
    return [change.to_dict() for change in query.list_changes(key)]


def create_app(
    sink: ObservationSink,
    query: ChangeQuery,
    poller: PollProducts,
    *,
    database_backend: str,
    poll_interval_seconds: float = 0,
) -> FastAPI:
    async def scheduled_polling() -> None:
        while True:
            await asyncio.sleep(poll_interval_seconds)
            try:
                await asyncio.to_thread(poller.run_once)
            except Exception:
                # A scheduled failure must not kill the API process. Production
                # code would also emit structured logs and metrics here.
                continue

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        task = None
        if poll_interval_seconds > 0:
            task = asyncio.create_task(scheduled_polling())
        try:
            yield
        finally:
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    app = FastAPI(
        title="Change Data Management Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "database": database_backend}

    @app.post("/internal/poll")
    async def poll_products() -> dict[str, int]:
        try:
            report = poller.run_once()
        except (httpx.HTTPError, ValueError) as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        return report.to_dict()

    @app.post("/webhooks/products")
    async def product_webhook(payload: dict[str, Any]) -> dict[str, Any]:
        delivery_id = str(payload.get("id") or "").strip()
        if not delivery_id:
            raise HTTPException(status_code=400, detail="webhook id is required")
        try:
            result = receive_webhook(payload, delivery_id, sink)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return result.to_dict()

    @app.get("/products/{partner_sku}/changes")
    async def product_changes(
        partner_sku: str,
        source_system: str = Query("vietful-emulator", alias="sourceSystem"),
    ) -> list[dict[str, Any]]:
        return query_product_changes(partner_sku, query, source_system)

    return app
