"""Resilient Beatbot cloud event client."""

from __future__ import annotations

import asyncio
import logging
import random
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from inspect import isawaitable

from aiohttp import ClientError, ClientSession

from .client import AccessTokenProvider
from .exceptions import (
    BeatbotAuthenticationError,
    BeatbotConnectionError,
    BeatbotConnectionReplacedError,
    BeatbotEventError,
    BeatbotTokenRejectedError,
)
from .models import BeatbotEvent
from .websocket import BeatbotEventStream

_LOGGER = logging.getLogger(__name__)

_EVENT_DEDUP_CACHE_SIZE = 256
_RECONNECT_DELAYS = (1.0, 2.0, 4.0, 8.0, 30.0, 60.0)
_RECONNECT_JITTER = 0.2

EventCallback = Callable[[BeatbotEvent], None | Awaitable[None]]
DeviceCallback = Callable[[str], None | Awaitable[None]]
ReconnectCallback = Callable[[], None | Awaitable[None]]
TokenRefreshCallback = Callable[[str], str | Awaitable[str]]


class BeatbotEventClient:
    """Maintain and recover an account-scoped Beatbot event stream."""

    def __init__(
        self,
        session: ClientSession,
        url: str,
        access_token: AccessTokenProvider,
        event_callback: EventCallback | None = None,
        *,
        state_callback: EventCallback | None = None,
        device_added_callback: DeviceCallback | None = None,
        device_removed_callback: DeviceCallback | None = None,
        reconnect_callback: ReconnectCallback | None = None,
        token_refresh_callback: TokenRefreshCallback | None = None,
    ) -> None:
        """Initialize the event client without connecting it."""
        self._session = session
        self._url = url
        self._access_token = access_token
        self._event_callback = event_callback
        self._state_callback = state_callback
        self._device_added_callback = device_added_callback
        self._device_removed_callback = device_removed_callback
        self._reconnect_callback = reconnect_callback
        self._token_refresh_callback = token_refresh_callback
        self._stream: BeatbotEventStream | None = None
        self._stopping = False
        self._token_refresh_attempted = False
        self._has_connected = False
        self._connection_generation = 0
        self._next_access_token: str | None = None
        self._seen_event_ids: OrderedDict[str, None] = OrderedDict()

    async def async_run(self) -> None:
        """Connect and receive events until closed or authentication fails."""
        failures = 0
        self._stopping = False
        try:
            while not self._stopping:
                connection_generation = self._connection_generation
                try:
                    await self._async_connect_and_receive()
                except asyncio.CancelledError:
                    raise
                except BeatbotConnectionReplacedError:
                    return
                except BeatbotTokenRejectedError as err:
                    if (
                        self._token_refresh_attempted
                        or self._token_refresh_callback is None
                    ):
                        raise BeatbotAuthenticationError(
                            "Event stream rejected the refreshed access token"
                        ) from err
                    try:
                        token = self._token_refresh_callback(err.access_token)
                        if isawaitable(token):
                            token = await token
                        if not token:
                            raise BeatbotAuthenticationError(
                                "Token refresh returned no access token"
                            )
                    except BeatbotAuthenticationError:
                        raise
                    except BeatbotConnectionError as refresh_err:
                        failures += 1
                        _LOGGER.warning(
                            "Beatbot OAuth token refresh failed: %s", refresh_err
                        )
                    else:
                        self._next_access_token = token
                        self._token_refresh_attempted = True
                        failures = 0
                        continue
                except BeatbotAuthenticationError:
                    raise
                except (
                    TimeoutError,
                    BeatbotConnectionError,
                    ClientError,
                    ConnectionError,
                ) as err:
                    if self._connection_generation != connection_generation:
                        failures = 0
                    failures += 1
                    _LOGGER.warning("Beatbot event stream disconnected: %s", err)
                except Exception:
                    failures += 1
                    _LOGGER.exception("Unexpected Beatbot event stream failure")

                if self._stopping:
                    return
                delay = _RECONNECT_DELAYS[min(failures - 1, len(_RECONNECT_DELAYS) - 1)]
                delay *= random.uniform(
                    1.0 - _RECONNECT_JITTER, 1.0 + _RECONNECT_JITTER
                )
                await asyncio.sleep(delay)
        finally:
            await self.async_close()

    async def _async_connect_and_receive(self) -> None:
        """Connect once and receive until the connection closes."""
        access_token = self._next_access_token
        self._next_access_token = None
        if access_token is None:
            access_token = self._access_token()
            if isawaitable(access_token):
                access_token = await access_token
        if not access_token:
            raise BeatbotAuthenticationError("Missing OAuth access token")

        stream = BeatbotEventStream(self._session, self._url, access_token)
        self._stream = stream
        try:
            await stream.connect()
            is_reconnect = self._has_connected
            self._has_connected = True
            self._connection_generation += 1
            if is_reconnect and self._reconnect_callback is not None:
                result = self._reconnect_callback()
                if isawaitable(result):
                    await result
            while not self._stopping:
                try:
                    event = await stream.receive()
                except BeatbotEventError as err:
                    _LOGGER.warning("Ignoring malformed Beatbot event: %s", err)
                    continue
                self._token_refresh_attempted = False
                if event.event_id in self._seen_event_ids:
                    continue
                self._remember_event(event.event_id)
                await self._async_dispatch_event(event)
        finally:
            await stream.close()
            if self._stream is stream:
                self._stream = None

    async def _async_dispatch_event(self, event: BeatbotEvent) -> None:
        """Route cloud event types to consumer callbacks."""
        if self._event_callback is not None:
            result = self._event_callback(event)
            if isawaitable(result):
                await result
        if event.event_type in ("properties_changed", "status"):
            if self._state_callback is not None:
                result = self._state_callback(event)
                if isawaitable(result):
                    await result
        elif event.event_type == "device_added":
            if self._device_added_callback is not None:
                result = self._device_added_callback(event.device_id)
                if isawaitable(result):
                    await result
        elif (
            event.event_type == "device_removed"
            and self._device_removed_callback is not None
        ):
            result = self._device_removed_callback(event.device_id)
            if isawaitable(result):
                await result

    async def async_close(self) -> None:
        """Stop receiving and close the current connection."""
        self._stopping = True
        stream, self._stream = self._stream, None
        if stream is not None:
            await stream.close()

    def _remember_event(self, event_id: str) -> None:
        """Remember an event identifier for bounded duplicate suppression."""
        self._seen_event_ids[event_id] = None
        self._seen_event_ids.move_to_end(event_id)
        while len(self._seen_event_ids) > _EVENT_DEDUP_CACHE_SIZE:
            self._seen_event_ids.popitem(last=False)
