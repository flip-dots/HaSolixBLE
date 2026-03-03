"""Test switches for SolixBLE integration."""

import asyncio
from contextlib import nullcontext
from typing import Any, Union
from unittest.mock import PropertyMock, patch

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from SolixBLE import PortStatus, SolixBLEDevice
from sqlalchemy import union

from custom_components.solix_ble.const import DOMAIN

from . import MOCK_C300_DETAILS, MOCK_C1000_DETAILS, MockDeviceDetails


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details,class_name,attribute,state_attribute,on_attribute,off_attribute,on_off_sequence",
    [
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS,
            "C300",
            "ac_output",
            "ac_output",
            "turn_ac_on",
            "turn_ac_off",
            (PortStatus.NOT_CONNECTED, PortStatus.OUTPUT, PortStatus.NOT_CONNECTED),
            id="c300_ac",
        ),
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS,
            "C300",
            "dc_output",
            "dc_output",
            "turn_dc_on",
            "turn_dc_off",
            (PortStatus.NOT_CONNECTED, PortStatus.OUTPUT, PortStatus.NOT_CONNECTED),
            id="c300_dc",
        ),
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS,
            "C300",
            "display",
            None,
            "turn_display_on",
            "turn_display_off",
            None,
            id="c300_display",
        ),
        pytest.param(
            MOCK_C1000_DETAILS,
            MOCK_C1000_DETAILS,
            "C1000",
            "ac_output",
            "ac_output",
            "turn_ac_on",
            "turn_ac_off",
            (PortStatus.NOT_CONNECTED, PortStatus.OUTPUT, PortStatus.NOT_CONNECTED),
            id="c1000_ac",
        ),
        pytest.param(
            MOCK_C1000_DETAILS,
            MOCK_C1000_DETAILS,
            "C1000",
            "dc_output",
            None,
            "turn_dc_on",
            "turn_dc_off",
            (PortStatus.NOT_CONNECTED, PortStatus.OUTPUT, PortStatus.NOT_CONNECTED),
            id="c1000_dc",
        ),
        pytest.param(
            MOCK_C1000_DETAILS,
            MOCK_C1000_DETAILS,
            "C1000",
            "display",
            None,
            "turn_display_on",
            "turn_display_off",
            None,
            id="c1000_display",
        ),
    ],
    indirect=["mock_config_entry"],
)
async def test_switch_entities(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
    class_name: str,
    attribute: str,
    state_attribute: str | None,
    on_attribute: str,
    off_attribute: str,
    on_off_sequence: Union[tuple[Any, Any, Any], None],
) -> None:
    """
    Test that the entities are added and show the expected values.

    :param on_off_sequence: The sequence of values that will be sent to the switch entity to represent its changing state.
    """

    mock_config_entry.add_to_hass(hass)

    captured_self: SolixBLEDevice = None

    def connect_side_effect(
        self: SolixBLEDevice,
    ):
        """We use this to capture the device object so we can run callbacks on it."""
        nonlocal captured_self
        captured_self = self
        return True

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
            f"SolixBLE.{class_name}.connect",
            autospec=True,
            side_effect=connect_side_effect,
        ),
        patch(
            f"SolixBLE.{class_name}.connected",
            side_effect=[True],
        ),
        patch(
            f"SolixBLE.{class_name}.connected",
            side_effect=[True],
        ),
        patch(
            f"SolixBLE.{class_name}.negotiated",
            side_effect=[True],
        ),
        patch(
            "SolixBLE.SolixBLEDevice.available",
            side_effect=[True],
        ),
        (
            patch(f"SolixBLE.{class_name}.{state_attribute}", new_callable=PropertyMock)
            if state_attribute
            else nullcontext()
        ) as mock_state_attribute,
        patch(f"SolixBLE.{class_name}.{on_attribute}") as mock_on_function,
        patch(f"SolixBLE.{class_name}.{off_attribute}") as mock_off_function,
    ):

        # Set up the integration
        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        # Calculate entity ID
        entity_id = (
            f"switch.{ mock_config_entry.title.lower().replace(" ", "_")}_{attribute}"
        )

        # If we have a state attribute we should start in the off position
        if state_attribute:
            mock_state_attribute.return_value = on_off_sequence[0]
            captured_self._run_state_changed_callbacks()
            await hass.async_block_till_done()

            assert (
                hass.states.get(entity_id).state == STATE_OFF
            ), "Expected initial state to be off!"

        # Else we should start in the unknown position
        else:
            assert (
                hass.states.get(entity_id).state == STATE_UNKNOWN
            ), "Expected initial state to be unknown!"

        # Turn on
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_on_function.assert_called_once()

        # If we have a state attribute it should now be in the on position
        if state_attribute:
            mock_state_attribute.return_value = on_off_sequence[1]
            captured_self._run_state_changed_callbacks()

            assert (
                hass.states.get(entity_id).state == STATE_ON
            ), "Expected new state to be on!"

        # Else it should remain in unknown position
        else:
            assert (
                hass.states.get(entity_id).state == STATE_UNKNOWN
            ), "Expected state to remain unknown!"

        # Turn off
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_off_function.assert_called_once()

        # If we have a state attribute it should now be in the off position
        if state_attribute:
            mock_state_attribute.return_value = on_off_sequence[2]
            captured_self._run_state_changed_callbacks()

            assert (
                hass.states.get(entity_id).state == STATE_OFF
            ), "Expected final state to be off!"

        # Else it should remain in unknown position
        else:
            assert (
                hass.states.get(entity_id).state == STATE_UNKNOWN
            ), "Expected final state to remain unknown!"
