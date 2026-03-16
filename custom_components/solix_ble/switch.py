"""Switch platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from SolixBLE import C300, C800, C1000, PortStatus, PrimeCharger160w, SolixBLEDevice

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from . import SolixBLEConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SolixBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switches."""

    device = config_entry.runtime_data
    switches: list[SolixSwitchEntity] = []

    # Support for AC output switch with status
    if type(device) in [C300, C800, C1000]:
        switches.append(
            SolixSwitchEntity(
                device,
                "AC Output",
                "ac_output",
                "ac_output",
                "turn_ac_on",
                "turn_ac_off",
            )
        )

    # Support for DC output switch with status
    if type(device) in [C300]:
        switches.append(
            SolixSwitchEntity(
                device,
                "DC Output",
                "dc_output",
                "dc_output",
                "turn_dc_on",
                "turn_dc_off",
            ),
        )

    # Support for DC output switch without status
    if type(device) in [C800, C1000]:
        switches.append(
            SolixSwitchEntity(
                device,
                "DC Output",
                "dc_output",
                None,
                "turn_dc_on",
                "turn_dc_off",
            ),
        )

    # Support for display on/off switch without status
    if type(device) in [C300, C800, C1000]:
        switches.append(
            SolixSwitchEntity(
                device,
                "Display",
                "display_on_off",
                None,
                "turn_display_on",
                "turn_display_off",
            ),
        )

    # Support for controlling USB Port C1
    if type(device) in [PrimeCharger160w]:
        switches.append(
            SolixSwitchEntity(
                device,
                "USB Port C1",
                "usb_port_c1",
                "usb_port_c1",
                "turn_usb_c1_on",
                "turn_usb_c1_off",
            ),
        )

    # Support for controlling USB Port C2
    if type(device) in [PrimeCharger160w]:
        switches.append(
            SolixSwitchEntity(
                device,
                "USB Port C2",
                "usb_port_c2",
                "usb_port_c2",
                "turn_usb_c2_on",
                "turn_usb_c2_off",
            ),
        )

    # Support for controlling USB Port C3
    if type(device) in [PrimeCharger160w]:
        switches.append(
            SolixSwitchEntity(
                device,
                "USB Port C3",
                "usb_port_c3",
                "usb_port_c3",
                "turn_usb_c3_on",
                "turn_usb_c3_off",
            ),
        )

    async_add_entities(switches)


class SolixSwitchEntity(SwitchEntity):
    """Representation of a device."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        device: SolixBLEDevice,
        name: str,
        attribute: str,
        state_attribute: str | None,
        on_function_attribute: str,
        off_function_attribute: str,
    ) -> None:
        """Initialize the device object. Does not connect.

        :param device: The device API object.
        :param name: Name of the switch entity.
        :param attribute: Attribute used in unique ID generation.
        :param state_attribute: Name of function in API object to determine state.
        :param on_function_attribute: Name of function in API object to turn switch on.
        :param off_function_attribute: Name of function in API object to turn switch off.
        """
        self._device = device
        self._address = device.address
        self._state_attribute = state_attribute
        self._on_function = getattr(device, on_function_attribute)
        self._off_function = getattr(device, off_function_attribute)

        self._attr_name = name
        self._attr_unique_id = f"{device.address}_{attribute}"
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

        if self._state_attribute is not None:
            state = getattr(self._device, self._state_attribute)

            if type(state) is PortStatus:
                if state is PortStatus.UNKNOWN:
                    self._attr_is_on = None
                elif state is PortStatus.NOT_CONNECTED:
                    self._attr_is_on = False
                elif state is PortStatus.OUTPUT:
                    self._attr_is_on = True
                else:
                    raise RuntimeError(
                        f"Unexpected port status '{state}' with type '{type(state)}'!"
                    )
            else:
                self._attr_is_on = state

    def _state_change_callback(self) -> None:
        """Run when device informs of state update. Updates local properties."""
        _LOGGER.debug("Received state notification from device %s", self.name)
        self._update_updatable_attributes()
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self._on_function()

    async def async_turn_off(self, **kwargs):
        """Turn the entity on."""
        await self._off_function()
