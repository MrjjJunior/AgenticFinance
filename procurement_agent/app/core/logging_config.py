"""
Logging configuration for the AI Procurement Agent.

Uses structured JSON logging in production (LOG_FORMAT=json) and
human-readable coloured output in development (LOG_FORMAT=text).
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")


class _ISOFormatter(logging.Formatter):
    """Formatter that uses ISO-8601 timestamps."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        return datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()


def setup_logging() -> None:
    """Call once at application startup."""
    fmt = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        if LOG_FORMAT == "text"
        else '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_ISOFormatter(fmt))

    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("xrpl").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
