"""SUNDAY entry point."""

import uvicorn

from sunday.api.app import create_app
from sunday.config.settings import settings

app = create_app()


def main():
    """Run the SUNDAY backend server."""
    uvicorn.run(
        "sunday.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
