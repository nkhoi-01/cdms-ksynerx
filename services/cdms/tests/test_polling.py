import unittest

import httpx

from cdms.adapters.memory import MemoryDatabase, MemoryUnitOfWork
from cdms.adapters.vietful import VietfulProductClient
from cdms.polling import PollProducts
from cdms.process_change import ProcessProductObservation


def product(name: str = "Demo Product") -> dict:
    return {
        "productId": 1,
        "sku": "SKU-001",
        "partnerSKU": "PARTNER-001",
        "productName": name,
        "units": ["EACH"],
        "categories": [],
    }


class MutableSource:
    def __init__(self) -> None:
        self.product = product()

    def iter_product_pages(self):
        yield [self.product]


class PollingTests(unittest.TestCase):
    def test_repeated_poll_does_not_store_duplicate_and_change_creates_version(self) -> None:
        database = MemoryDatabase()
        processor = ProcessProductObservation(MemoryUnitOfWork(database))
        source = MutableSource()
        poller = PollProducts(source, processor)

        first = poller.run_once()
        second = poller.run_once()
        source.product = product("Renamed Product")
        third = poller.run_once()

        self.assertEqual({"processed": 1, "stored": 1, "unchanged": 0, "duplicate": 0}, first.to_dict())
        self.assertEqual({"processed": 1, "stored": 0, "unchanged": 0, "duplicate": 1}, second.to_dict())
        self.assertEqual({"processed": 1, "stored": 1, "unchanged": 0, "duplicate": 0}, third.to_dict())
        self.assertEqual([1, 2], [change.version for change in database.changes])

    def test_vietful_client_consumes_all_pages(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            page = int(request.url.params["PageIndex"])
            if page == 1:
                return httpx.Response(200, json=[product(), {**product(), "productId": 2}])
            return httpx.Response(200, json=[])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        source = VietfulProductClient(
            "http://inventory.test",
            client=client,
            page_size=2,
        )

        pages = list(source.iter_product_pages())

        self.assertEqual(1, len(pages))
        self.assertEqual(2, len(pages[0]))


if __name__ == "__main__":
    unittest.main()
