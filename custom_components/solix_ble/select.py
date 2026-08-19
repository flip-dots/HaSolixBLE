"""Select platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from SolixBLE import F2000Old, SolixBLEDevice
from SolixBLE.states import LightStatus

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from . import SolixBLEConfigEntry

#: Ordered to match LightStatus's declaration order (UNKNOWN excluded - not
#: a settable option, matches F2000Old.set_light_mode() rejecting it).
LIGHT_MODE_OPTIONS = ["Off", "Low", "Medium", "High", "SOS"]
_LIGHT_MODE_BY_OPTION = {
    "Off": LightStatus.OFF,
    "Low": LightStatus.LOW,
    "Medium": LightStatus.MEDIUM,
    "High": LightStatus.HIGH,
    "SOS": LightStatus.SOS,
}

_LIGHT_MODE_BY_STATUS = {
    status: option for option, status in _LIGHT_MODE_BY_OPTION.items()
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SolixBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the selects."""

    device = config_entry.runtime_data
    selects: list[SolixLightModeSelectEntity] = []

    if type(device) in [F2000Old]:
        selects.append(SolixLightModeSelectEntity(device))

    async_add_entities(selects)


class SolixLightModeSelectEntity(SelectEntity):
    """Light bar mode control, backed by set_light_mode()/light."""

    _attr_has_entity_name = True
    _attr_name = "Light Mode"
    _attr_options = LIGHT_MODE_OPTIONS

    def __init__(self, device: SolixBLEDevice) -> None:
        """Initialize the select. Does not connect.

        :param device: The device API object.
        """
        self._device = device
        self._attr_unique_id = f"{device.address}_light_mode"
        self._attr_device_info = DeviceInfo(
            name=device.name,
            connections={(CONNECTION_BLUETOOTH, device.address)},
        )
        self._update_updatable_attributes()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._device.add_callback(self._state_change_callback)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from HA."""
        self._device.remove_callback(self._state_change_callback)

    def _update_updatable_attributes(self) -> None:
        """Update this entities updatable attrs from the devices state."""
        self._attr_available = self._device.available
        self._attr_current_option = _LIGHT_MODE_BY_STATUS.get(self._device.light)

    def _state_change_callback(self) -> None:
        """Run when device informs of state update. Updates local properties."""
        _LOGGER.debug("Received state notification from device %s", self.name)
        self._update_updatable_attributes()
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._device.set_light_mode(_LIGHT_MODE_BY_OPTION[option])
