"""Asynchronous client for the Beatbot cloud API."""

from .client import BeatbotClient
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
    "BeatbotEventError",
    "BeatbotEventStream",
    "BeatbotTokenRejectedError",
    "DeviceError",
    "DeviceStatus",
    "ERROR_BITS_BY_CATEGORY",
    "FirmwareVersion",
    "ProductCategory",
    "STATUS_BY_CATEGORY",
    "error_mask_for",
    "status_for",
]
