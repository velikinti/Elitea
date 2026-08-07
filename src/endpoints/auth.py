from __future__ import annotations

from fastapi import Header, HTTPException, status

from settings import settings


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """Require API key auth for protected endpoints.

    Policy:
    - If QA_API_KEY is not configured:
        - fail closed in production (503)
        - allow open in non-prod (dev/test/demo)
    - If configured, require exact match in X-API-Key header.
    """

    # Fail-closed in prod if misconfigured
    if not getattr(settings, "api_key", None):
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API key auth not configured",
            )
        return

    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
        )
