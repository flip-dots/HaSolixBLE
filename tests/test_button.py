"""Test the Apply button for SolixBLE Solarbank 2."""

import asyncio
from contextlib import ExitStack
from unittest.mock import patch

import pytest
from homeassistant.components.button import (
    DOMAIN as BUTTON_DOMAIN,
    SERVICE_PRESS,
)
from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solix_ble.const import DOMAIN

from . import (
    MOCK_SOLAR_BANK_2_DETAILS,
    MockDeviceDetails,
)


def _enter_device_setup_patches(stack: ExitStack, class_name: str, mock_device_details):
    """Enter the standard set of patches that bring the integration up."""
    stack.enter_context(
        patch(
            "custom_components.solix_ble.async_ble_device_from_address",
            return_value=mock_device_details.get_ble_device(),
        )
    )
    stack.enter_context(
        patch("custom_components.solix_ble.async_scanner_count", return_value=1)
    )
    stack.enter_context(
        patch(f"SolixBLE.{class_name}.connect", autospec=True, return_value=True)
    )
    stack.enter_context(patch(f"SolixBLE.{class_name}.connected", side_effect=[True]))
    stack.enter_context(patch(f"SolixBLE.{class_name}.connected", side_effect=[True]))
    stack.enter_context(patch(f"SolixBLE.{class_name}.negotiated", side_effect=[True]))
    stack.enter_context(
        patch("SolixBLE.SolixBLEDevice.available", side_effect=[True])
    )


NUMBER_ENTITY_ID = "number.solar_bank_2_output_power_target"
BUTTON_ENTITY_ID = "button.solar_bank_2_apply_power_target"


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details",
    [pytest.param(MOCK_SOLAR_BANK_2_DETAILS, MOCK_SOLAR_BANK_2_DETAILS, id="sb2")],
    indirect=["mock_config_entry"],
)
async def test_apply_button_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
) -> None:
    """The Apply button is registered for a Solarbank 2."""
    mock_config_entry.add_to_hass(hass)

    with ExitStack() as stack:
        _enter_device_setup_patches(stack, "Solarbank2", mock_device_details)
        stack.enter_context(patch("SolixBLE.Solarbank2.set_schedule"))

        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        assert hass.states.get(BUTTON_ENTITY_ID) is not None


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details",
    [pytest.param(MOCK_SOLAR_BANK_2_DETAILS, MOCK_SOLAR_BANK_2_DETAILS, id="sb2")],
    indirect=["mock_config_entry"],
)
async def test_apply_button_calls_set_schedule(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
) -> None:
    """Pressing Apply sends the current Number value via set_schedule."""
    mock_config_entry.add_to_hass(hass)

    with ExitStack() as stack:
        _enter_device_setup_patches(stack, "Solarbank2", mock_device_details)
        mock_set_schedule = stack.enter_context(
            patch("SolixBLE.Solarbank2.set_schedule")
        )

        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: NUMBER_ENTITY_ID, ATTR_VALUE: 250},
            blocking=True,
        )

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: BUTTON_ENTITY_ID},
            blocking=True,
        )

        mock_set_schedule.assert_called_once_with(power_w=250)


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details",
    [pytest.param(MOCK_SOLAR_BANK_2_DETAILS, MOCK_SOLAR_BANK_2_DETAILS, id="sb2")],
    indirect=["mock_config_entry"],
)
async def test_apply_button_raises_when_number_unset(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
) -> None:
    """Pressing Apply before setting the Number raises and does not call the device."""
    mock_config_entry.add_to_hass(hass)

    with ExitStack() as stack:
        _enter_device_setup_patches(stack, "Solarbank2", mock_device_details)
        mock_set_schedule = stack.enter_context(
            patch("SolixBLE.Solarbank2.set_schedule")
        )

        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: BUTTON_ENTITY_ID},
                blocking=True,
            )

        mock_set_schedule.assert_not_called()


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details,raised_exception",
    [
        pytest.param(
            MOCK_SOLAR_BANK_2_DETAILS,
            MOCK_SOLAR_BANK_2_DETAILS,
            ConnectionError("not connected"),
            id="connection_error",
        ),
        pytest.param(
            MOCK_SOLAR_BANK_2_DETAILS,
            MOCK_SOLAR_BANK_2_DETAILS,
            ValueError("power_w must be 0-800 W"),
            id="value_error",
        ),
    ],
    indirect=["mock_config_entry"],
)
async def test_apply_button_wraps_library_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
    raised_exception: Exception,
) -> None:
    """Library errors from set_schedule surface as HomeAssistantError."""
    mock_config_entry.add_to_hass(hass)

    with ExitStack() as stack:
        _enter_device_setup_patches(stack, "Solarbank2", mock_device_details)
        stack.enter_context(
            patch(
                "SolixBLE.Solarbank2.set_schedule",
                side_effect=raised_exception,
            )
        )

        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: NUMBER_ENTITY_ID, ATTR_VALUE: 100},
            blocking=True,
        )

        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: BUTTON_ENTITY_ID},
                blocking=True,
            )


