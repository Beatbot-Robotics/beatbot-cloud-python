"""Typed Beatbot device protocol values."""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class ProductCategory(StrEnum):
    """Product categories returned by Beatbot discovery."""

    POOL_CLEAN_BOT = "pool_clean_bot"
    CLEAN_BASE_STATION = "clean_base_station"
    LAWN_MOWER = "lawn_mower"


class DeviceStatus(StrEnum):
    """Semantic device statuses decoded from category-specific raw values."""

    STANDBY = "standby"
    GOTO_CHARGE = "goto_charge"
    CHARGING = "charging"
    CHARGE_DONE = "charge_done"
    PAUSED = "paused"
    CLEANING = "cleaning"
    SLEEP = "sleep"
    RETURN_TRIP = "return_trip"
    CLEAN_DONE = "clean_done"
    REMOTE_CONTROL = "remote_control"
    CLEAN_WAIT = "clean_wait"
    WIFI_CONNECT = "wifi_connect"
    DIVING = "diving"
    EMERGE = "emerge"
    AUTO_DOCK = "auto_dock"
    FINISH_CONNECT = "finish_connect"
    DOCK = "dock"
    SELF_CLEANING = "self_cleaning"
    REPLENISH_ENERGY = "replenish_energy"
    CHASE_LIGHT = "chase_light"
    DOCK_DONE = "dock_done"
    UNCHECK = "uncheck"
    SELF_CHECKING = "self_checking"
    CHECK_DOWN = "check_down"


class DeviceError(StrEnum):
    """Semantic errors and notices decoded from device bitmasks."""

    DUST_BOX_FULL = "dust_box_full"
    DUST_BOX_LOSS = "dust_box_loss"
    POWER_LOW = "power_low"
    POWER_CUTTING = "power_cutting"
    ENV_HIGH_TEMPERATURE = "env_high_temperature"
    ENV_LOW_TEMPERATURE = "env_low_temperature"
    MOTOR_ERROR = "motor_error"
    MOTOR_WHEEL_LEFT = "motor_wheel_left"
    MOTOR_WHEEL_RIGHT = "motor_wheel_right"
    MOTOR_THRUSTER_LEFT = "motor_thruster_left"
    MOTOR_THRUSTER_RIGHT = "motor_thruster_right"
    MOTOR_PUMP = "motor_pump"
    MOTOR_AIRPUMP_LEFT = "motor_airpump_left"
    MOTOR_AIRPUMP_RIGHT = "motor_airpump_right"
    MOTOR_BRUSH = "motor_brush"
    MOTOR_REAGENT = "motor_reagent"
    MOTOR_ROD = "motor_rod"
    ENTER_SHAWDOW_WATER_ERROR = "enter_shawdow_water_error"
    TRAPPED = "trapped"
    CHARGE_HIGH_TEMPERATURE = "charge_high_temperature"
    CHARGE_LOW_TEMPERATURE = "charge_low_temperature"
    MOTOR_THRUSTER = "motor_thruster"
    PLATFORM_CLEAN_ERR = "platform_clean_err"
    SELF_ERR_SPRAY = "self_err_spray"
    SELF_ERR_LEVER = "self_err_lever"
    SELF_ERR_PUSHER = "self_err_pusher"
    SELF_ERR_CLEAN_CONFLICT = "self_err_clean_conflict"
    ERR_DUST_NOT_INSTALL = "err_dust_not_install"
    NOTICE_SELF_NOT_PAIRED = "notice_self_not_paired"
    NOTICE_SELF_BASE_DUST = "notice_self_base_dust"
    NOTICE_SELF_TEMP_LOW = "notice_self_temp_low"
    NOTICE_SELF_ROBOT_NOT_COMM = "notice_self_robot_not_comm"
    NOTICE_SELF_ROBOT_NOT_POS = "notice_self_robot_not_pos"
    NOTICE_SELF_ROBOT_DUST = "notice_self_robot_dust"
    NOTICE_CLEAN_CLOSED_DUST = "notice_clean_closed_dust"
    NOTICE_CLEAN_SPRAY_NOT_POS = "notice_clean_spray_not_pos"
    NOTICE_CLEAN_OPEND_DUST = "notice_clean_opend_dust"
    NOTICE_CLEAN_COMM = "notice_clean_comm"
    NOTICE_CLEAN_ROBOT_NOT_POS = "notice_clean_robot_not_pos"
    NOTICE_CLEAN_BASE_DUST = "notice_clean_base_dust"
    NOTICE_CLEAN_SPRAY_LEAVE_POS = "notice_clean_spray_leave_pos"
    NOTICE_CLEAN_USER_END_EARLY = "notice_clean_user_end_early"
    NOTICE_CLEANED_SPRAY_NOT_RESET = "notice_cleaned_spray_not_reset"
    NOTICE_CLEANED_LEVER_NOT_RESET = "notice_cleaned_lever_not_reset"
    NOTICE_CLEAN_DRAIN_PUMP_EMPTY = "notice_clean_drain_pump_empty"
    NOTICE_CLN_ROBOT_DUST_NOT_POS = "notice_cln_robot_dust_not_pos"
    NOTICE_CLEAN_LEVER_NOT_RESET = "notice_clean_lever_not_reset"
    NOTICE_CLEAN_DONE_NORMAL = "notice_clean_done_normal"


