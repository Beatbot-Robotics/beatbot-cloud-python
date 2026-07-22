"""Asynchronous client for the Beatbot cloud API."""

from .client import BeatbotClient
from .exceptions import (
    BeatbotAuthenticationError,
    BeatbotConnectionError,
    BeatbotConnectionReplacedError,
    BeatbotTokenRejectedError,
)
from .models import BeatbotCapability, BeatbotDeviceData, BeatbotEvent, FirmwareVersion
from .websocket import BeatbotEventStream

__all__ = [
    "BeatbotAuthenticationError",
    "BeatbotCapability",
    "BeatbotClient",
    "BeatbotConnectionError",
    "BeatbotConnectionReplacedError",
    "BeatbotDeviceData",
    "BeatbotEvent",
    "BeatbotEventStream",
    "BeatbotTokenRejectedError",
    "FirmwareVersion",
]
