"""Simple API key authentication for Architecture Council."""

import os
import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_EXPECTED_KEY = os.getenv("ARCHITECT_API_KEY", "")


def verify_api_key(api_key: str = Security(_API_KEY_HEADER)) -> str:
    """FastAPI dependency — validates X-API-Key header."""
    if not _EXPECTED_KEY:
        # No key configured — allow all (dev mode)
        return "dev"
    if not api_key or not secrets.compare_digest(api_key, _EXPECTED_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key
