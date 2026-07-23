"""Tests for typed Beatbot protocol mappings."""

from beatbot_cloud import (
    DeviceError,
    DeviceStatus,
    ProductCategory,
    error_mask_for,
    status_for,
)


def test_status_mapping_is_category_specific():
    assert status_for(ProductCategory.POOL_CLEAN_BOT, 0) is DeviceStatus.STANDBY
    assert status_for(ProductCategory.CLEAN_BASE_STATION, 0) is DeviceStatus.CLEANING
    assert status_for(ProductCategory.POOL_CLEAN_BOT, 999) is None


def test_clean_base_error_mask_can_exclude_notices():
    all_errors = error_mask_for(ProductCategory.CLEAN_BASE_STATION)
    faults_only = error_mask_for(
        ProductCategory.CLEAN_BASE_STATION, include_notices=False
    )

    assert all_errors > faults_only
    assert faults_only & (1 << 0)
    assert not faults_only & (1 << 5)
    assert DeviceError.SELF_ERR_SPRAY.value == "self_err_spray"
