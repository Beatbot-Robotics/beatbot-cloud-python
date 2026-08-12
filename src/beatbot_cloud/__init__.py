"""Asynchronous client for the Beatbot cloud API."""

from .auth import decode_access_token
from .client import BeatbotClient
from .event_client import BeatbotEventClient
from .exceptions import (
    BeatbotAuthenticationError,
    BeatbotConnectionError,
    BeatbotConnectionReplacedError,
    BeatbotEventError,
    BeatbotTokenRejectedError,
)
from .models import BeatbotCapability, BeatbotDeviceData, BeatbotEvent, FirmwareVersion
from .protocol import (
    ERROR_BITS_BY_CATEGORY,
    STATUS_BY_CATEGORY,
    DeviceError,
    DeviceStatus,
    ProductCategory,
    error_for,
    error_mask_for,
    status_for,
)
from .websocket import BeatbotEventStream

__all__ = [
    "BeatbotAuthenticationError",
    "BeatbotCapability",
    "BeatbotClient",
    "BeatbotConnectionError",
    "BeatbotConnectionReplacedError",
    "BeatbotDeviceData",
    "BeatbotEvent",
    "BeatbotEventClient",
    "BeatbotEventError",
    "BeatbotEventStream",
    "BeatbotTokenRejectedError",
    "DeviceError",
    "DeviceStatus",
    "ERROR_BITS_BY_CATEGORY",
    "FirmwareVersion",
    "ProductCategory",
    "STATUS_BY_CATEGORY",
    "error_for",
    "error_mask_for",
    "status_for",
    "decode_access_token",
]
