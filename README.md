# Change Data Management Service

A Junior-level Python prototype that captures distinct product changes from a
VietFul-compatible inventory service through polling and webhook callbacks.

## Status

The core vertical slice is working:

- deterministic Faker inventory data;
- a limited VietFul V1 Products-compatible emulator;
- manual and configurable scheduled polling;
- product webhook ingestion;
- deterministic normalization and SHA-256 content hashing;
- idempotent delivery receipts;
- ordered product change history;
- PostgreSQL transactions, constraints, and per-product locking;
- an in-memory mode for quick demonstrations;
- unit, HTTP, rollback, concurrency, and PostgreSQL integration tests;
- single-machine Docker Compose definitions.

Excel ingestion is deliberately deferred. The Compose file parses, but its
image build has not been executed in the implementation environment because
Docker is unavailable there. Run the Docker quickstart before presenting.

## Problem

The service observes product data repeatedly. It must store a new version only
when business content changes and must remain correct when a delivery is
retried or concurrent workers receive it together.

"Exactly once" is implemented as **effectively-once database effects**, not as
an assumption of exactly-once networking:

1. a stable source delivery ID is claimed in `ingestion_receipts`;
2. the product is locked for the transaction;
3. canonical content is hashed and compared with the latest cursor;
4. only changed content is appended to `product_changes`;
5. the receipt, change, and cursor commit or roll back together.

The outcomes are intentionally distinct:

- `stored`: a new business version was appended;
- `unchanged`: a new delivery contained the current business state;
- `duplicate`: the same delivery ID was already processed.

## Architecture

```mermaid
flowchart LR
    EMULATOR[VietFul inventory emulator]
    POLL[Scheduled/manual polling]
    CALLBACK[Webhook callback]

    EMULATOR --> POLL
    EMULATOR --> CALLBACK
    POLL --> NORMALIZE[Canonical normalization]
    CALLBACK --> NORMALIZE
    NORMALIZE --> PROCESS[ProcessProductObservation]
    PROCESS -->|single transaction| RECEIPTS[(Delivery receipts)]
    PROCESS -->|append distinct versions| CHANGES[(Product changes)]
    PROCESS -->|latest hash/version| CURSORS[(Product cursors)]
    RECEIPTS --- POSTGRES[(PostgreSQL)]
    CHANGES --- POSTGRES
    CURSORS --- POSTGRES
```

Both ingestion paths call the same
[`ProcessProductObservation`](services/cdms/src/cdms/process_change.py) use
case. Transport adapters do not implement their own deduplication rules.

## Technology

| Component | Choice |
| --- | --- |
| Backend | Python 3.14, FastAPI, Uvicorn |
| Database | PostgreSQL 17 container, Psycopg 3 |
| Emulator data | Faker with a pinned version and isolated seeds |
| HTTP client/testing | HTTPX |
| Deployment | Docker Compose on one machine |
| Tests | Python `unittest` |

No Node.js application is required for this backend-only MVP.

## Repository layout

```text
compose.yaml
services/
├── cdms/
│   ├── Dockerfile
│   ├── migrations/001_initial.sql
│   ├── requirements.txt
│   ├── src/cdms/
│   │   ├── domain.py
│   │   ├── normalization.py
│   │   ├── process_change.py
│   │   ├── polling.py
│   │   ├── api.py
│   │   └── adapters/
│   └── tests/
└── inventory-emulator/
    ├── Dockerfile
    ├── requirements.txt
    ├── src/inventory_emulator/
    └── tests/
```

## Quickstart with PostgreSQL

Requirements: Docker Engine or Docker Desktop, Docker Compose v2, and `curl`.

```bash
git clone https://github.com/nkhoi-01/cdms-ksynerx.git
cd cdms-ksynerx
cp .env.example .env
```

Replace the demo password in `.env`, then start the stack:

```bash
docker compose up --build -d
docker compose ps
```

Health checks:

```bash
curl -sS http://127.0.0.1:8001/health
curl -sS http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
{"status":"ok","database":"postgresql"}
```

API documentation is available at:

- <http://127.0.0.1:8001/docs> for the inventory emulator;
- <http://127.0.0.1:8000/docs> for CDMS.

## Demonstration

Start from an empty database if exact counts matter. `docker compose down -v`
removes the local database volume and must not be used on valuable data.

First poll:

```bash
curl -sS -X POST http://127.0.0.1:8000/internal/poll
```

```json
{"processed":3,"stored":3,"unchanged":0,"duplicate":0}
```

Repeat the poll:

```json
{"processed":3,"stored":0,"unchanged":0,"duplicate":3}
```

Change product 1 and deliberately deliver its callback twice:

```bash
curl -sS -X POST \
  'http://127.0.0.1:8001/internal/products/1/mutate?callback_copies=2' \
  -H 'content-type: application/json' \
  --data-binary '{"productName":"Callback Demo Product"}'
```

