"""Structured logging for the VS Code engineering crew."""

from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure a single stream handler and return the package logger."""
    logger = logging.getLogger("engineering_team.vscode_optimized")
    logger.setLevel(level)
    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        logger.addHandler(handler)
    logger.propagate = False
    return logger
