"""kanban-poc/kanban_poc/backend/task_validator.py

Proof-of-concept validation utilities for Kanban task enhancements.

This module is framework-agnostic: you can call these functions from FastAPI,
Flask, Django, or a plain SQLite service.

Validates:
- priority: High/Medium/Low (case-insensitive input accepted, normalized)
- assignee: name (len/trim) + email (RFC-lite)
- due_date: ISO `YYYY-MM-DD` (validated and normalized)

Design goals:
- Explicit, testable functions.
- Strict error messages suitable for returning via API.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date


ALLOWED_PRIORITIES = ("High", "Medium", "Low")

# Pragmatic email regex (intentionally not fully RFC 5322).
_EMAIL_RE = re.compile(
    r"^(?=.{1,254}$)(?=.{1,64}@)[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$"
)


class ValidationError(ValueError):
    """Raised when a field fails validation."""


@dataclass(frozen=True)
class Assignee:
    name: str | None
    email: str | None


def validate_priority(value: str | None) -> str:
    """Validate and normalize priority.

    Args:
        value: Input priority. If None/blank, defaults to "Medium".

    Returns:
        Normalized priority string: one of "High", "Medium", "Low".

    Raises:
        ValidationError: if provided value is not allowed.
    """
    if value is None:
        return "Medium"

    v = value.strip()
    if not v:
        return "Medium"

    # Accept case-insensitive inputs but normalize to canonical casing.
    for allowed in ALLOWED_PRIORITIES:
        if v.lower() == allowed.lower():
            return allowed

    raise ValidationError(
        f"Invalid priority '{value}'. Must be one of: {', '.join(ALLOWED_PRIORITIES)}."
    )


def validate_assignee_name(name: str | None) -> str | None:
    """Validate assignee name.

    Rules (POC):
    - Optional.
    - Trim whitespace.
    - If present, length must be 1..100.
    """
    if name is None:
        return None

    n = name.strip()
    if not n:
        return None

    if len(n) > 100:
        raise ValidationError("Assignee name must be at most 100 characters.")

    return n


def validate_email(email: str | None) -> str | None:
    """Validate assignee email.

    Rules (POC):
    - Optional.
    - Trim whitespace.
    - If present, must match a pragmatic email regex.
    """
    if email is None:
        return None

    e = email.strip()
    if not e:
        return None

    if len(e) > 254:
        raise ValidationError("Email must be at most 254 characters.")

    if not _EMAIL_RE.match(e):
        raise ValidationError("Invalid email format.")

    return e


def validate_due_date(value: str | None) -> str | None:
    """Validate due date in ISO format YYYY-MM-DD.

    Returns normalized ISO string (YYYY-MM-DD) or None.

    Notes:
    - Uses datetime.date.fromisoformat which enforces strict formatting.
    """
    if value is None:
        return None

    v = value.strip()
    if not v:
        return None

    try:
        d = date.fromisoformat(v)
    except ValueError as exc:
        raise ValidationError("Invalid due_date. Expected format YYYY-MM-DD.") from exc

    # Normalize (fromisoformat already parses and we re-render to canonical ISO)
    return d.isoformat()


def validate_task_metadata(
    *,
    priority: str | None = None,
    assignee_name: str | None = None,
    assignee_email: str | None = None,
    due_date: str | None = None,
) -> dict:
    """Validate all task metadata fields and return normalized values."""

    normalized_priority = validate_priority(priority)
    normalized_name = validate_assignee_name(assignee_name)
    normalized_email = validate_email(assignee_email)
    normalized_due_date = validate_due_date(due_date)

    return {
        "priority": normalized_priority,
        "assignee_name": normalized_name,
        "assignee_email": normalized_email,
        "due_date": normalized_due_date,
    }