The response contains one stable delivery ID and two successful callback
attempts:

```json
{"deliveryId":"emulator:1:2:updated","callbackResults":[true,true]}
```

Query the change history:

```bash
curl -sS http://127.0.0.1:8000/products/PARTNER-00001/changes
```

The result contains version 1 from polling and exactly one version 2 from the
webhook. Version 2 reports `changedFields: ["productName"]`; the repeated
callback creates no version 3.

A later poll reports one `unchanged` product and two duplicate poll deliveries:

```json
{"processed":3,"stored":0,"unchanged":1,"duplicate":2}
```

## Tests

Create host environments and install the pinned dependencies:

```bash
python3 -m venv services/cdms/.venv
python3 -m venv services/inventory-emulator/.venv
services/cdms/.venv/bin/python -m pip install -r services/cdms/requirements.txt
services/inventory-emulator/.venv/bin/python -m pip install \
  -r services/inventory-emulator/requirements.txt
```

Run CDMS tests:

```bash
PYTHONPATH=services/cdms/src \
  services/cdms/.venv/bin/python -m unittest discover \
  -s services/cdms/tests -p 'test_*.py' -v
```

Run emulator tests:

```bash
PYTHONPATH=services/inventory-emulator/src \
  services/inventory-emulator/.venv/bin/python -m unittest discover \
  -s services/inventory-emulator/tests -p 'test_*.py' -v
```

PostgreSQL tests run when `TEST_DATABASE_URL` points to a dedicated test
database. They truncate CDMS tables, so do not point them at valuable data.

```bash
TEST_DATABASE_URL='postgresql://cdms:password@127.0.0.1:5432/cdms_test' \
PYTHONPATH=services/cdms/src \
  services/cdms/.venv/bin/python -m unittest discover \
  -s services/cdms/tests -p 'test_*.py' -v
```

Verified results:

- 17 CDMS tests passed with PostgreSQL enabled;
- 9 emulator tests passed;
- 50 concurrent in-memory duplicate submissions produced one change;
- 20 concurrent PostgreSQL duplicate submissions produced one change;
- a simulated write failure rolled back its delivery receipt and was retryable;
- real localhost HTTP produced the demonstration outputs above.

## API summary

| Service | Method and path | Purpose |
| --- | --- | --- |
| Emulator | `GET /api/v1/Products` | Paginated product list |
| Emulator | `GET /api/v1/Products/{partnerSKU}` | Product detail |
| Emulator | `POST /api/v1/Products` | Create products |
| Emulator | `PUT /api/v1/Products/{id}` | Update a product |
| Emulator | `POST /internal/products/{id}/mutate` | Controlled demo mutation/callback duplication |
| CDMS | `POST /internal/poll` | Run one polling cycle |
| CDMS | `POST /webhooks/products` | Receive a product observation |
| CDMS | `GET /products/{partnerSKU}/changes` | Query ordered changes |

## Trade-offs and unfinished work

- Excel upload is not implemented.
- The emulator implements only the V1 Products subset needed by the demo.
- Webhook HMAC verification and authentication are not implemented.
- Polling uses a stable content-derived delivery ID rather than a persisted
  source paging checkpoint.
- The API performs synchronous database work inside handlers; a production
  version would use a worker model or async database boundary under heavy load.
- Load coverage is a bounded concurrency spike, not a sustained benchmark.
- Structured logs, metrics, tracing, and an external retry queue are deferred.
- The container definitions still need execution on a Docker-capable machine.

These omissions keep the submission focused on a coherent, tested Junior-level
vertical slice rather than a broad collection of unfinished endpoints.

## Lessons learned

- Product identity and delivery identity solve different problems.
- Duplicate delivery and unchanged business content are different outcomes.
- Stable normalization is required before content hashing.
- A database constraint and one transaction are stronger guarantees than an
  in-process set or Faker's uniqueness helper.
- An advisory transaction lock protects the first concurrent update even when
  a product cursor row does not exist yet.
- A small, demonstrable failure-safe path is more valuable than untested scope.

## AI assistance disclosure

AI tools were used for requirement analysis, documentation extraction,
architecture discussion, initial scaffolding, implementation assistance, test
construction, debugger configuration, and README drafting. The candidate is
responsible for reviewing, running, understanding, and explaining all submitted
code and for identifying any later candidate-authored changes during the
presentation.

## References

- [VietFul API documentation](https://ext.stg.vnfai.com/doc/index.html)
- [VietFul V1 Products](https://ext.stg.vnfai.com/doc/index.html#tag/Products)
- [Faker documentation](https://faker.readthedocs.io/en/master/)
- [PostgreSQL documentation](https://www.postgresql.org/docs/current/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
