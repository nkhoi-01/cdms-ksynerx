"""FastAPI handlers for the emulated V1 Products subset."""

from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query, Response, status

from .callbacks import CallbackPublisher
from .domain import EmulatedProduct
from .store import ProductStore


def create_app(store: ProductStore, callbacks: CallbackPublisher) -> FastAPI:
    app = FastAPI(
        title="VietFul Inventory Emulator",
        version="0.1.0",
        description="A deliberately small V1 Products-compatible test service.",
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/Products")
    async def list_products(
        keyword: str | None = Query(None, alias="Keyword"),
        partner_skus: str | None = Query(None, alias="PartnerSKUs"),
        skus: str | None = Query(None, alias="SKUs"),
        page_index: int = Query(1, alias="PageIndex", ge=1),
        page_size: int = Query(100, alias="PageSize", ge=1, le=500),
    ) -> list[dict[str, Any]]:
        products = store.list_page(page_index, page_size)
        partner_filter = set(partner_skus.split(",")) if partner_skus else None
        sku_filter = set(skus.split(",")) if skus else None
        normalized_keyword = keyword.casefold() if keyword else None
        return [
            product.to_vietful_dict()
            for product in products
            if (partner_filter is None or product.partner_sku in partner_filter)
            and (sku_filter is None or product.sku in sku_filter)
            and (
                normalized_keyword is None
                or normalized_keyword in product.sku.casefold()
                or normalized_keyword in product.product_name.casefold()
            )
        ]

    @app.get("/api/v1/Products/{partner_sku}")
    async def get_product(partner_sku: str) -> dict[str, Any]:
        product = store.get(partner_sku)
        if product is None:
            raise HTTPException(status_code=404, detail="product not found")
        return product.to_vietful_dict()

    @app.post("/api/v1/Products")
    async def create_products(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        products: list[EmulatedProduct] = []
        next_id = store.next_product_id()
        try:
            for offset, item in enumerate(payload):
                products.append(
                    EmulatedProduct.from_payload(item, product_id=next_id + offset)
                )
            mutations = store.create(products)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        for mutation in mutations:
            callbacks.publish(mutation)
        return [mutation.product.to_vietful_dict() for mutation in mutations]

    @app.put("/api/v1/Products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def update_product(product_id: int, payload: dict[str, Any]) -> Response:
        current = store.get_by_id(product_id)
        if current is None:
            raise HTTPException(status_code=404, detail="product not found")
        try:
            mutation = store.update(product_id, current.with_updates(payload))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        callbacks.publish(mutation)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/internal/products/{product_id}/mutate")
    async def mutate_product(
        product_id: int,
        updates: dict[str, Any] = Body(default_factory=dict),
        callback_copies: int = Query(1, ge=0, le=10),
    ) -> dict[str, Any]:
        current = store.get_by_id(product_id)
        if current is None:
            raise HTTPException(status_code=404, detail="product not found")
        if not updates:
            updates = {"productName": f"{current.product_name} (updated)"}
        try:
            mutation = store.update(product_id, current.with_updates(updates))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        deliveries = [callbacks.publish(mutation) for _ in range(callback_copies)]
        return {
            "deliveryId": mutation.delivery_id,
            "callbackResults": deliveries,
            "product": mutation.product.to_vietful_dict(),
        }

    return app
