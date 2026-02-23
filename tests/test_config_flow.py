"""Test the SolixBLE integration config flow."""

from typing import Union
from unittest.mock import AsyncMock, PropertyMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry

from custom_components.solix_ble.const import DOMAIN

from . import (
    MOCK_C300_DETAILS,
    MOCK_C300X_DETAILS,
    MOCK_C1000_DETAILS,
    MOCK_C1000X_DETAILS,
    MOCK_UNKNOWN_DETAILS,
    BLEDevice,
    MockDeviceDetails,
)
from .conftest import MockConfigEntry


@pytest.mark.parametrize(
    "mock_device_details",
    [
        MOCK_C300_DETAILS,
        MOCK_C300X_DETAILS,
        MOCK_C1000_DETAILS,
        MOCK_C1000X_DETAILS,
        MOCK_UNKNOWN_DETAILS,
    ],
    ids=["c300", "c300x", "c1000", "c1000x", "unknown"],
)
async def test_bluetooth_form(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_device_details: MockDeviceDetails,
) -> None:
    """Test bluetooth discovery form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=mock_device_details.get_service_info(),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        CONF_NAME: mock_device_details.name,
        CONF_MAC: mock_device_details.addr,
    }

    with (
        patch(
            "custom_components.solix_ble.config_flow.async_ble_device_from_address",
            return_value=mock_device_details.get_ble_device(),
        ),
        patch(
            "custom_components.solix_ble.config_flow.async_scanner_count",
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
        result = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"],
            user_input={"device_model": mock_device_details.model_string},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == mock_device_details.name
    assert result["result"].unique_id == device_registry.format_mac(
        mock_device_details.addr
    )
    assert result["result"].data == {"model": mock_device_details.model_class}

    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    "mock_device_details,ble_device,scanner_count,connect,available,error",
    [
        pytest.param(
            MOCK_C300_DETAILS, None, 1, True, True, "not_found", id="not_found"
        ),
        pytest.param(
            MOCK_C300_DETAILS,
            None,
            0,
            True,
            True,
            "no_scanners",
            id="no_scanners",
        ),
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS.get_ble_device(),
            1,
            False,
            True,
            "cannot_connect",
            id="connect_false",
        ),
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS.get_ble_device(),
            1,
            Exception("Something bad!"),
            True,
            "unknown",
            id="connect_exception",
        ),
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS.get_ble_device(),
            1,
            True,
            False,
            "cannot_subscribe",
            id="available_false",
        ),
    ],
)
async def test_bluetooth_form_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_device_details: MockDeviceDetails,
    ble_device: BLEDevice,
    scanner_count: int,
    connect: Union[bool, Exception],
    available: bool,
    error: str,
) -> None:
    """Test bluetooth discovery form when the is a problem."""

    # First we test with a problem
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=mock_device_details.get_service_info(),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        CONF_NAME: mock_device_details.name,
        CONF_MAC: mock_device_details.addr,
    }

    with (
        patch(
            "custom_components.solix_ble.config_flow.async_ble_device_from_address",
            return_value=ble_device,
        ),
        patch(
            "custom_components.solix_ble.config_flow.async_scanner_count",
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
        result = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"],
            user_input={"device_model": mock_device_details.model_string},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": error}

    # Then we test when that problem is gone to make sure it still works
    # and nothing wonky has happened to the internal state
    with (
        patch(
            "custom_components.solix_ble.config_flow.async_ble_device_from_address",
            return_value=mock_device_details.get_ble_device(),
        ),
        patch(
            "custom_components.solix_ble.config_flow.async_scanner_count",
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
        result = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"],
            user_input={"device_model": mock_device_details.model_string},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == mock_device_details.name
    assert result["result"].unique_id == device_registry.format_mac(
        mock_device_details.addr
    )
    assert result["result"].data == {"model": mock_device_details.model_class}

    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_form_exception(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the user form raises a discovery only error."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_implemented"


@pytest.mark.parametrize(
    "mock_setup_entry, mock_config_entry, mock_device_details",
    [
        pytest.param(None, MOCK_C300_DETAILS, MOCK_C300_DETAILS, id="C300"),
        pytest.param(None, MOCK_C1000_DETAILS, MOCK_C1000_DETAILS, id="C1000"),
        pytest.param(None, MOCK_UNKNOWN_DETAILS, MOCK_UNKNOWN_DETAILS, id="Unknown"),
    ],
    indirect=["mock_config_entry"],
)
async def test_bluetooth_form_exception_already_set_up(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
) -> None:
    """Test bluetooth discovery form is aborted when device is already set up."""

    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=mock_device_details.get_service_info(),
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    "mock_config_entry,mock_device_details",
    [
        pytest.param(MOCK_C300_DETAILS, MOCK_C1000_DETAILS, id="c300_and_c1000"),
        pytest.param(MOCK_C300_DETAILS, MOCK_UNKNOWN_DETAILS, id="c300_and_unknown"),
        pytest.param(MOCK_C1000_DETAILS, MOCK_UNKNOWN_DETAILS, id="c1000_and_unknown"),
    ],
    indirect=["mock_config_entry"],
)
async def test_bluetooth_form_multiple_set_up(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
) -> None:
    """Test bluetooth discovery form will let us setup multiple distinct devices."""

    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=mock_device_details.get_service_info(),
    )
    assert (
        result["type"] is FlowResultType.FORM
    ), f"{mock_config_entry} AND {mock_device_details}"
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        CONF_NAME: mock_device_details.name,
        CONF_MAC: mock_device_details.addr,
    }
