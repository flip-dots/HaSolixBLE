"""Test number entities for SolixBLE integration."""

import asyncio
from contextlib import ExitStack
from unittest.mock import patch

import pytest
from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
)

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


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details",
    [pytest.param(MOCK_SOLAR_BANK_2_DETAILS, MOCK_SOLAR_BANK_2_DETAILS, id="sb2")],
    indirect=["mock_config_entry"],
)
async def test_number_entity_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
) -> None:
    """The Output Power Target number is registered for a Solarbank 2 and starts unknown."""
    mock_config_entry.add_to_hass(hass)

    with ExitStack() as stack:
        _enter_device_setup_patches(stack, "Solarbank2", mock_device_details)
        mock_set_schedule = stack.enter_context(
            patch("SolixBLE.Solarbank2.set_schedule")
        )

        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        entity_id = "number.solar_bank_2_output_power_target"
        state = hass.states.get(entity_id)
        assert state is not None, "Expected Output Power Target entity to exist"
        assert state.state == STATE_UNKNOWN
        attrs = state.attributes
        assert attrs["min"] == 0
        assert attrs["max"] == 800
        assert attrs["step"] == 10
        assert attrs["unit_of_measurement"] == "W"
        mock_set_schedule.assert_not_called()


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details",
    [pytest.param(MOCK_SOLAR_BANK_2_DETAILS, MOCK_SOLAR_BANK_2_DETAILS, id="sb2")],
    indirect=["mock_config_entry"],
)
async def test_number_set_value_does_not_call_device(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
) -> None:
    """Setting the number value stores it locally without invoking set_schedule."""
    mock_config_entry.add_to_hass(hass)

    with ExitStack() as stack:
        _enter_device_setup_patches(stack, "Solarbank2", mock_device_details)
        mock_set_schedule = stack.enter_context(
            patch("SolixBLE.Solarbank2.set_schedule")
        )

        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        entity_id = "number.solar_bank_2_output_power_target"

        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: 250},
            blocking=True,
        )

        assert hass.states.get(entity_id).state == "250"
        mock_set_schedule.assert_not_called()


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details,input_value,expected_state",
    [
        pytest.param(
            MOCK_SOLAR_BANK_2_DETAILS, MOCK_SOLAR_BANK_2_DETAILS, 257, "260",
            id="snap_up",
        ),
        pytest.param(
            MOCK_SOLAR_BANK_2_DETAILS, MOCK_SOLAR_BANK_2_DETAILS, 254, "250",
            id="snap_down",
        ),
        pytest.param(
            MOCK_SOLAR_BANK_2_DETAILS, MOCK_SOLAR_BANK_2_DETAILS, 799, "800",
            id="snap_up_at_max_boundary",
        ),
    ],
    indirect=["mock_config_entry"],
)
async def test_number_snaps_to_step(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
    input_value: int,
    expected_state: str,
) -> None:
    """SB2-specific: non-multiple-of-10 inputs are rounded to the nearest 10 W.

    HA's number platform rejects out-of-range values *before* they reach the
    entity, so we only need to verify rounding behavior for in-range inputs
    (including a boundary case where rounding lands on max).

    The snap policy lives in SolixSchedulePowerNumberEntity.async_set_native_value
    and is tied to the SB2 Output Power Target. Future devices that add Number
    entities should make their own snapping decision and have separate tests.
    """
    mock_config_entry.add_to_hass(hass)

    with ExitStack() as stack:
        _enter_device_setup_patches(stack, "Solarbank2", mock_device_details)
        stack.enter_context(patch("SolixBLE.Solarbank2.set_schedule"))

        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        entity_id = "number.solar_bank_2_output_power_target"

        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: input_value},
            blocking=True,
        )

        assert hass.states.get(entity_id).state == expected_state


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details",
    [pytest.param(MOCK_SOLAR_BANK_2_DETAILS, MOCK_SOLAR_BANK_2_DETAILS, id="sb2")],
    indirect=["mock_config_entry"],
)
async def test_number_restores_value(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
) -> None:
    """A previously-saved value is restored on startup via RestoreEntity."""
    mock_config_entry.add_to_hass(hass)

    entity_id = "number.solar_bank_2_output_power_target"
    mock_restore_cache(hass, [State(entity_id, "320")])

    with ExitStack() as stack:
        _enter_device_setup_patches(stack, "Solarbank2", mock_device_details)
        stack.enter_context(patch("SolixBLE.Solarbank2.set_schedule"))

        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == "320.0"


