"""Test sensor for SolixBLE integration."""

import asyncio
from contextlib import ExitStack
from datetime import datetime
from typing import Any, Tuple, Union
from unittest.mock import PropertyMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from SolixBLE import LightStatus, PortStatus

from custom_components.solix_ble.const import DOMAIN

from . import (
    MOCK_C300_DETAILS,
    MOCK_C300_TEST_DATA,
    MOCK_C1000_DETAILS,
    MOCK_C1000_TEST_DATA,
    MOCK_UNKNOWN_DETAILS,
    MOCK_UNKNOWN_TEST_DATA,
    MockDeviceDetails,
)


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details,class_name,test_data",
    [
        pytest.param(
            MOCK_C300_DETAILS, MOCK_C300_DETAILS, "C300", MOCK_C300_TEST_DATA, id="c300"
        ),
        pytest.param(
            MOCK_C1000_DETAILS,
            MOCK_C1000_DETAILS,
            "C1000",
            MOCK_C1000_TEST_DATA,
            id="c1000",
        ),
        pytest.param(
            MOCK_UNKNOWN_DETAILS,
            MOCK_UNKNOWN_DETAILS,
            "Generic",
            MOCK_UNKNOWN_TEST_DATA,
            id="unknown",
        ),
    ],
    indirect=["mock_config_entry"],
)
async def test_sensor_entities(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
    class_name: str,
    test_data: dict[str, Union[Tuple[str, Any], Any]],
) -> None:
    """Test that the entities are added and show the expected values."""

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
            f"SolixBLE.{class_name}.connect",
            side_effect=[True],
        ),
        patch(
            f"SolixBLE.{class_name}.available",
            side_effect=[True],
        ),
        ExitStack() as dynamic_context,
    ):

        # We dynamically patch all of the sensor entities in the test data
        for key, value in test_data.items():
            dynamic_context.enter_context(
                patch(
                    f"SolixBLE.{class_name}.{key}",
                    new_callable=PropertyMock,
                    return_value=(value[1] if type(value) is tuple else value),
                )
            )

        # Set up the integration
        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        # Check that the entities exist and are showing what we expect
        for key, value in test_data.items():

            # If the entity ID is manually specified use that rather
            # than using the method name of the underlying class
            if type(value) is tuple:
                key = value[0]
                value = value[1]

            # There are not enough words in the universe to express how
            # much I hate timezones
            if type(value) is datetime:
                value = f"{value.strftime("%Y-%m-%dT%H:%M:%S")}+00:00"

            # If the value is a port or light status then we format
            # its name to get the correct value that HA will have
            elif type(value) is PortStatus or type(value) is LightStatus:
                value = value.name.capitalize().replace("_", " ")

            else:
                value = f"{value}"

            # Calculate entity ID and get value
            entity_id = (
                f"sensor.{ mock_config_entry.title.lower().replace(" ", "_")}_{key}"
            )
            entity = hass.states.get(entity_id)

            # Check that entity ID exists
            assert (
                entity is not None
            ), f"Expected to find '{value}' at '{entity_id}' but instead got None!"

            # Check that entities state matches what we expect
            assert (
                f"{entity.state}" == value
            ), f"Expected to find '{value}' at '{entity_id}' but instead the entity was '{entity.state}'!"
