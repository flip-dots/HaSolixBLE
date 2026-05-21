"""Number platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.const import EntityCategory, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from SolixBLE import Solarbank2, SolixBLEDevice

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from . import SolixBLEConfigEntry


SCHEDULE_POWER_UNIQUE_SUFFIX = "output_power_target"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SolixBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the numbers."""

    device = config_entry.runtime_data
    numbers: list[NumberEntity] = []

    if type(device) is Solarbank2:
        numbers.append(SolixSchedulePowerNumberEntity(device))

    async_add_entities(numbers)


class SolixSchedulePowerNumberEntity(NumberEntity, RestoreEntity):
    """Output power target for the Solarbank 2.

    Stores the value the user wants to apply; the actual BLE write is
    performed by the matching Apply button. The device does not report
    the current schedule back, so the value is restored from HA state
    on startup.
    """

    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = 800
    _attr_native_step = 10
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_mode = NumberMode.SLIDER
    _attr_device_class = NumberDeviceClass.POWER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device: SolixBLEDevice) -> None:
        """Initialize the entity."""
        self._device = device
        self._attr_name = "Output Power Target"
        self._attr_unique_id = f"{device.address}_{SCHEDULE_POWER_UNIQUE_SUFFIX}"
        self._attr_device_info = DeviceInfo(
            name=device.name,
            connections={(CONNECTION_BLUETOOTH, device.address)},
        )
        self._attr_native_value = None
        self._attr_available = device.available

    async def async_added_to_hass(self) -> None:
        """Restore last value and subscribe to availability updates."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in ("unknown", "unavailable"):
            try:
                restored = float(last_state.state)
            except (TypeError, ValueError):
                restored = None
            if restored is not None:
                self._attr_native_value = max(
                    self._attr_native_min_value,
                    min(self._attr_native_max_value, restored),
                )

        self._device.add_callback(self._availability_callback)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from device callbacks."""
        self._device.remove_callback(self._availability_callback)

    def _availability_callback(self) -> None:
        """Update availability from device state."""
        self._attr_available = self._device.available
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Store the new value; do not write to the device until Apply is pressed."""
        # Solarbank 2-specific: We snap the native step (10 W) of the slider in the 
        # original Anker app to avoid trouble.
        # If future devices add Number entities, they should decide their own snapping policy.
        step = self._attr_native_step
        snapped = round(value / step) * step
        self._attr_native_value = max(
            self._attr_native_min_value,
            min(self._attr_native_max_value, snapped),
        )
        self.async_write_ha_state()
