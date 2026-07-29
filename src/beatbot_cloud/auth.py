"""Authentication helpers for Beatbot cloud tokens."""

import base64
import binascii
import json
from typing import Any


def decode_access_token(access_token: str) -> dict[str, Any] | None:
    """Decode the claims from a JWT access token without verifying its signature."""
    try:
        payload = access_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
    except (
        binascii.Error,
        IndexError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValueError,
    ):
        return None
    return claims if isinstance(claims, dict) else None
