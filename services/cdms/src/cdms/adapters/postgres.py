"""PostgreSQL implementation of transactions, commands, and change queries."""


class PostgresUnitOfWork:
    def __init__(self, connection_factory) -> None:
        # TODO: Store a connection factory rather than one global connection.
        raise NotImplementedError

    def transaction(self):
        # TODO: Open a transaction and expose a ChangeTransaction implementation.
        # TODO: Roll back on exceptions and commit only complete change processing.
        raise NotImplementedError


class PostgresChangeQuery:
    def __init__(self, connection_factory) -> None:
        # TODO: Store the query dependency.
        raise NotImplementedError

    def list_changes(self, key):
        # TODO: Query changes by entity key in deterministic version order.
        raise NotImplementedError
