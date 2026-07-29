"""Typed Beatbot cloud models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import (
    INTERFACE_CHILD_LOCK,
    INTERFACE_SENSOR_ERROR,
    INTERFACE_VACUUM_BATTERY,
    INTERFACE_VACUUM_STATE,
    INTERFACE_VOICE_DISTURB,
    INTERFACE_WORK_MODE,
)


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

    def apply_state(
        self, states: dict[str, Any] | None, is_online: bool | None = None
    ) -> None:
        """Apply a runtime-state response or event to this device."""
        if states:
            if INTERFACE_VACUUM_STATE in states:
                self.work_status = states[INTERFACE_VACUUM_STATE]
            if INTERFACE_VACUUM_BATTERY in states:
                self.battery_level = states[INTERFACE_VACUUM_BATTERY]
            if INTERFACE_SENSOR_ERROR in states:
                self.error_code = states[INTERFACE_SENSOR_ERROR]
            if INTERFACE_WORK_MODE in states:
                self.work_mode = states[INTERFACE_WORK_MODE]
            if INTERFACE_CHILD_LOCK in states:
                self.child_lock = states[INTERFACE_CHILD_LOCK]
            if INTERFACE_VOICE_DISTURB in states:
                self.voice_disturb = states[INTERFACE_VOICE_DISTURB]
        if is_online is not None:
            self.is_online = is_online

    def copy_runtime_state_from(self, other: BeatbotDeviceData) -> None:
        """Copy the last-known runtime state from another instance."""
        self.work_status = other.work_status
        self.work_mode = other.work_mode
        self.error_code = other.error_code
        self.battery_level = other.battery_level
        self.is_online = other.is_online
        self.child_lock = other.child_lock
        self.voice_disturb = other.voice_disturb


@dataclass(frozen=True, slots=True)
class BeatbotEvent:
    """A validated Beatbot cloud event envelope."""

    event_id: str
    event_type: str
    device_id: str
    payload: dict[str, Any] | None
