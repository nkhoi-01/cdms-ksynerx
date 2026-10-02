"""CDMS ASGI application and process entry point."""

import os

from .api import create_app
from .bootstrap import build_application


application = build_application()
app = create_app(
    application.processor,
    application.query,
    application.poller,
    database_backend=application.database_backend,
    poll_interval_seconds=application.poll_interval_seconds,
)


def main() -> int:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
