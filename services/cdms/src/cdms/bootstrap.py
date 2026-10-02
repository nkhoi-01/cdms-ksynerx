"""Construct concrete adapters and wire the application dependency graph."""

from dataclasses import dataclass
import os

from .adapters.memory import MemoryChangeQuery, MemoryDatabase, MemoryUnitOfWork
from .adapters.postgres import (
    PostgresChangeQuery,
    PostgresUnitOfWork,
    apply_migrations,
    create_connection_factory,
)
from .adapters.vietful import VietfulProductClient
from .polling import PollProducts
from .ports import ChangeQuery
from .process_change import ProcessProductObservation


@dataclass(slots=True)
class Application:
    processor: ProcessProductObservation
    query: ChangeQuery
    poller: PollProducts
    database_backend: str
    poll_interval_seconds: float


def build_application() -> Application:
    database_url = os.getenv("DATABASE_URL", "memory://")
    if database_url == "memory://":
        database = MemoryDatabase()
        unit_of_work = MemoryUnitOfWork(database)
        query: ChangeQuery = MemoryChangeQuery(database)
        database_backend = "memory"
    elif database_url.startswith(("postgresql://", "postgres://")):
        connection_factory = create_connection_factory(database_url)
        apply_migrations(connection_factory)
        unit_of_work = PostgresUnitOfWork(connection_factory)
        query = PostgresChangeQuery(connection_factory)
        database_backend = "postgresql"
    else:
        raise ValueError("DATABASE_URL must be memory:// or a PostgreSQL URL")

    processor = ProcessProductObservation(unit_of_work)
    source = VietfulProductClient(
        os.getenv("INVENTORY_BASE_URL", "http://127.0.0.1:8001")
    )
    return Application(
        processor=processor,
        query=query,
        poller=PollProducts(source, processor),
        database_backend=database_backend,
        poll_interval_seconds=float(os.getenv("POLL_INTERVAL_SECONDS", "0")),
    )
