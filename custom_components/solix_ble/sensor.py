"""sensor platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import as_local
from SolixBLE import (
    C300,
    C300DC,
    C800,
    C1000,
    C1000G2,
    F2000,
    F3800,
    PrimeCharger160w,
    PrimeCharger250w,
    Solarbank2,
    SolixBLEDevice,
)

from .const import (
    CHARGING_STATUS_C300_STRINGS,
    CHARGING_STATUS_F3800_STRINGS,
    CUT_OFF_SB2_STRINGS,
    GRID_STATUS_STRINGS,
    LIGHT_STATUS_SB2_STRINGS,
    LIGHT_STATUS_STRINGS,
    MAX_LOAD_SB2_STRINGS,
    OVERLOAD_STATUS_C300DC_STRINGS,
    PORT_STATUS_STRINGS,
    USAGE_MODE_SB2_STRINGS,
)

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from . import SolixBLEConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SolixBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Sensors."""

    device = config_entry.runtime_data
    sensors: list[SolixSensorEntity] = []

    # Charging status sensor
    if type(device) in [C300, C300DC]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Charging Status",
                None,
                "charging_status",
                SensorDeviceClass.ENUM,
                CHARGING_STATUS_C300_STRINGS,
                None,
            )
        )

    # Charging status sensor
    if type(device) in [F3800]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Charging Status",
                None,
                "charging_status",
                SensorDeviceClass.ENUM,
                CHARGING_STATUS_F3800_STRINGS,
                None,
            )
        )

    # Time remaining sensor
    if type(device) in [C300, C300DC, C800, C1000, F2000, F3800]:
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
                state_class=None,
            )
        ),

    # Battery percentage sensor
    if type(device) in [C300, C300DC, C800, C1000, C1000G2, F2000, F3800, Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Battery Percentage",
                "%",
                "battery_percentage",
                SensorDeviceClass.BATTERY,
            )
        )

    # Battery charge power sensor
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Battery charge power",
                "W",
                "battery_charge_power",
                SensorDeviceClass.POWER,
            )
        )

    # Battery discharge power sensor
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Battery discharge power",
                "W",
                "battery_discharge_power",
                SensorDeviceClass.POWER,
            )
        )

    # Battery health sensor
    if type(device) in [C300DC, C800, C1000, C1000G2, F2000]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Battery Health",
                "%",
                "battery_health",
                None,
            )
        )

    # Battery charged energy (energy in)
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Battery input energy",
                "kWh",
                "charged_energy",
                SensorDeviceClass.ENERGY,
                state_class=None,
            )
        )

    # Solarbank dispensed energy (energy out)
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Total output energy",
                "kWh",
                "output_energy",
                SensorDeviceClass.ENERGY,
                state_class=None,
            )
        )

    # Output cutoff thresholds
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Output cutoff threshold",
                None,
                "output_cutoff_data",
                SensorDeviceClass.ENUM,
                CUT_OFF_SB2_STRINGS,
                state_class=None,
            )
        )

    # Input cutoff thresholds
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Input cutoff threshold",
                None,
                "input_cutoff_data",
                SensorDeviceClass.ENUM,
                CUT_OFF_SB2_STRINGS,
                state_class=None,
            )
        )

    # Temperature sensor
    if type(device) in [C300, C300DC, C800, C1000, C1000G2, F2000, F3800, Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Temperature",
                UnitOfTemperature.CELSIUS,
                "temperature",
                SensorDeviceClass.TEMPERATURE,
            )
        )

    # Total power in sensor
    if type(device) in [C300, C300DC, C800, C1000, F3800]:
        sensors.append(
            SolixSensorEntity(
                device, "Total Power In", "W", "power_in", SensorDeviceClass.POWER
            )
        )

    # Total power out sensor
    if type(device) in [C300, C300DC, C800, C1000, C1000G2, F3800, Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device, "Total Power Out", "W", "power_out", SensorDeviceClass.POWER
            )
        )

    # AC power in sensor
    if type(device) in [C300, C800, C1000, C1000G2, F2000, F3800]:
        sensors.append(
            SolixSensorEntity(
                device,
                "AC Power In",
                "W",
                "ac_power_in",
                SensorDeviceClass.POWER,
            )
        )

    # AC power out sensor
    if type(device) in [C300, C800, C1000, C1000G2, F2000, F3800, Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "AC Power Out",
                "W",
                "ac_power_out",
                SensorDeviceClass.POWER,
            )
        )

    # AC output on/off sensor
    if type(device) in [C300, C800, C1000, C1000G2, F3800]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status AC Out",
                None,
                "ac_output",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
                None,
            )
        )

    # AC output timer
    if type(device) in [C300, C800, C1000]:
        sensors.append(
            SolixSensorEntity(
                device,
                "AC Timer",
                None,
                "ac_timer",
                SensorDeviceClass.TIMESTAMP,
                state_class=None,
            )
        )

    # Solar power in
    if type(device) in [C300, C300DC, C800, C1000, C1000G2, F2000, F3800, Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Solar Power In",
                "W",
                "solar_power_in",
                SensorDeviceClass.POWER,
            )
        )

    # Solar yield
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "PV Yield",
                "kWh",
                "pv_yield",
                SensorDeviceClass.ENERGY,
                state_class=None,
            )
        )

    # DC power out
    if type(device) in [C300, C300DC, C1000G2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "DC Power Out",
                "W",
                "dc_power_out",
                SensorDeviceClass.POWER,
            )
        )

    # DC/Solar power in status
    if type(device) in [C300DC]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status Solar",
                None,
                "solar_port",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
                None,
            )
        )

    # DC power out status
    # TODO: Reenable for C1000 when underlying library fixes
    if type(device) in [C300, C1000G2, F3800]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status DC Out",
                None,
                "dc_output",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
                None,
            )
        )

    # DC Timer
    if type(device) in [C300, C300DC]:
        sensors.append(
            SolixSensorEntity(
                device,
                "DC Timer",
                None,
                "dc_timer",
                SensorDeviceClass.TIMESTAMP,
                state_class=None,
            )
        )

    # USB C1 power out
    if type(device) in [
        C300,
        C300DC,
        C800,
        C1000,
        C1000G2,
        F2000,
        F3800,
        PrimeCharger160w,
        PrimeCharger250w,
    ]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C1 Power",
                "W",
                "usb_c1_power",
                SensorDeviceClass.POWER,
            )
        )

    # USB C2 power out
    if type(device) in [
        C300,
        C300DC,
        C800,
        C1000,
        C1000G2,
        F2000,
        F3800,
        PrimeCharger160w,
        PrimeCharger250w,
    ]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C2 Power",
                "W",
                "usb_c2_power",
                SensorDeviceClass.POWER,
            )
        )

    # USB C3 power out
    if type(device) in [
        C300,
        C300DC,
        C1000G2,
        F2000,
        F3800,
        PrimeCharger160w,
        PrimeCharger250w,
    ]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C3 Power",
                "W",
                "usb_c3_power",
                SensorDeviceClass.POWER,
            )
        )

    # USB C4 power out
    if type(device) in [C300DC, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C4 Power",
                "W",
                "usb_c4_power",
                SensorDeviceClass.POWER,
            )
        )

    # USB A1 power out
    if type(device) in [
        C300,
        C300DC,
        C800,
        C1000,
        C1000G2,
        F2000,
        F3800,
        PrimeCharger250w,
    ]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB A1 Power",
                "W",
                "usb_a1_power",
                SensorDeviceClass.POWER,
            )
        )

    # USB A2 power out
    if type(device) in [C300DC, C800, C1000, F2000, F3800, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB A2 Power",
                "W",
                "usb_a2_power",
                SensorDeviceClass.POWER,
            )
        )

    # USB C1 status
    if type(device) in [
        C300,
        C300DC,
        C1000G2,
        F3800,
        PrimeCharger160w,
        PrimeCharger250w,
    ]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status USB C1",
                None,
                "usb_port_c1",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
                None,
            )
        )

    # USB C2 status
    if type(device) in [
        C300,
        C300DC,
        C1000G2,
        F3800,
        PrimeCharger160w,
        PrimeCharger250w,
    ]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status USB C2",
                None,
                "usb_port_c2",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
                None,
            )
        )

    # USB C3 status
    if type(device) in [
        C300,
        C300DC,
        C1000G2,
        F3800,
        PrimeCharger160w,
        PrimeCharger250w,
    ]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status USB C3",
                None,
                "usb_port_c3",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
                None,
            )
        )

    # USB C4 status
    if type(device) in [C300DC, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status USB C4",
                None,
                "usb_port_c4",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
                None,
            )
        )

    # USB A1 status
    if type(device) in [C300, C300DC, C1000G2, F3800, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status USB A1",
                None,
                "usb_port_a1",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
                None,
            )
        )

    # USB A2 status
    if type(device) in [C300DC, F3800, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status USB A2",
                None,
                "usb_port_a2",
                SensorDeviceClass.ENUM,
                PORT_STATUS_STRINGS,
                None,
            )
        )

    # Overload status
    if type(device) in [C300DC]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Overload Status",
                None,
                "device_overload",
                SensorDeviceClass.ENUM,
                OVERLOAD_STATUS_C300DC_STRINGS,
                None,
            )
        )

    # USB C1 voltage out
    if type(device) in [PrimeCharger160w, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C1 Voltage",
                "V",
                "usb_c1_voltage",
                SensorDeviceClass.VOLTAGE,
            )
        )

    # USB C2 voltage out
    if type(device) in [PrimeCharger160w, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C2 Voltage",
                "V",
                "usb_c2_voltage",
                SensorDeviceClass.VOLTAGE,
            )
        )

    # USB C3 voltage out
    if type(device) in [PrimeCharger160w, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C3 Voltage",
                "V",
                "usb_c3_voltage",
                SensorDeviceClass.VOLTAGE,
            )
        )

    # USB C4 voltage out
    if type(device) in [PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C4 Voltage",
                "V",
                "usb_c4_voltage",
                SensorDeviceClass.VOLTAGE,
            )
        )

    # USB A1 voltage out
    if type(device) in [PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB A1 Voltage",
                "V",
                "usb_a1_voltage",
                SensorDeviceClass.VOLTAGE,
            )
        )

    # USB A2 voltage out
    if type(device) in [PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB A2 Voltage",
                "V",
                "usb_a2_voltage",
                SensorDeviceClass.VOLTAGE,
            )
        )

    # USB C1 current out
    if type(device) in [PrimeCharger160w, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C1 Current",
                "A",
                "usb_c1_current",
                SensorDeviceClass.CURRENT,
            )
        )

    # USB C2 current out
    if type(device) in [PrimeCharger160w, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C2 Current",
                "A",
                "usb_c2_current",
                SensorDeviceClass.CURRENT,
            )
        )

    # USB C3 current out
    if type(device) in [PrimeCharger160w, PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C3 Current",
                "A",
                "usb_c3_current",
                SensorDeviceClass.CURRENT,
            )
        )

    # USB C4 current out
    if type(device) in [PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB C4 Current",
                "A",
                "usb_c4_current",
                SensorDeviceClass.CURRENT,
            )
        )

    # USB A1 current out
    if type(device) in [PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB A1 Current",
                "A",
                "usb_a1_current",
                SensorDeviceClass.CURRENT,
            )
        )

    # USB A2 current out
    if type(device) in [PrimeCharger250w]:
        sensors.append(
            SolixSensorEntity(
                device,
                "USB A2 Current",
                "A",
                "usb_a2_current",
                SensorDeviceClass.CURRENT,
            )
        )

    # Light status
    if type(device) in [C300, C300DC]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status Light",
                None,
                "light",
                SensorDeviceClass.ENUM,
                LIGHT_STATUS_STRINGS,
                None,
            )
        )

    # Display status
    if type(device) in [C300DC]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Display Status",
                None,
                "display_mode",
                SensorDeviceClass.ENUM,
                LIGHT_STATUS_STRINGS,
                None,
            )
        )

    # Error status
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Error code",
                None,
                "error_code",
                state_class=None,
            )
        )

    # Firmware version
    if type(device) in [C300, C300DC, C800, C1000, F2000, F3800, Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Firmware Version",
                None,
                "software_version",
                state_class=None,
            )
        )

    # Serial number
    if type(device) in [C300, C300DC, C800, C1000, C1000G2, F2000, F3800, Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Serial Number",
                None,
                "serial_number",
                state_class=None,
            )
        )

    # Expansion battery temperature sensor
    if type(device) in [C1000, F2000]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Expansion Battery Temperature",
                UnitOfTemperature.CELSIUS,
                "temperature_expansion",
                SensorDeviceClass.TEMPERATURE,
            )
        )

    # Expansion battery percentage
    if type(device) in [C1000, F2000]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Expansion Battery Percentage",
                "%",
                "battery_percentage_expansion",
                SensorDeviceClass.BATTERY,
            )
        )

    # Average battery percentage across all batteries
    if type(device) in [F3800, Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Average Battery Percentage",
                "%",
                "battery_percentage_aggregate",
                SensorDeviceClass.BATTERY,
            )
        )

    # Expansion battery health
    if type(device) in [C1000, F2000]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Expansion Battery Health",
                "%",
                "battery_health_expansion",
                SensorDeviceClass.BATTERY,
            )
        )

    # Expansion battery firmware version
    if type(device) in [C1000, F2000, Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Expansion Battery Firmware Version",
                None,
                "software_version_expansion",
                state_class=None,
            )
        )

    # Number of expansion batteries
    if type(device) in [C1000, F2000]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Number Of Expansion Batteries",
                None,
                "num_expansion",
            )
        )

    ######################
    # Solar bank sensors #
    ######################

    # Grid to home power
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Grid to Home power",
                "W",
                "grid_to_home_power",
                SensorDeviceClass.POWER,
            )
        )

    # PV to grid power
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "PV to Grid power",
                "W",
                "pv_to_grid_power",
                SensorDeviceClass.POWER,
            )
        )

    # Grid import energy
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Grid import energy",
                "kWh",
                "grid_import_energy",
                SensorDeviceClass.ENERGY,
                state_class=None,
            )
        )

    # Grid export energy
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Grid export energy",
                "kWh",
                "grid_export_energy",
                SensorDeviceClass.ENERGY,
                state_class=None,
            )
        )

    # House demand (power used by house)
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "House demand power",
                "W",
                "house_demand",
                SensorDeviceClass.POWER,
            )
        )

    # House demand (power used by house)
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "House consumed energy",
                "kWh",
                "consumed_energy",
                SensorDeviceClass.ENERGY,
                state_class=None,
            )
        )

    # Power out of the built-in sockets
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "AC Power Out Sockets",
                "W",
                "ac_power_out_sockets",
                SensorDeviceClass.POWER,
            )
        )

    # Max load
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Maximum load",
                None,
                "max_load",
                SensorDeviceClass.ENUM,
                MAX_LOAD_SB2_STRINGS,
                state_class=None,
            )
        )

    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Usage mode",
                None,
                "usage_mode",
                SensorDeviceClass.ENUM,
                USAGE_MODE_SB2_STRINGS,
                state_class=None,
            )
        )

    # Solar PV power in for port 1
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Solar Power In Port 1",
                "W",
                "solar_pv_1_power_in",
                SensorDeviceClass.POWER,
            )
        )

    # Solar PV power in for port 2
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Solar Power In Port 2",
                "W",
                "solar_pv_2_power_in",
                SensorDeviceClass.POWER,
            )
        )

    # Solar PV power in for port 3
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Solar Power In Port 3",
                "W",
                "solar_pv_3_power_in",
                SensorDeviceClass.POWER,
            )
        )

    # Solar PV power in for port 4
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Solar Power In Port 4",
                "W",
                "solar_pv_4_power_in",
                SensorDeviceClass.POWER,
            )
        )

    # Solarbank light status
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Status light",
                None,
                "light_mode",
                SensorDeviceClass.ENUM,
                LIGHT_STATUS_SB2_STRINGS,
                None,
            )
        )

    # Grid status
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Grid Status",
                None,
                "grid_status",
                SensorDeviceClass.ENUM,
                GRID_STATUS_STRINGS,
                None,
            )
        )

    # Heater status
    if type(device) in [Solarbank2]:
        sensors.append(
            SolixSensorEntity(
                device,
                "Battery Heating",
                None,
                "battery_heating",
                None,
            )
        )

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
        state_class: SensorStateClass = SensorStateClass.MEASUREMENT,
    ) -> None:
        """Initialize the device object. Does not connect."""

        self._attribute_name = attribute

        self._device = device
        self._address = device.address
        self._attr_name = name
        self._attr_unique_id = f"{device.address}_{attribute}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_options = enum_options
        self._attr_state_class = state_class
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
            self._attr_native_value = self._attr_options[
                list(type(attribute_value)).index(attribute_value)
            ]

        # Else pass through value
        else:
            self._attr_native_value = attribute_value

    def _state_change_callback(self) -> None:
        """Run when device informs of state update. Updates local properties."""
        _LOGGER.debug("Received state notification from device %s", self.name)
        self._update_updatable_attributes()
        self.async_write_ha_state()
