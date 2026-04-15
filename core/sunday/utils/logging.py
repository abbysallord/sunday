"""Structured logging setup for SUNDAY."""

import logging
import sys
from pathlib import Path

import structlog
from rich.console import Console
from rich.logging import RichHandler

from sunday.config.settings import settings


def setup_logging() -> structlog.stdlib.BoundLogger:
    """Configure structured logging with rich console output."""

    # Ensure log directory exists
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Rich console handler (pretty terminal output)
    console = Console(stderr=True)
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )

    # File handler
    file_handler = logging.FileHandler(log_dir / "sunday.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    # Root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        handlers=[rich_handler, file_handler],
    )

    # Silence noisy libraries
    for logger_name in ("httpx", "httpcore", "chromadb", "urllib3"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger("sunday")


log = setup_logging()
