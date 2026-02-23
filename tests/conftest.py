"""Common fixtures for the Solix BLE tests."""

import logging
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solix_ble.const import DOMAIN

from . import MockDeviceDetails

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def mock_bluetooth_dependency(hass):
    """Auto-mock bluetooth and bluetooth_adapters dependencies."""
    # This mock prevents 'bluetooth_adapters' from failing during setup
    with patch(
        "homeassistant.components.bluetooth_adapters.async_setup", return_value=True
    ), patch("homeassistant.components.bluetooth.async_setup", return_value=True):
        hass.config.components.add("bluetooth")
        hass.config.components.add("bluetooth_adapters")


@pytest.fixture(autouse=True)
def mock_bluetooth(enable_bluetooth: None):
    """Auto mock bluetooth."""


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.solix_ble.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry(request: MockDeviceDetails) -> MockConfigEntry:
    """Create a mock config entry."""
    _LOGGER.debug(f"Creating mock config entry using: {request.param}")
    assert type(request.param) is MockDeviceDetails
    return MockConfigEntry(
        domain=DOMAIN,
        title=request.param.name,
        unique_id=request.param.addr.lower(),
        data={"model": request.param.model_class},
    )
