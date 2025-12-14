"""sensor platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from SolixBLE import SolixBLEDevice, C300, C1000, Generic

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util.dt import as_local

from .const import LIGHT_STATUS_STRINGS, PORT_STATUS_STRINGS

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from . import SolixBLEConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SolixBLEConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Sensors."""

    device = config_entry.runtime_data
    sensors = []

    # Common sensors
    if any(x in device.name for x in ["C300X", "C1000"]):
        sensors.append(
            SolixSensorEntity(
                device, "AC Timer", None, "ac_timer", SensorDeviceClass.TIMESTAMP
            )
        )
        sensors.append(
            SolixSensorEntity(device, "Remaining Hours", "hours", "hours_remaining"),
        )
        sensors.append(
            SolixSensorEntity(device, "Remaining Days", "days", "days_remaining"),
        )
        sensors.append(
            SolixSensorEntity(device, "Remaining Time", "hours", "time_remaining"),
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "Timestamp Remaining",
                None,
                "timestamp_remaining",
                SensorDeviceClass.TIMESTAMP,
            )
        ),
        sensors.append(
            SolixSensorEntity(
                device,
                "AC Power In",
                "W",
                "ac_power_in",
                SensorDeviceClass.POWER,
            )
        ),
        sensors.append(
            SolixSensorEntity(
                device,
                "AC Power Out",
                "W",
                "ac_power_out",
                SensorDeviceClass.POWER,
            )
        ),
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C1 Power",
                "W",
                "usb_c1_power",
                SensorDeviceClass.POWER,
            )
        ),
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C2 Power",
                "W",
                "usb_c2_power",
                SensorDeviceClass.POWER,
            )
        ),
        sensors.append(
            SolixSensorEntity(
                device, "USB A1 Power", "W", "usb_a1_power", SensorDeviceClass.POWER
            )
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "Solar Power In",
                "W",
                "solar_power_in",
                SensorDeviceClass.POWER,
            )
        )
        sensors.append(
            SolixSensorEntity(
                device, "Total Power In", "W", "power_in", SensorDeviceClass.POWER
            )
        ),
        sensors.append(
            SolixSensorEntity(
                device, "Total Power Out", "W", "power_out", SensorDeviceClass.POWER
            )
        ),
        sensors.append(
            SolixSensorEntity(
                device,
                "Battery Percentage",
                "%",
                "battery_percentage",
                SensorDeviceClass.BATTERY,
            )
        )

    # C300X only sensors
    if any(x in device.name for x in ["C300X"]):
        sensors.append(
            SolixSensorEntity(
                device, "DC Timer", None, "dc_timer", SensorDeviceClass.TIMESTAMP
            )
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C3 Power",
                "W",
                "usb_c3_power",
                SensorDeviceClass.POWER,
            )
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "DC Power Out",
                "W",
                "dc_power_out",
                SensorDeviceClass.POWER,
            )
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "Status Solar",
                None,
                "solar_port",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
            )
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "Status USB C1",
                None,
                "usb_port_c1",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
            )
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "Status USB C2",
                None,
                "usb_port_c2",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
            )
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "Status USB C3",
                None,
                "usb_port_c3",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
            )
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "Status USB A1",
                None,
                "usb_port_a1",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
            )
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "Status DC Out",
                None,
                "dc_port",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
            )
        )
        sensors.append(
            SolixSensorEntity(
                device,
                "Status Light",
                None,
                "light",
                SensorDeviceClass.ENUM,
                LIGHT_STATUS_STRINGS,
            )
        )

    # C1000 only sensors
    if any(x in device.name for x in ["C1000"]):
        SolixSensorEntity(
            device, "USB A2 Power", "W", "usb_a2_power", SensorDeviceClass.POWER
        ),

    async_add_entities(sensors)


class SolixSensorEntity(SensorEntity):
    """Representation of a device."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        device: SolixBLEDevice,
        name: str,
        unit: str,
        attribute: str,
        device_class: SensorDeviceClass | None = None,
        enum_options: list[str] | None = None,
    ) -> None:
        """Initialize the device object. Does not connect."""

        self._attribute_name = attribute

        self._device = device
        self._address = device.address
        self._attr_name = name
        self._attr_unique_id = f"{device.address}-{name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_options = enum_options
        self._attr_state_class = (
            SensorStateClass.MEASUREMENT
            if not enum_options and device_class is not SensorDeviceClass.TIMESTAMP
            else None
        )
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

        attribute_value = getattr(self._device, self._attribute_name)

        # If none pass through
        if attribute_value is None:
            self._attr_native_value = attribute_value

        # If timestamp add timezone info
        elif self._attr_device_class is SensorDeviceClass.TIMESTAMP:
            self._attr_native_value = as_local(attribute_value)

        # If enum use enum strings
        elif self._attr_device_class == SensorDeviceClass.ENUM:
            self._attr_native_value = self._attr_options[attribute_value.value + 1]

        # Else pass through value
        else:
            self._attr_native_value = attribute_value

    def _state_change_callback(self) -> None:
        """Run when device informs of state update. Updates local properties."""
        _LOGGER.debug("Received state notification from device %s", self.name)
        self._update_updatable_attributes()
        self.async_write_ha_state()
