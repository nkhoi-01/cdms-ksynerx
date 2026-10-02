"""Inventory emulator process entry point."""

import os

from .api import create_app
from .callbacks import CallbackPublisher
from .product_factory import ProductFactory
from .store import ProductStore


def build_app():
    seed = int(os.getenv("EMULATOR_SEED", "2604"))
    product_count = int(os.getenv("EMULATOR_PRODUCT_COUNT", "3"))
    callback_url = os.getenv("CDMS_WEBHOOK_URL")
    store = ProductStore(ProductFactory(seed).build_many(product_count))
    return create_app(store, CallbackPublisher(callback_url))


app = build_app()


def main() -> int:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
