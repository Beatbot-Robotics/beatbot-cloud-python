"""Tests for Beatbot authentication helpers."""

import base64
import json

import pytest

from beatbot_cloud import decode_access_token


def test_decode_access_token() -> None:
    """Decode valid JWT claims."""
    payload = (
        base64.urlsafe_b64encode(json.dumps({"sub": "user-1", "region": "eu"}).encode())
        .decode()
        .rstrip("=")
    )

    assert decode_access_token(f"header.{payload}.signature") == {
        "sub": "user-1",
        "region": "eu",
    }


@pytest.mark.parametrize("token", ["", "invalid", "a.!.c", "a.W10.c"])
def test_decode_access_token_rejects_invalid_claims(token: str) -> None:
    """Reject malformed tokens and non-object claims."""
    assert decode_access_token(token) is None
