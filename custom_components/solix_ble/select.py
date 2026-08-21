"""Select platform."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
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


LIGHT_MODE_BY_OPTION = {
    "Off": LightStatus.OFF,
    "Low": LightStatus.LOW,
    "Medium": LightStatus.MEDIUM,
    "High": LightStatus.HIGH,
    "SOS": LightStatus.SOS,
}

SCREEN_BRIGHTNESS_BY_OPTION = {
    "Off": LightStatus.OFF,
    "Low": LightStatus.LOW,
    "Medium": LightStatus.MEDIUM,
    "High": LightStatus.HIGH,
}

RECHARD_POWER_BY_OPTION = {
    "200W": 200,
    "300W": 300,
    "400W": 400,
    "500W": 500,
    "600W": 600,
    "750W": 750,
    "1440W": 1440,
    "Silent": 749,
    "High Speed": 1439,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SolixBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the selects."""

    device = config_entry.runtime_data
    selects: list[SolixSelectEntity] = []

    if type(device) in [F2000Old]:
        selects.append(
            SolixSelectEntity(
                device=device,
                name="Light Mode",
                unique_id_suffix="light_mode",
                attribute="light",
                options=LIGHT_MODE_BY_OPTION,
                action=device.set_light_mode,
            )
        )

    if type(device) in [F2000Old]:
        selects.append(
            SolixSelectEntity(
                device=device,
                name="Screen Brightness",
                unique_id_suffix="screen_brightness",
                attribute="screen_brightness",
                options=SCREEN_BRIGHTNESS_BY_OPTION,
                action=device.set_screen_brightness,
            )
        )

    if type(device) in [F2000Old]:
        selects.append(
            SolixSelectEntity(
                device=device,
                name="AC Power Input Limit",
                unique_id_suffix="ac_power_input_limit",
                attribute="ac_power_in_limit",
                options=RECHARD_POWER_BY_OPTION,
                action=device.set_ac_power_in_limit,
            )
        )

    async_add_entities(selects)


class SolixSelectEntity(SelectEntity):
    """Representation of a LightStatus-backed select."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device: SolixBLEDevice,
        name: str,
        unique_id_suffix: str,
        attribute: str,
        options: dict[str, LightStatus],
        action: Callable[[LightStatus], Awaitable[None]],
    ) -> None:
        """Initialize the select. Does not connect.

        :param device: The device API object.
        :param name: Home Assistant entity name.
        :param unique_id_suffix: Unique ID suffix for this entity.
        :param attribute: Device attribute containing the current state.
        :param options: Mapping of Home Assistant option strings to LightStatus.
        :param action: Async device method used to set the value.
        """
        self._device = device
        self._attribute_name = attribute
        self._option_by_status = {
            status: option for option, status in options.items()
        }
        self._status_by_option = options
        self._action = action

        self._attr_name = name
        self._attr_unique_id = f"{device.address}_{unique_id_suffix}"
        self._attr_options = list(options)

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
        """Update this entity's updatable attrs from the device state."""
        self._attr_available = self._device.available

        status = getattr(self._device, self._attribute_name)
        self._attr_current_option = self._option_by_status.get(status)

    def _state_change_callback(self) -> None:
        """Run when device informs of state update. Updates local properties."""
        _LOGGER.debug("Received state notification from device %s", self.name)
        self._update_updatable_attributes()
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._action(self._status_by_option[option])
