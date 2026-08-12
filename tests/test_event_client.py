"""Tests for the resilient Beatbot event client."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from beatbot_cloud import (
    BeatbotAuthenticationError,
    BeatbotConnectionError,
    BeatbotConnectionReplacedError,
    BeatbotEvent,
    BeatbotEventClient,
    BeatbotEventError,
    BeatbotTokenRejectedError,
)


def client(**kwargs):
    return BeatbotEventClient(
        SimpleNamespace(),
        "wss://test",
        kwargs.pop("access_token", lambda: "token"),
        kwargs.pop("event_callback", Mock()),
        **kwargs,
    )


async def test_connect_delivers_unique_events_and_ignores_malformed():
    event_callback = Mock()
    event = BeatbotEvent("event-1", "status", "device-1", {"online": True})
    stream = SimpleNamespace(
        connect=AsyncMock(),
        receive=AsyncMock(
            side_effect=[BeatbotEventError("bad"), event, event, asyncio.CancelledError]
        ),
        close=AsyncMock(),
    )
    event_client = client(event_callback=event_callback)

    with (
        patch("beatbot_cloud.event_client.BeatbotEventStream", return_value=stream),
        pytest.raises(asyncio.CancelledError),
    ):
        await event_client._async_connect_and_receive()

    event_callback.assert_called_once_with(event)
    stream.close.assert_awaited_once()


async def test_reconnect_callback_runs_after_first_connection():
    reconnect_callback = AsyncMock()
    event_client = client(reconnect_callback=reconnect_callback)
    event_client._has_connected = True
    stream = SimpleNamespace(
        connect=AsyncMock(),
        receive=AsyncMock(side_effect=asyncio.CancelledError),
        close=AsyncMock(),
    )

    with (
        patch("beatbot_cloud.event_client.BeatbotEventStream", return_value=stream),
        pytest.raises(asyncio.CancelledError),
    ):
        await event_client._async_connect_and_receive()

    reconnect_callback.assert_awaited_once()


async def test_token_rejection_refreshes_and_reconnects():
    refresh_callback = AsyncMock(return_value="new-token")
    event_client = client(token_refresh_callback=refresh_callback)
    event_client._async_connect_and_receive = AsyncMock(
        side_effect=[
            BeatbotTokenRejectedError("old-token"),
            BeatbotConnectionReplacedError(),
        ]
    )

    await event_client.async_run()

    refresh_callback.assert_awaited_once_with("old-token")
    assert event_client._next_access_token == "new-token"


async def test_repeated_token_rejection_requires_authentication():
    event_client = client(token_refresh_callback=AsyncMock(return_value="new-token"))
    event_client._token_refresh_attempted = True
    event_client._async_connect_and_receive = AsyncMock(
        side_effect=BeatbotTokenRejectedError("new-token")
    )

    with pytest.raises(BeatbotAuthenticationError):
        await event_client.async_run()


async def test_connection_failure_retries():
    event_client = client()
    event_client._async_connect_and_receive = AsyncMock(
        side_effect=[
            BeatbotConnectionError("offline"),
            BeatbotConnectionReplacedError(),
        ]
    )

    with patch("beatbot_cloud.event_client.asyncio.sleep", AsyncMock()) as sleep:
        await event_client.async_run()

    sleep.assert_awaited_once()


async def test_close_is_idempotent():
    event_client = client()
    stream = SimpleNamespace(close=AsyncMock())
    event_client._stream = stream

    await event_client.async_close()
    await event_client.async_close()

    stream.close.assert_awaited_once()
