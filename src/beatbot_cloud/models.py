"""Typed Beatbot cloud models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FirmwareVersion:
    """A device firmware version."""

    channel: int
    version: str


@dataclass(slots=True)
class BeatbotCapability:
    """A Home Assistant capability advertised by Beatbot discovery."""

    interface_info: str
    retrievable: bool = False
    proactively_reported: bool = False
    non_controllable: bool = False


@dataclass(slots=True)
class BeatbotDeviceData:
    """A discovered Beatbot device."""

    device_id: str
    product_id: str
    product_category: str
    work_status: int
    work_mode: int
    error_code: int
    battery_level: int
    versions: list[FirmwareVersion]
    is_online: bool
    child_lock: bool = False
    voice_disturb: bool = False
    name: str = ""
    model: str = ""
    work_mode_options: dict[int, str] = field(default_factory=dict)
    capabilities: dict[str, BeatbotCapability] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BeatbotEvent:
    """A validated Beatbot cloud event envelope."""

    event_id: str
    event_type: str
    device_id: str
    payload: dict[str, Any] | None
