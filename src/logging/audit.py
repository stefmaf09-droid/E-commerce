"""
Structured audit logging for sensitive actions.

Implements docs/ROADMAP.md priorite haute item 4 ("Audit & logging - actions
sensibles"): every sensitive event is written as a single JSON line, so logs
stay grep-able and easy to ship to a log aggregator later.

Usage
-----
    from src.logging.audit import log_event, log_user_created

    log_event("user_login", user_email="client@example.com", success=True)

    # or one of the convenience wrappers for the events called out in the
    # roadmap's acceptance criteria:
    log_user_created(user_email="client@example.com", platform="shopify")
    log_user_login(user_email="client@example.com", success=True)
    log_stripe_activation(user_email="client@example.com", stripe_account_id="acct_123")
    log_ticket_fallback_created(user_email="client@example.com", reason="3 echecs consecutifs")

Each call appends one JSON object per line to ``logs/audit.log`` (created on
first use; the ``logs/`` directory is already gitignored) and also emits it
through the standard ``logging`` module under the ``audit`` logger name, so
it shows up alongside the rest of the application logs too.

Example line written to logs/audit.log
---------------------------------------
    {"timestamp": "2026-08-11T14:32:07.512931+00:00", "event": "user_login",
     "user_email": "client@example.com", "success": true}
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
_LOG_PATH = os.path.join(_LOG_DIR, "audit.log")

_audit_logger = logging.getLogger("audit")
_audit_logger.setLevel(logging.INFO)
_audit_logger.propagate = False  # keep audit records out of the general app log stream

if not any(isinstance(h, logging.FileHandler) and getattr(h, "_is_audit_handler", False)
           for h in _audit_logger.handlers):
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        _handler = logging.FileHandler(_LOG_PATH, encoding="utf-8")
        _handler._is_audit_handler = True  # marker to avoid double-attaching on reimport
        _handler.setFormatter(logging.Formatter("%(message)s"))
        _audit_logger.addHandler(_handler)
    except OSError:
        # If the filesystem is read-only (some deployment targets) fall back
        # to stdout only, via the standard "audit" logger's default handlers.
        logging.getLogger(__name__).warning(
            "Could not open %s for writing; audit events will only go to stdout.", _LOG_PATH
        )


def log_event(event: str, **details: Any) -> Dict[str, Any]:
    """
    Record a structured audit event as a single JSON line.

    Args:
        event: short event name, e.g. "user_login", "stripe_activation".
        **details: any JSON-serializable extra fields (user_email, ip, etc).
                    Non-serializable values are coerced to str() so a bad
                    field never breaks the calling code path.

    Returns:
        The dict that was logged, in case the caller wants to inspect it.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
    }
    for key, value in details.items():
        try:
            json.dumps(value)
            record[key] = value
        except TypeError:
            record[key] = str(value)

    try:
        _audit_logger.info(json.dumps(record, ensure_ascii=False))
    except Exception:
        # Audit logging must never crash the calling feature.
        logging.getLogger(__name__).exception("Failed to write audit event %r", event)

    return record


def log_user_created(user_email: str, platform: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
    """Audit event: a new client account was created."""
    return log_event("user_created", user_email=user_email, platform=platform, **extra)


def log_user_login(user_email: str, success: bool = True, **extra: Any) -> Dict[str, Any]:
    """Audit event: a login attempt (successful or not)."""
    return log_event("user_login", user_email=user_email, success=success, **extra)


def log_stripe_activation(user_email: str, stripe_account_id: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
    """Audit event: a client's Stripe Connect account was activated."""
    return log_event(
        "stripe_activation", user_email=user_email, stripe_account_id=stripe_account_id, **extra
    )


def log_ticket_fallback_created(user_email: str, reason: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
    """Audit event: a manual support ticket was auto-created after repeated failures."""
    return log_event("ticket_fallback_created", user_email=user_email, reason=reason, **extra)
