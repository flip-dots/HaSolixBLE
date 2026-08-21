"""Button platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from collections.abc import Awaitable, Callable

from homeassistant.components.button import ButtonEntity
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
    """Set up the buttons."""

    device = config_entry.runtime_data
    buttons: list[SolixButtonEntity] = []

    if type(device) in [F2000Old]:
        buttons.append(
            SolixButtonEntity(
                device,
                name="Request Extended Data",
                unique_id_suffix="request_extended_data",
                action=device.send_poll_extended,
            )
        )

    async_add_entities(buttons)


class SolixButtonEntity(ButtonEntity):
    """Representation of a device button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device: SolixBLEDevice,
        name: str,
        unique_id_suffix: str,
        action: Callable[[], Awaitable[None]],
    ) -> None:
        """Initialize the button."""

        self._device = device
        self._action = action

        self._attr_name = name
        self._attr_unique_id = f"{device.address}_{unique_id_suffix}"
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
        """Update entity attributes from the device state."""
        self._attr_available = self._device.available

    def _state_change_callback(self) -> None:
        """Run when device informs of state update."""
        self._update_updatable_attributes()
        self.async_write_ha_state()

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._action()