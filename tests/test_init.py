"""Test SolixBLE setup process."""

import asyncio
from datetime import timedelta
from unittest.mock import PropertyMock, patch

import pytest
from bleak.backends.device import BLEDevice
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.solix_ble.const import DOMAIN

from . import MOCK_C300_DETAILS, MOCK_UNKNOWN_DETAILS, MockDeviceDetails
from .conftest import MockConfigEntry


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details",
    [
        pytest.param(MOCK_C300_DETAILS, MOCK_C300_DETAILS, id="c300"),
    ],
    indirect=["mock_config_entry"],
)
async def test_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
) -> None:
    """Test that the config is loaded if there are no errors."""

    mock_config_entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.solix_ble.async_ble_device_from_address",
            return_value=mock_device_details.get_ble_device(),
        ),
        patch(
            "custom_components.solix_ble.async_scanner_count",
            return_value=1,
        ),
        patch(
            "SolixBLE.SolixBLEDevice.connect",
            side_effect=[True],
        ),
        patch(
            "SolixBLE.SolixBLEDevice.available",
            side_effect=[True],
        ),
    ):
        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        assert mock_config_entry.state is ConfigEntryState.LOADED


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details,ble_device,scanner_count,connect,available,error",
    [
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS,
            None,
            1,
            True,
            True,
            "The device was not found",
            id="not_found",
        ),
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS,
            None,
            0,
            True,
            True,
            "No Bluetooth scanners",
            id="no_scanners",
        ),
        pytest.param(
            MOCK_UNKNOWN_DETAILS,
            MOCK_UNKNOWN_DETAILS,
            MOCK_UNKNOWN_DETAILS.get_ble_device(),
            1,
            False,
            True,
            f"'{MOCK_UNKNOWN_DETAILS.name}' is not supported",
            id="unsupported_warning",
        ),
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS.get_ble_device(),
            1,
            False,
            True,
            "Device found but unable to connect",
            id="connect_false",
        ),
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS.get_ble_device(),
            1,
            Exception("Something went wrong"),
            True,
            "Unexpected exception when connecting to device",
            id="connect_exception",
        ),
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS.get_ble_device(),
            1,
            True,
            False,
            "Device connected but unable to subscribe to telemetry",
            id="available_false",
        ),
    ],
    indirect=["mock_config_entry"],
)
async def test_setup_error(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
    ble_device: BLEDevice | None,
    scanner_count: int,
    connect: Exception | bool,
    available: bool,
    error: str,
) -> None:
    """Test that ConfigEntryNotReady is raised if there is an error condition."""

    # First we test with a problem
    mock_config_entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.solix_ble.async_ble_device_from_address",
            return_value=ble_device,
        ),
        patch(
            "custom_components.solix_ble.async_scanner_count",
            return_value=scanner_count,
        ),
        patch(
            "SolixBLE.SolixBLEDevice.connect",
            side_effect=[connect],
        ),
        patch(
            "SolixBLE.SolixBLEDevice.available",
            new_callable=PropertyMock,
            return_value=available,
        ),
    ):
        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
        assert error in caplog.text

    # Then we test when that problem is gone to make sure it still works
    # and nothing wonky has happened to the internal state
    with (
        patch(
            "custom_components.solix_ble.async_ble_device_from_address",
            return_value=mock_device_details.get_ble_device(),
        ),
        patch(
            "custom_components.solix_ble.async_scanner_count",
            return_value=1,
        ),
        patch(
            "SolixBLE.SolixBLEDevice.connect",
            side_effect=[True],
        ),
        patch(
            "SolixBLE.SolixBLEDevice.available",
            side_effect=[True],
        ),
    ):
        # Try again
        next_retry = dt.utcnow() + timedelta(seconds=150)  # Default initial backoff
        async_fire_time_changed(hass, next_retry)
        await hass.async_block_till_done()
        await asyncio.sleep(0.2)
        assert mock_config_entry.state is ConfigEntryState.LOADED