STATUS_BY_CATEGORY: Final[dict[ProductCategory, dict[int, DeviceStatus]]] = {
    ProductCategory.POOL_CLEAN_BOT: {
        0: DeviceStatus.STANDBY,
        1: DeviceStatus.GOTO_CHARGE,
        2: DeviceStatus.CHARGING,
        3: DeviceStatus.CHARGE_DONE,
        4: DeviceStatus.PAUSED,
        5: DeviceStatus.CLEANING,
        6: DeviceStatus.SLEEP,
        7: DeviceStatus.RETURN_TRIP,
        8: DeviceStatus.CLEAN_DONE,
        9: DeviceStatus.REMOTE_CONTROL,
        10: DeviceStatus.CLEAN_WAIT,
        11: DeviceStatus.WIFI_CONNECT,
        12: DeviceStatus.DIVING,
        13: DeviceStatus.EMERGE,
        14: DeviceStatus.AUTO_DOCK,
        15: DeviceStatus.FINISH_CONNECT,
        16: DeviceStatus.DOCK,
        17: DeviceStatus.SELF_CLEANING,
        18: DeviceStatus.REPLENISH_ENERGY,
        19: DeviceStatus.CHASE_LIGHT,
        20: DeviceStatus.DOCK_DONE,
    },
    ProductCategory.CLEAN_BASE_STATION: {
        0: DeviceStatus.CLEANING,
        1: DeviceStatus.CLEANING,
        2: DeviceStatus.STANDBY,
        3: DeviceStatus.UNCHECK,
        4: DeviceStatus.SELF_CHECKING,
        5: DeviceStatus.CHECK_DOWN,
    },
    ProductCategory.LAWN_MOWER: {},
}

ERROR_BITS_BY_CATEGORY: Final[
    dict[ProductCategory, tuple[tuple[DeviceError, int], ...]]
] = {
    ProductCategory.POOL_CLEAN_BOT: tuple(
        (error, 1 << bit)
        for bit, error in enumerate(
            (
                DeviceError.DUST_BOX_FULL,
                DeviceError.DUST_BOX_LOSS,
                DeviceError.POWER_LOW,
                DeviceError.POWER_CUTTING,
                DeviceError.ENV_HIGH_TEMPERATURE,
                DeviceError.ENV_LOW_TEMPERATURE,
                DeviceError.MOTOR_ERROR,
                DeviceError.MOTOR_WHEEL_LEFT,
                DeviceError.MOTOR_WHEEL_RIGHT,
                DeviceError.MOTOR_THRUSTER_LEFT,
                DeviceError.MOTOR_THRUSTER_RIGHT,
                DeviceError.MOTOR_PUMP,
                DeviceError.MOTOR_AIRPUMP_LEFT,
                DeviceError.MOTOR_AIRPUMP_RIGHT,
                DeviceError.MOTOR_BRUSH,
                DeviceError.MOTOR_REAGENT,
                DeviceError.MOTOR_ROD,
                DeviceError.ENTER_SHAWDOW_WATER_ERROR,
                DeviceError.TRAPPED,
                DeviceError.CHARGE_HIGH_TEMPERATURE,
                DeviceError.CHARGE_LOW_TEMPERATURE,
                DeviceError.MOTOR_THRUSTER,
                DeviceError.PLATFORM_CLEAN_ERR,
            )
        )
    ),
    ProductCategory.CLEAN_BASE_STATION: tuple(
        (error, 1 << bit)
        for bit, error in enumerate(
            (
                DeviceError.SELF_ERR_SPRAY,
                DeviceError.SELF_ERR_LEVER,
                DeviceError.SELF_ERR_PUSHER,
                DeviceError.SELF_ERR_CLEAN_CONFLICT,
                DeviceError.ERR_DUST_NOT_INSTALL,
                DeviceError.NOTICE_SELF_NOT_PAIRED,
                DeviceError.NOTICE_SELF_BASE_DUST,
                DeviceError.NOTICE_SELF_TEMP_LOW,
                DeviceError.NOTICE_SELF_ROBOT_NOT_COMM,
                DeviceError.NOTICE_SELF_ROBOT_NOT_POS,
                DeviceError.NOTICE_SELF_ROBOT_DUST,
                DeviceError.NOTICE_CLEAN_CLOSED_DUST,
                DeviceError.NOTICE_CLEAN_SPRAY_NOT_POS,
                DeviceError.NOTICE_CLEAN_OPEND_DUST,
                DeviceError.NOTICE_CLEAN_COMM,
                DeviceError.NOTICE_CLEAN_ROBOT_NOT_POS,
                DeviceError.NOTICE_CLEAN_BASE_DUST,
                DeviceError.NOTICE_CLEAN_SPRAY_LEAVE_POS,
                DeviceError.NOTICE_CLEAN_USER_END_EARLY,
                DeviceError.NOTICE_CLEANED_SPRAY_NOT_RESET,
                DeviceError.NOTICE_CLEANED_LEVER_NOT_RESET,
                DeviceError.NOTICE_CLEAN_DRAIN_PUMP_EMPTY,
                DeviceError.NOTICE_CLN_ROBOT_DUST_NOT_POS,
                DeviceError.NOTICE_CLEAN_LEVER_NOT_RESET,
                DeviceError.NOTICE_CLEAN_DONE_NORMAL,
            )
        )
    ),
    ProductCategory.LAWN_MOWER: (),
}


def status_for(category: ProductCategory, raw_status: int) -> DeviceStatus | None:
    """Decode a raw work status for a product category."""
    return STATUS_BY_CATEGORY.get(category, {}).get(raw_status)


def error_for(category: ProductCategory, error_code: int) -> DeviceError | None:
    """Return the first active error for a product category."""
    return next(
        (
            error
            for error, bit in ERROR_BITS_BY_CATEGORY.get(category, ())
            if error_code & bit
        ),
        None,
    )


def error_mask_for(category: ProductCategory, *, include_notices: bool = True) -> int:
    """Return the combined error mask for a product category."""
    return sum(
        bit
        for error, bit in ERROR_BITS_BY_CATEGORY.get(category, ())
        if include_notices or not error.value.startswith("notice_")
    )
