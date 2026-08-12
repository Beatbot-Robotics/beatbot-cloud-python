"""Tests for the Beatbot REST client."""

from __future__ import annotations

import json

import pytest
from aiohttp import ClientError

from beatbot_cloud import (
    BeatbotAuthenticationError,
    BeatbotClient,
    BeatbotConnectionError,
    BeatbotEvent,
)
from beatbot_cloud.const import REGION_API_BASE_URL


class Response:
    """Small response double."""

    def __init__(self, data, *, status=200, content_type="application/json"):
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.body = data if isinstance(data, str) else json.dumps(data)

    async def text(self):
        return self.body


class Session:
    """Record requests and return or raise a configured result."""

    def __init__(self, result):
        self.result = result
        self.calls = []

    async def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def client(result, region="na", access_token="access-token"):
    session = Session(result)
    return BeatbotClient(region, session, access_token), session


def envelope(data=None, *, code=200, message=None):
    return Response({"code": code, "message": message, "data": data})


@pytest.mark.parametrize("region", ["cn", "na", "eu"])
def test_region_and_event_url(region):
    api, _ = client(envelope(), region)
    assert api._base_url == REGION_API_BASE_URL[region]
    assert api.event_stream_url.startswith("wss://")


def test_unknown_region():
    with pytest.raises(ValueError, match="Unknown or missing"):
        client(envelope(), "moon")


def test_event_url_preserves_non_https_scheme():
    api, _ = client(envelope())
    api._base_url = "ws://example.test"
    assert api.event_stream_url == "ws://example.test/openapi/v1/ha/ws"


@pytest.mark.parametrize("status", [401, 403])
async def test_request_rejects_auth_status(status):
    api, _ = client(Response("denied", status=status))
    with pytest.raises(BeatbotAuthenticationError):
        await api._request("GET", "/test")


async def test_request_rejects_http_error():
    api, _ = client(Response("failed", status=500))
    with pytest.raises(BeatbotConnectionError, match="500"):
        await api._request("GET", "/test")


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (Response("not json", content_type="text/plain"), "non-JSON"),
        (Response("[]"), "invalid response envelope"),
        (envelope(code=400, message="bad"), "API error 400: bad"),
    ],
)
async def test_request_rejects_invalid_envelope(response, message):
    api, _ = client(response)
    with pytest.raises(BeatbotConnectionError, match=message):
        await api._request("GET", "/test")


async def test_request_forwards_options_and_returns_data():
    api, session = client(envelope({"ok": True}))
    result = await api._request(
        "POST", "/test", params={"a": "b"}, json_body={"value": 1}
    )
    assert result == {"ok": True}
    method, url, kwargs = session.calls[0]
    assert method == "POST"
    assert url.endswith("/test")
    assert kwargs["params"] == {"a": "b"}
    assert kwargs["json"] == {"value": 1}
    assert kwargs["headers"]["Authorization"] == "Bearer access-token"


async def test_client_error_is_connection_error():
    api, _ = client(ClientError("offline"))
    with pytest.raises(BeatbotConnectionError, match="offline"):
        await api._request("GET", "/test")


async def test_timeout_is_connection_error():
    api, _ = client(TimeoutError("timed out"))
    with pytest.raises(BeatbotConnectionError, match="timed out"):
        await api._request("GET", "/test")


async def test_async_access_token_provider():
    async def access_token():
        return "rotated-token"

    api, session = client(envelope(), access_token=access_token)

    await api.get_devices()

    assert session.calls[0][2]["headers"]["Authorization"] == "Bearer rotated-token"


async def test_missing_access_token_requires_authentication():
    api, _ = client(envelope(), access_token="")
    with pytest.raises(BeatbotAuthenticationError, match="Missing"):
        await api.get_devices()


async def test_get_devices_empty():
    api, _ = client(envelope(None))
    assert await api.get_devices() == []


async def test_get_devices_accepts_object_payload():
    api, _ = client(envelope({"devices": []}))
    assert await api.get_devices() == []


async def test_get_devices_rejects_invalid_string():
    api, _ = client(envelope("not json"))
    with pytest.raises(BeatbotConnectionError, match="Invalid discovery"):
        await api.get_devices()


