"""Number platform."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from SolixBLE import F2000Old, SolixBLEDevice

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from . import SolixBLEConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SolixBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the numbers."""

    device = config_entry.runtime_data
    numbers: list[SolixNumberEntity] = []

    if type(device) in [F2000Old]:
        numbers.append(
            SolixNumberEntity(
                device=device,
                name="Screen Timeout",
                attribute="screen_timeout",
                minimum=0,
                maximum=65535,
                step=1,
                unit="s",
                action=device.set_screen_timeout,
            )
        )

    async_add_entities(numbers)


class SolixNumberEntity(NumberEntity):
    """Representation of a numeric device setting."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device: SolixBLEDevice,
        name: str,
        attribute: str,
        minimum: float,
        maximum: float,
        step: float,
        unit: str | None,
        action: Callable[[int], Awaitable[None]],
    ) -> None:
        """Initialize the number entity.

        :param device: The device API object.
        :param name: Home Assistant entity name.
        :param attribute: Device attribute containing the current value.
        :param minimum: Minimum allowed value.
        :param maximum: Maximum allowed value.
        :param step: Value increment.
        :param unit: Unit of measurement.
        :param action: Async device method used to set the value.
        """
        self._device = device
        self._attribute_name = attribute
        self._action = action

        self._attr_name = name
        self._attr_unique_id = f"{device.address}_{attribute}"
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit

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
        self._attr_native_value = getattr(self._device, self._attribute_name)

    def _state_change_callback(self) -> None:
        """Run when device informs of state update. Updates local properties."""
        _LOGGER.debug("Received state notification from device %s", self.name)
        self._update_updatable_attributes()
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Change the value."""
        await self._action(int(value))