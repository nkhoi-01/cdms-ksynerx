"""Mutable source-of-truth state exposed by the inventory emulator."""

from collections.abc import Iterable
from threading import RLock

from .domain import EmulatedProduct, ProductMutation


class ProductStore:
    def __init__(self, products: Iterable[EmulatedProduct] = ()) -> None:
        self._lock = RLock()
        self._products: dict[int, EmulatedProduct] = {}
        for product in products:
            self._insert(product)

    def _insert(self, product: EmulatedProduct) -> None:
        if product.product_id in self._products:
            raise ValueError(f"product id already exists: {product.product_id}")
        if any(item.partner_sku == product.partner_sku for item in self._products.values()):
            raise ValueError(f"partner SKU already exists: {product.partner_sku}")
        self._products[product.product_id] = product

    def list_page(self, page_index: int, page_size: int) -> list[EmulatedProduct]:
        if page_index < 1 or page_size < 1:
            raise ValueError("page_index and page_size must be positive")
        with self._lock:
            ordered = sorted(self._products.values(), key=lambda item: item.product_id)
            start = (page_index - 1) * page_size
            return ordered[start : start + page_size]

    def get(self, partner_sku: str) -> EmulatedProduct | None:
        with self._lock:
            return next(
                (item for item in self._products.values() if item.partner_sku == partner_sku),
                None,
            )

    def get_by_id(self, product_id: int) -> EmulatedProduct | None:
        with self._lock:
            return self._products.get(product_id)

    def create(self, products: Iterable[EmulatedProduct]) -> list[ProductMutation]:
        with self._lock:
            incoming = list(products)
            incoming_ids = [product.product_id for product in incoming]
            incoming_skus = [product.partner_sku for product in incoming]
            if len(incoming_ids) != len(set(incoming_ids)):
                raise ValueError("request contains duplicate product ids")
            if len(incoming_skus) != len(set(incoming_skus)):
                raise ValueError("request contains duplicate partner SKUs")
            existing_skus = {item.partner_sku for item in self._products.values()}
            if any(product_id in self._products for product_id in incoming_ids):
                raise ValueError("product id already exists")
            if existing_skus.intersection(incoming_skus):
                raise ValueError("partner SKU already exists")

            mutations: list[ProductMutation] = []
            for product in incoming:
                self._insert(product)
                mutations.append(self._mutation("created", product))
            return mutations

    def next_product_id(self) -> int:
        with self._lock:
            return max(self._products, default=0) + 1

    def update(self, product_id: int, product: EmulatedProduct) -> ProductMutation:
        with self._lock:
            if product_id not in self._products:
                raise KeyError(product_id)
            duplicate = next(
                (
                    item
                    for item in self._products.values()
                    if item.partner_sku == product.partner_sku and item.product_id != product_id
                ),
                None,
            )
            if duplicate is not None:
                raise ValueError(f"partner SKU already exists: {product.partner_sku}")
            self._products[product_id] = product
            return self._mutation("updated", product)

    @staticmethod
    def _mutation(mutation_type: str, product: EmulatedProduct) -> ProductMutation:
        return ProductMutation(
            delivery_id=(
                f"emulator:{product.product_id}:{product.source_version}:{mutation_type}"
            ),
            mutation_type=mutation_type,
            product=product,
        )
