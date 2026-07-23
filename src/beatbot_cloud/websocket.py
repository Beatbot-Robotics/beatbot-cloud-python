"""Low-level Beatbot cloud WebSocket event transport."""

from __future__ import annotations

import json
from typing import Any

from aiohttp import (
    ClientSession,
    ClientWebSocketResponse,
    WSMsgType,
    WSServerHandshakeError,
)

from .exceptions import (
    BeatbotAuthenticationError,
    BeatbotConnectionError,
    BeatbotConnectionReplacedError,
    BeatbotEventError,
    BeatbotTokenRejectedError,
)
from .models import BeatbotEvent

_INTEGER_PROPERTIES = {
    "vacuum.state",
    "vacuum.battery",
    "sensor.error",
    "select.work_mode",
}
_BOOLEAN_PROPERTIES = {"switch.child_lock", "switch.voice_disturb"}


class BeatbotEventStream:
    """Connect to and receive validated events from a Beatbot account stream."""

    def __init__(
        self,
        session: ClientSession,
        url: str,
        access_token: str,
        *,
        heartbeat: float = 30.0,
        receive_timeout: float = 90.0,
    ) -> None:
        """Initialize an event stream without connecting it."""
        self._session = session
        self._url = url
        self._access_token = access_token
        self._heartbeat = heartbeat
        self._receive_timeout = receive_timeout
        self._ws: ClientWebSocketResponse | None = None

    async def connect(self) -> None:
        """Open the WebSocket connection."""
        try:
            self._ws = await self._session.ws_connect(
                self._url,
                headers={"Authorization": f"Bearer {self._access_token}"},
                heartbeat=self._heartbeat,
                autoping=True,
            )
        except WSServerHandshakeError as err:
            if err.status == 401:
                raise BeatbotTokenRejectedError(
                    self._access_token, handshake=True
                ) from err
            if err.status == 403:
                raise BeatbotAuthenticationError from err
            raise BeatbotConnectionError(str(err)) from err

    async def receive(self) -> BeatbotEvent:
        """Receive and validate the next text event."""
        if self._ws is None:
            raise RuntimeError("Event stream is not connected")
        message = await self._ws.receive(timeout=self._receive_timeout)
        if message.type is WSMsgType.TEXT:
            return self.parse_event(message.data)
        if message.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR):
            self._raise_for_close_code(self._ws.close_code, self._ws.exception())
        raise BeatbotConnectionError(f"Unexpected WebSocket message: {message.type}")

    @staticmethod
    def parse_event(raw: str) -> BeatbotEvent:
        """Parse and validate a Beatbot event envelope."""
        try:
            event: Any = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as err:
            raise BeatbotEventError("Event is not valid JSON") from err
        if not isinstance(event, dict):
            raise BeatbotEventError("Event is not an object")
        event_id = event.get("eventId")
        event_type = event.get("type")
        device_id = event.get("deviceId")
        if not all(
            isinstance(value, str) and value
            for value in (event_id, event_type, device_id)
        ):
            raise BeatbotEventError("Event is missing eventId, type, or deviceId")
        payload = event.get("payload")
        if event_type == "device_removed":
            if payload is not None:
                raise BeatbotEventError("device_removed payload is not null")
        elif not isinstance(payload, dict):
            raise BeatbotEventError("Event payload is not an object")
        if event_type == "properties_changed":
            BeatbotEventStream._validate_property_payload(payload)
        elif event_type == "status" and not isinstance(payload.get("online"), bool):
            raise BeatbotEventError("Status event has an invalid online value")
        return BeatbotEvent(event_id, event_type, device_id, payload)

    @staticmethod
    def _validate_property_payload(payload: dict[str, Any]) -> None:
        """Validate known property values before exposing an event."""
        interface_info = payload.get("interfaceInfo")
        if not isinstance(interface_info, str) or not interface_info:
            raise BeatbotEventError("Property event is missing a valid interfaceInfo")
        if "value" not in payload:
            raise BeatbotEventError("Property event is missing value")
        value = payload["value"]
        if interface_info in _INTEGER_PROPERTIES and (
            not isinstance(value, int) or isinstance(value, bool)
        ):
            raise BeatbotEventError(
                f"Property event has an invalid value for {interface_info}"
            )
        if interface_info in _BOOLEAN_PROPERTIES and not isinstance(value, bool):
            raise BeatbotEventError(
                f"Property event has an invalid value for {interface_info}"
            )

    def _raise_for_close_code(
        self, code: int | None, error: BaseException | None
    ) -> None:
        """Translate Beatbot close codes into public client exceptions."""
        if code == 4001:
            raise BeatbotTokenRejectedError(self._access_token) from error
        if code == 4002:
            raise BeatbotConnectionReplacedError from error
        if code == 4003:
            raise BeatbotAuthenticationError from error
        raise BeatbotConnectionError(f"WebSocket closed with code {code}") from error

    async def close(self) -> None:
        """Close the stream if connected."""
        websocket, self._ws = self._ws, None
        if websocket is not None and not websocket.closed:
            await websocket.close()
