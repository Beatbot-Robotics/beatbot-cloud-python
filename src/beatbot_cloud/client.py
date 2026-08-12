"""Region-aware asynchronous Beatbot REST client."""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from inspect import isawaitable
from typing import Any, TypeAlias

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import (
    DEVICE_ACTIONS_PATH,
    DEVICE_STATES_PATH,
    DEVICES_PATH,
    EVENTS_PATH,
    HTTP_API_TIMEOUT,
    INTERFACE_WORK_MODE,
    REGION_API_BASE_URL,
    RESULT_SUCCESS_CODE,
)
from .exceptions import BeatbotAuthenticationError, BeatbotConnectionError
from .models import BeatbotCapability, BeatbotDeviceData, FirmwareVersion

_LOGGER = logging.getLogger(__name__)


AccessTokenProvider: TypeAlias = Callable[[], str | Awaitable[str]]


class BeatbotClient:
    """Access the Beatbot cloud API."""

    def __init__(
        self,
        region: str,
        session: ClientSession,
        access_token: str | AccessTokenProvider,
    ) -> None:
        """Initialize the client for an OAuth token's region claim."""
        try:
            self._base_url = REGION_API_BASE_URL[region]
        except KeyError as err:
            raise ValueError(f"Unknown or missing Beatbot region: {region!r}") from err
        self._session = session
        self._access_token = access_token

    async def async_get_access_token(self) -> str:
        """Return the current access token."""
        token = (
            self._access_token() if callable(self._access_token) else self._access_token
        )
        if isawaitable(token):
            token = await token
        if not token:
            raise BeatbotAuthenticationError("Missing OAuth access token")
        return token

    @property
    def event_stream_url(self) -> str:
        """Return the region-routed WebSocket endpoint."""
        if self._base_url.startswith("https://"):
            base_url = f"wss://{self._base_url.removeprefix('https://')}"
        else:
            base_url = self._base_url
        return f"{base_url}{EVENTS_PATH}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_body: Any | None = None,
    ) -> Any:
        """Request and validate a Beatbot result envelope."""
        access_token = await self.async_get_access_token()
        try:
            response = await self._session.request(
                method,
                f"{self._base_url}{path}",
                params=params,
                json=json_body,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {access_token}",
                },
                timeout=ClientTimeout(total=HTTP_API_TIMEOUT),
            )
        except ClientError as err:
            raise BeatbotConnectionError(str(err)) from err

        body = await response.text()
        if response.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
            raise BeatbotAuthenticationError(f"Unauthorized: {response.status}")
        if response.status >= HTTPStatus.BAD_REQUEST:
            raise BeatbotConnectionError(f"API request failed: {response.status}")

        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, TypeError) as err:
            content_type = response.headers.get("Content-Type", "unknown")
            _LOGGER.warning(
                "Beatbot API returned non-JSON response (%s, %s)",
                response.status,
                content_type,
            )
            raise BeatbotConnectionError(
                f"API returned non-JSON response ({response.status}, {content_type})"
            ) from err

        if not isinstance(payload, dict):
            raise BeatbotConnectionError("API returned an invalid response envelope")
        if payload.get("code") != RESULT_SUCCESS_CODE:
            raise BeatbotConnectionError(
                f"API error {payload.get('code')}: {payload.get('message')}"
            )
        return payload.get("data")

    async def get_devices(self) -> list[BeatbotDeviceData]:
        """Return devices discovered for the account."""
        raw = await self._request("GET", DEVICES_PATH)
        if not raw:
            return []
        if isinstance(raw, str):
            try:
                discovery = json.loads(raw)
            except (json.JSONDecodeError, TypeError) as err:
                raise BeatbotConnectionError(
                    f"Invalid discovery payload: {err}"
                ) from err
        else:
            discovery = raw

        devices = (discovery or {}).get("devices") or []
        return [
            parsed
            for device in devices
            if (parsed := self._parse_device(device)) is not None
        ]

    @staticmethod
    def _parse_device(device: dict[str, Any]) -> BeatbotDeviceData | None:
        """Parse a discovery device, ignoring entries without an ID."""
        device_id = device.get("deviceId") or ""
        if not device_id:
            return None
        versions = [
            FirmwareVersion(
                channel=item.get("channel", 0), version=item.get("version") or ""
            )
            for item in (device.get("versions") or [])
            if isinstance(item, dict)
        ]
        capabilities = device.get("capabilities")
        return BeatbotDeviceData(
            device_id=device_id,
            product_id=device.get("productId") or "",
            product_category=device.get("productCategory") or "",
            name=device.get("name") or "",
            model=device.get("model") or "",
            work_status=0,
            work_mode=0,
            error_code=0,
            battery_level=0,
            versions=versions,
            is_online=bool(device.get("isOnline", False)),
            work_mode_options=BeatbotClient._parse_work_mode_options(capabilities),
            capabilities=BeatbotClient._parse_capabilities(capabilities),
        )

    @staticmethod
    def _parse_work_mode_options(
        capabilities: list[dict[str, Any]] | None,
    ) -> dict[int, str]:
        """Extract the per-device work-mode value-to-label mapping."""
        for capability in capabilities or []:
            if not isinstance(capability, dict):
                continue
            if capability.get("interfaceInfo") != INTERFACE_WORK_MODE:
                continue
            configuration = capability.get("configuration")
            if isinstance(configuration, str):
                try:
                    configuration = json.loads(configuration)
                except (json.JSONDecodeError, TypeError):
                    configuration = None
            if not isinstance(configuration, dict):
                return {}
            options: dict[int, str] = {}
            for option in configuration.get("options") or []:
                value = option.get("value")
                label = option.get("label")
                if value is not None and label:
                    options[value] = label
            return options
        return {}

    @staticmethod
    def _parse_capabilities(
        capabilities: list[dict[str, Any]] | None,
    ) -> dict[str, BeatbotCapability]:
        """Parse discovery capabilities into a mapping by interface key."""
        parsed: dict[str, BeatbotCapability] = {}
        for capability in capabilities or []:
            if not isinstance(capability, dict):
                continue
            interface_info = capability.get("interfaceInfo")
            if not interface_info:
                continue
            parsed[interface_info] = BeatbotCapability(
                interface_info=interface_info,
                retrievable=bool(capability.get("retrievable", False)),
                proactively_reported=bool(capability.get("proactivelyReported", False)),
                non_controllable=bool(capability.get("nonControllable", False)),
            )
        return parsed

    async def get_device_states(self) -> dict[str, dict[str, Any]]:
        """Return batched runtime state for all devices."""
        raw = await self._request("GET", DEVICE_STATES_PATH)
        if isinstance(raw, str):
            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return {}
        else:
            payload = raw
        devices = (payload or {}).get("devices") or []
        return {
            device["deviceId"]: {
                "is_online": device.get("isOnline"),
                "states": device.get("states") or {},
            }
            for device in devices
            if device.get("deviceId")
        }

    async def get_device_state(self, device_id: str) -> dict[str, Any]:
        """Return runtime state for one device."""
        raw = await self._request("GET", f"{DEVICE_ACTIONS_PATH}/{device_id}/state")
        if isinstance(raw, str):
            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return {}
        else:
            payload = raw
        if not isinstance(payload, dict):
            return {}
        return {
            "is_online": payload.get("isOnline"),
            "states": payload.get("states") or {},
        }

    async def send_action(self, device_id: str, interface_info: str) -> None:
        """Issue a parameterless action by its interface key."""
        await self._request(
            "POST",
            f"{DEVICE_ACTIONS_PATH}/{device_id}/actions",
            json_body={"interfaceInfo": interface_info},
        )

    async def set_work_mode(self, device_id: str, label: str) -> None:
        """Set a device's work mode by its advertised label."""
        await self._request(
            "POST",
            f"{DEVICE_ACTIONS_PATH}/{device_id}/actions",
            json_body={"interfaceInfo": INTERFACE_WORK_MODE, "label": label},
        )

    async def set_switch(self, device_id: str, interface_info: str, label: str) -> None:
        """Set an on/off capability."""
        await self._request(
            "POST",
            f"{DEVICE_ACTIONS_PATH}/{device_id}/actions",
            json_body={"interfaceInfo": interface_info, "label": label},
        )
