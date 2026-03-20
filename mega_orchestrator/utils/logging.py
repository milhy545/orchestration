import logging
import os
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> None:
    """
    Configure standard logging for MCP services.
    """
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(level=level, format=format, handlers=handlers)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with the specified name.
    """
    return logging.getLogger(name)
