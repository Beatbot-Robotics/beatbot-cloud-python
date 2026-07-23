"""Tests for the Beatbot WebSocket transport."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiohttp import WSMsgType, WSServerHandshakeError

from beatbot_cloud import (
    BeatbotAuthenticationError,
    BeatbotConnectionError,
    BeatbotConnectionReplacedError,
    BeatbotEventError,
    BeatbotEventStream,
    BeatbotTokenRejectedError,
)


def stream(session=None):
    return BeatbotEventStream(session or SimpleNamespace(), "wss://test", "token")


@pytest.mark.parametrize(
    "raw",
    ["not-json", "[]", "{}", '{"eventId":"1","type":"status","deviceId":"d"}'],
)
def test_parse_rejects_invalid_events(raw):
    with pytest.raises(BeatbotConnectionError):
        BeatbotEventStream.parse_event(raw)


def test_parse_rejects_removed_payload():
    with pytest.raises(BeatbotConnectionError, match="not null"):
        BeatbotEventStream.parse_event(
            '{"eventId":"1","type":"device_removed","deviceId":"d","payload":{}}'
        )


def test_parse_event():
    event = BeatbotEventStream.parse_event(
        '{"eventId":"1","type":"status","deviceId":"d","payload":{"online":true}}'
    )
    assert event.event_id == "1"
    assert event.payload == {"online": True}


@pytest.mark.parametrize(
    "payload",
    [
        {"interfaceInfo": "vacuum.battery"},
        {"interfaceInfo": "vacuum.battery", "value": None},
        {"interfaceInfo": "vacuum.battery", "value": True},
        {"interfaceInfo": "switch.child_lock", "value": 1},
        {"interfaceInfo": "", "value": 1},
    ],
)
def test_parse_rejects_invalid_property_values(payload):
    with pytest.raises(BeatbotEventError, match="Property event"):
        BeatbotEventStream.parse_event(
            '{"eventId":"1","type":"properties_changed","deviceId":"d",'
            f'"payload":{json.dumps(payload)}}}'
        )


def test_parse_accepts_unknown_property_with_value():
    event = BeatbotEventStream.parse_event(
        '{"eventId":"1","type":"properties_changed","deviceId":"d",'
        '"payload":{"interfaceInfo":"future.value","value":null}}'
    )
    assert event.payload == {"interfaceInfo": "future.value", "value": None}


def test_parse_rejects_invalid_status_value():
    with pytest.raises(BeatbotConnectionError, match="Status event"):
        BeatbotEventStream.parse_event(
            '{"eventId":"1","type":"status","deviceId":"d","payload":{"online":"yes"}}'
        )


def test_parse_removed_event():
    event = BeatbotEventStream.parse_event(
        '{"eventId":"1","type":"device_removed","deviceId":"d","payload":null}'
    )
    assert event.payload is None


async def test_connect_and_close():
    websocket = SimpleNamespace(closed=False, close=AsyncMock())
    session = SimpleNamespace(ws_connect=AsyncMock(return_value=websocket))
    event_stream = stream(session)
    await event_stream.connect()
    await event_stream.close()
    websocket.close.assert_awaited_once()


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (401, BeatbotTokenRejectedError),
        (403, BeatbotAuthenticationError),
        (500, BeatbotConnectionError),
    ],
)
async def test_connect_translates_handshake_errors(status, error_type):
    error = WSServerHandshakeError(
        SimpleNamespace(real_url="wss://test"), (), status=status
    )
    session = SimpleNamespace(ws_connect=AsyncMock(side_effect=error))
    with pytest.raises(error_type):
        await stream(session).connect()


async def test_receive_requires_connection():
    with pytest.raises(RuntimeError, match="not connected"):
        await stream().receive()


async def test_receive_text_event():
    message = SimpleNamespace(
        type=WSMsgType.TEXT,
        data='{"eventId":"1","type":"status","deviceId":"d","payload":{"online":true}}',
    )
    event_stream = stream()
    event_stream._ws = SimpleNamespace(receive=AsyncMock(return_value=message))
    assert (await event_stream.receive()).device_id == "d"


@pytest.mark.parametrize(
    ("code", "error_type"),
    [
        (4001, BeatbotTokenRejectedError),
        (4002, BeatbotConnectionReplacedError),
        (4003, BeatbotAuthenticationError),
        (4008, BeatbotConnectionError),
    ],
)
async def test_receive_translates_close_codes(code, error_type):
    message = SimpleNamespace(type=WSMsgType.CLOSE, data=None)
    event_stream = stream()
    event_stream._ws = SimpleNamespace(
        receive=AsyncMock(return_value=message),
        close_code=code,
        exception=lambda: None,
    )
    with pytest.raises(error_type):
        await event_stream.receive()


async def test_receive_rejects_unexpected_message():
    message = SimpleNamespace(type=WSMsgType.BINARY, data=b"data")
    event_stream = stream()
    event_stream._ws = SimpleNamespace(receive=AsyncMock(return_value=message))
    with pytest.raises(BeatbotConnectionError, match="Unexpected"):
        await event_stream.receive()


async def test_close_without_connection():
    await stream().close()
