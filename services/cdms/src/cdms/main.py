"""CDMS process entry point."""

from .bootstrap import build_application


def main() -> int:
    # TODO: Build and start the chosen HTTP server and polling scheduler.
    # TODO: Add graceful shutdown and readiness/liveness handling.
    build_application()
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())

