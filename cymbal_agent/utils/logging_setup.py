"""
Centralized Cloud Logging setup.

- Uses CloudLoggingHandler (background thread) so logging does not add latency
  to your request path.
- Keeps the JSON shape you’ve been using:
  jsonPayload.message + jsonPayload.custom{...}
"""

import logging
from typing import Optional, Dict

import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler


def _setup_logger() -> logging.Logger:
    """Create or return the singleton evaluation logger."""
    log_name = "agent-evaluation-logs"
    logger = logging.getLogger(log_name)
    if any(isinstance(h, CloudLoggingHandler) for h in logger.handlers):
        return logger

    try:
        client = google.cloud.logging.Client(project="YOUR_PROJECT_ID")
        handler = CloudLoggingHandler(client, name=log_name)  # async transport
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    except Exception as e:
        # Fallback to console if Cloud Logging is unavailable (local dev)
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(log_name)
        logger.warning("Cloud Logging setup failed; using console. Error: %s", e)

    return logger


_eval_log = _setup_logger()


def log_structured_entry(message: str, severity: str, custom_log: Optional[Dict] = None) -> None:
    """
    Emit a JSON-structured log row compatible with your existing queries.

    Args:
        message: Short label for the row (e.g., "Final agent turn").
        severity: "INFO" | "WARNING" | "ERROR" etc.
        custom_log: A dict with your structured payload (invocation_id, request, response, usage, tags…).

    Resulting shape in Cloud Logging:
        jsonPayload.message = <message>
        jsonPayload.custom  = <custom_log>
    """
    level = getattr(logging, severity.upper(), logging.INFO)
    _eval_log.log(level, message, extra={"json_fields": {"message": message, "custom": custom_log or {}}}) #