async def test_get_devices_parses_models_and_capabilities():
    configuration = json.dumps(
        {"options": [{"value": 0, "label": "quick"}, {"value": None}]}
    )
    data = {
        "devices": [
            {},
            {
                "deviceId": "device-1",
                "productId": "product-1",
                "productCategory": "pool_clean_bot",
                "name": "Pool bot",
                "model": "Aqua",
                "isOnline": True,
                "versions": [None, {"channel": 1, "version": "2.0"}],
                "capabilities": [
                    None,
                    {},
                    {
                        "interfaceInfo": "select.work_mode",
                        "configuration": configuration,
                        "retrievable": True,
                        "proactivelyReported": True,
                    },
                ],
            },
        ]
    }
    api, _ = client(envelope(json.dumps(data)))
    devices = await api.get_devices()
    assert len(devices) == 1
    assert devices[0].device_id == "device-1"
    assert devices[0].work_mode_options == {0: "quick"}
    assert devices[0].versions[0].version == "2.0"
    assert devices[0].capabilities["select.work_mode"].retrievable


def test_device_applies_and_copies_runtime_state():
    """Runtime state is parsed by the library model without dynamic attributes."""
    api, _ = client(envelope())
    device = api._parse_device({"deviceId": "d1"})
    previous = api._parse_device({"deviceId": "d1", "isOnline": True})
    assert device is not None
    assert previous is not None
    previous.apply_state(
        {
            "vacuum.state": 5,
            "vacuum.battery": 80,
            "sensor.error": 2,
            "select.work_mode": 1,
            "switch.child_lock": True,
            "switch.voice_disturb": True,
        }
    )
    device.copy_runtime_state_from(previous)

    assert device.work_status == 5
    assert device.battery_level == 80
    assert device.error_code == 2
    assert device.work_mode == 1
    assert device.child_lock
    assert device.voice_disturb
    assert device.is_online


def test_state_events_apply_to_device():
    """State-bearing events interpret their payload in the library."""
    api, _ = client(envelope())
    device = api._parse_device({"deviceId": "d1", "isOnline": True})
    assert device is not None

    changed = BeatbotEvent(
        "1",
        "properties_changed",
        "d1",
        {"interfaceInfo": "vacuum.battery", "value": 42},
    ).apply_to(device)
    online_changed = BeatbotEvent("2", "status", "d1", {"online": False}).apply_to(
        device
    )

    assert changed
    assert online_changed
    assert device.battery_level == 42
    assert not device.is_online
    assert not BeatbotEvent("3", "unknown", "d1", {}).apply_to(device)


@pytest.mark.parametrize("configuration", ["bad json", [], None])
def test_invalid_work_mode_configuration(configuration):
    assert (
        BeatbotClient._parse_work_mode_options(
            [{"interfaceInfo": "select.work_mode", "configuration": configuration}]
        )
        == {}
    )


async def test_get_device_states():
    api, _ = client(
        envelope(
            {
                "devices": [
                    {},
                    {"deviceId": "d1", "isOnline": True, "states": {"x": 1}},
                ]
            }
        )
    )
    assert await api.get_device_states() == {
        "d1": {"is_online": True, "states": {"x": 1}}
    }


async def test_get_device_states_invalid_string():
    api, _ = client(envelope("bad"))
    assert await api.get_device_states() == {}


@pytest.mark.parametrize("data", ["bad", [], None])
async def test_get_device_state_invalid(data):
    api, _ = client(envelope(data))
    assert await api.get_device_state("d1") == {}


async def test_get_device_state():
    api, _ = client(envelope({"isOnline": False, "states": {"battery": 10}}))
    assert await api.get_device_state("d1") == {
        "is_online": False,
        "states": {"battery": 10},
    }


async def test_actions():
    api, session = client(envelope())
    await api.send_action("d1", "vacuum.start")
    await api.set_work_mode("d1", "quick")
    await api.set_switch("d1", "switch.child_lock", "on")
    assert [call[2]["json"] for call in session.calls] == [
        {"interfaceInfo": "vacuum.start"},
        {"interfaceInfo": "select.work_mode", "label": "quick"},
        {"interfaceInfo": "switch.child_lock", "label": "on"},
    ]
