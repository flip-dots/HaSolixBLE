"""Button platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from SolixBLE import Solarbank2, SolixBLEDevice

from .const import DOMAIN
from .number import SCHEDULE_POWER_UNIQUE_SUFFIX

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from . import SolixBLEConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SolixBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the buttons."""

    device = config_entry.runtime_data
    buttons: list[ButtonEntity] = []

    if type(device) is Solarbank2:
        buttons.append(SolixApplyScheduleButtonEntity(device))

    async_add_entities(buttons)


class SolixApplyScheduleButtonEntity(ButtonEntity):
    """Apply the staged Output Power Target to a Solarbank 2 via set_schedule()."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device: SolixBLEDevice) -> None:
        """Initialize the entity."""
        self._device = device
        self._number_unique_id = f"{device.address}_{SCHEDULE_POWER_UNIQUE_SUFFIX}"
        self._attr_name = "Apply"
        self._attr_unique_id = f"{device.address}_apply_schedule"
        self._attr_device_info = DeviceInfo(
            name=device.name,
            connections={(CONNECTION_BLUETOOTH, device.address)},
        )
        self._attr_available = device.available

    async def async_added_to_hass(self) -> None:
        """Subscribe to availability updates."""
        await super().async_added_to_hass()
        self._device.add_callback(self._availability_callback)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from device callbacks."""
        self._device.remove_callback(self._availability_callback)

    def _availability_callback(self) -> None:
        """Update availability from device state."""
        self._attr_available = self._device.available
        self.async_write_ha_state()

    async def async_press(self) -> None:
        """Send the current Output Power Target value to the device."""
        registry = er.async_get(self.hass)
        number_entity_id = registry.async_get_entity_id(
            NUMBER_DOMAIN, DOMAIN, self._number_unique_id
        )
        if number_entity_id is None:
            raise HomeAssistantError(
                "Output Power Target entity is not registered yet"
            )

        state = self.hass.states.get(number_entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            raise HomeAssistantError("Output Power Target is not set")

        try:
            power_w = int(round(float(state.state)))
        except (TypeError, ValueError) as err:
            raise HomeAssistantError(
                f"Output Power Target has an invalid value: {state.state!r}"
            ) from err

        try:
            await self._device.set_schedule(power_w=power_w)
        except (ConnectionError, ValueError) as err:
            raise HomeAssistantError(str(err)) from err

        _LOGGER.debug("set_schedule(%d W) sent to %s", power_w, self._device.name)
