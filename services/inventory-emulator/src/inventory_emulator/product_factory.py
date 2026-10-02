"""Deterministic Faker-backed inventory product generation."""

from faker import Faker

from .domain import EmulatedProduct


class ProductFactory:
    def __init__(self, seed: int, locale: str = "vi_VN") -> None:
        self._seed = seed
        self._locale = locale

    def build(self, product_number: int) -> EmulatedProduct:
        if product_number < 1:
            raise ValueError("product_number must be at least 1")
        fake = Faker(self._locale)
        fake.seed_instance(self._seed * 1_000_003 + product_number)
        category = fake.random_element(("ELECTRONICS", "HOME", "OFFICE"))
        color = fake.safe_color_name().title()
        product_word = fake.word().title()

        return EmulatedProduct(
            product_id=product_number,
            sku=f"SKU-{product_number:05d}",
            partner_sku=f"PARTNER-{product_number:05d}",
            product_name=f"{product_word} {product_number}",
            color=color,
            description=fake.sentence(nb_words=8),
            units=("EACH",),
            categories=(str(category),),
        )

    def build_many(self, count: int) -> list[EmulatedProduct]:
        if count < 0:
            raise ValueError("count cannot be negative")
        return [self.build(number) for number in range(1, count + 1)]
