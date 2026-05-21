"""Tests for the SolixBLE Bluetooth integration."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from bleak.backends.scanner import AdvertisementData, BLEDevice
from habluetooth import BluetoothServiceInfoBleak
from SolixBLE import LightStatus, PortStatus
from SolixBLE.devices.solarbank2 import (
    GridStatus,
    LightMode,
    MaxLoadSB2,
    SBPowerCutoff,
    SBUsageMode,
)

from custom_components.solix_ble.const import Models

# Copied from HA Bluetooth tests
ADVERTISEMENT_DATA_DEFAULTS = {
    "local_name": "",
    "manufacturer_data": {},
    "service_data": {},
    "service_uuids": [],
    "rssi": -127,
    "platform_data": ((),),
    "tx_power": -127,
}

# Copied from HA Bluetooth tests
BLE_DEVICE_DEFAULTS = {
    "name": None,
    "details": None,
}


# Copied from HA Bluetooth tests
def generate_advertisement_data(**kwargs: Any) -> AdvertisementData:
    """Generate advertisement data with defaults."""
    new = kwargs.copy()
    for key, value in ADVERTISEMENT_DATA_DEFAULTS.items():
        new.setdefault(key, value)
    return AdvertisementData(**new)


# Copied from HA Bluetooth tests
def generate_ble_device(
    address: str | None = None,
    name: str | None = None,
    details: Any | None = None,
    **kwargs: Any,
) -> BLEDevice:
    """Generate a BLEDevice with defaults."""
    new = kwargs.copy()
    if address is not None:
        new["address"] = address
    if name is not None:
        new["name"] = name
    if details is not None:
        new["details"] = details
    for key, value in BLE_DEVICE_DEFAULTS.items():
        new.setdefault(key, value)
    return BLEDevice(**new)


@dataclass
class MockDeviceDetails:
    """Mock of a generic power station used for testing config flow."""

    name: str
    addr: str
    model_string: str
    model_class: Models

    def get_ble_device(self) -> BLEDevice:
        return generate_ble_device(self.addr, self.name)

    def get_service_info(self) -> BluetoothServiceInfoBleak:
        return BluetoothServiceInfoBleak(
            name=self.name,
            manufacturer_data={0: b""},
            service_data={"0000ff09-0000-1000-8000-00805f9b34fb": b""},
            service_uuids=[
                "0000ff09-0000-1000-8000-00805f9b34fb",
            ],
            address=self.addr,
            rssi=-60,
            source="local",
            advertisement=generate_advertisement_data(
                local_name=self.name,
                manufacturer_data={0: b""},
            ),
            device=self.get_ble_device(),
            time=0,
            connectable=True,
            tx_power=-127,
        )


MOCK_C300_DETAILS = MockDeviceDetails(
    name="Anker SOLIX C300",
    addr="AA:BB:CC:DD:EE:00",
    model_string="C300(X)",
    model_class=Models.C300,
)

MOCK_C300X_DETAILS = MockDeviceDetails(
    name="Anker SOLIX C300X",
    addr="AA:BB:CC:DD:EE:01",
    model_string="C300(X)",
    model_class=Models.C300,
)

MOCK_C300DC_DETAILS = MockDeviceDetails(
    name="Anker SOLIX C300X DC",
    addr="AA:BB:CC:DD:EE:01",
    model_string="C300(X) DC",
    model_class=Models.C300DC,
)

MOCK_C800_DETAILS = MockDeviceDetails(
    name="Anker SOLIX C800",
    addr="AA:BB:CC:DD:EE:08",
    model_string="C800(X)",
    model_class=Models.C800,
)

MOCK_C1000_DETAILS = MockDeviceDetails(
    name="Anker SOLIX C1000",
    addr="AA:BB:CC:DD:EE:02",
    model_string="C1000(X)",
    model_class=Models.C1000,
)

MOCK_C1000X_DETAILS = MockDeviceDetails(
    name="Anker SOLIX C1000X",
    addr="AA:BB:CC:DD:EE:03",
    model_string="C1000(X)",
    model_class=Models.C1000,
)

MOCK_C1000G2_DETAILS = MockDeviceDetails(
    name="Anker SOLIX C1000 Gen 2",
    addr="AA:BB:CC:DD:EE:03",
    model_string="C1000(X) Gen 2",
    model_class=Models.C1000G2,
)

MOCK_F2000_DETAILS = MockDeviceDetails(
    name="Anker SOLIX F2000",
    addr="AA:BB:CC:DD:EE:03",
    model_string="F2000 (767)",
    model_class=Models.F2000,
)

MOCK_F3800_DETAILS = MockDeviceDetails(
    name="Anker SOLIX F3800",
    addr="AA:BB:CC:DD:EE:03",
    model_string="F3800",
    model_class=Models.F3800,
)

MOCK_PRIME_160_DETAILS = MockDeviceDetails(
    name="Anker Prime 160w Charger",
    addr="AA:BB:CC:DD:00:00",
    model_string="Prime Charger (160w)",
    model_class=Models.PRIME_CHARGER_160,
)

MOCK_PRIME_250_DETAILS = MockDeviceDetails(
    name="Anker Prime 250w Charger",
    addr="AA:BB:CC:DD:00:01",
    model_string="Prime Charger (250w)",
    model_class=Models.PRIME_CHARGER_250,
)

MOCK_SOLAR_BANK_2_DETAILS = MockDeviceDetails(
    name="Solar Bank 2",
    addr="AA:BB:CC:DD:00:02",
    model_string="Solarbank 2",
    model_class=Models.SOLARBANK_2,
)

MOCK_UNKNOWN_DETAILS = MockDeviceDetails(
    name="Anker SOLIX IDK",
    addr="AA:BB:CC:DD:EE:04",
    model_string="Unknown",
    model_class=Models.UNKNOWN,
)

# Sometimes the method name we are patching and the
# entity ID do not line up, so a tuple is used to
# manually specify it
MOCK_C300_TEST_DATA = {
    "ac_timer": datetime.now(UTC),
    "dc_timer": datetime.now(UTC),
    "hours_remaining": ("remaining_hours", 1),
    "days_remaining": ("remaining_days", 2),
    "time_remaining": ("remaining_time", 2.5),
    "timestamp_remaining": datetime.now(UTC),
    "ac_power_in": 3,
    "ac_power_out": 4,
    "usb_c1_power": 5,
    "usb_c2_power": 6,
    "usb_c3_power": 7,
    "usb_a1_power": 8,
    "dc_power_out": 9,
    "solar_power_in": 10,
    "power_in": ("total_power_in", 11),
    "power_out": ("total_power_out", 12),
    # TODO: Solar port is broken in underlying library
    # "solar_port": ("status_solar", PortStatus.INPUT),
    "battery_percentage": 13,
    "usb_port_c1": ("status_usb_c1", PortStatus.OUTPUT),
    "usb_port_c2": ("status_usb_c2", PortStatus.NOT_CONNECTED),
    "usb_port_c3": ("status_usb_c3", PortStatus.INPUT),
    "usb_port_a1": ("status_usb_a1", PortStatus.OUTPUT),
    "dc_output": ("status_dc_out", PortStatus.OUTPUT),
    "ac_output": ("status_ac_out", PortStatus.NOT_CONNECTED),
    "light": ("status_light", LightStatus.HIGH),
}

# Sometimes the method name we are patching and the
# entity ID do not line up, so a tuple is used to
# manually specify it
MOCK_C300DC_TEST_DATA = {
    "dc_timer": datetime.now(UTC),
    "hours_remaining": ("remaining_hours", 1),
    "days_remaining": ("remaining_days", 2),
    "time_remaining": ("remaining_time", 2.5),
    "timestamp_remaining": datetime.now(UTC),
    "usb_c1_power": 5,
    "usb_c2_power": 6,
    "usb_c3_power": 7,
    "usb_c4_power": 8,
    "usb_a1_power": 9,
    "usb_a2_power": 10,
    "dc_power_out": 11,
    "solar_power_in": 12,
    "power_in": ("total_power_in", 13),
    "power_out": ("total_power_out", 14),
    "solar_port": ("status_solar", PortStatus.INPUT),
    "battery_percentage": 15,
    "battery_health": 16,
    "usb_port_c1": ("status_usb_c1", PortStatus.OUTPUT),
    "usb_port_c2": ("status_usb_c2", PortStatus.NOT_CONNECTED),
    "usb_port_c3": ("status_usb_c3", PortStatus.INPUT),
    "usb_port_c4": ("status_usb_c4", PortStatus.NOT_CONNECTED),
    "usb_port_a1": ("status_usb_a1", PortStatus.OUTPUT),
    "usb_port_a2": ("status_usb_a2", PortStatus.NOT_CONNECTED),
    "light": ("status_light", LightStatus.HIGH),
    "display_mode": ("display_status", LightStatus.OFF),
    "software_version": ("firmware_version", "0.0.17"),
    "temperature": 18,
}

# Sometimes the method name we are patching and the
# entity ID do not line up, so a tuple is used to
# manually specify it.
MOCK_C800_TEST_DATA = {
    "ac_timer": datetime.now(UTC),
    "hours_remaining": ("remaining_hours", 5),
    "days_remaining": ("remaining_days", 6),
    "time_remaining": ("remaining_time", 12),
    "timestamp_remaining": datetime.now(UTC),
    "ac_power_in": 89,
    "ac_power_out": 45,
    "usb_c1_power": 99,
    "usb_c2_power": 7,
    "usb_a1_power": 5,
    "usb_a2_power": 12,
    "solar_power_in": 0,
    "power_in": ("total_power_in", 89),
    "power_out": ("total_power_out", 102),
    # TODO: Solar port is broken in underlying library
    # "solar_port": ("status_solar", PortStatus.INPUT),
    "ac_output": ("status_ac_out", PortStatus.OUTPUT),
    "battery_percentage": 100,
}

# Sometimes the method name we are patching and the
# entity ID do not line up, so a tuple is used to
# manually specify it
MOCK_C1000_TEST_DATA = {
    "ac_timer": datetime.now(UTC),
    "hours_remaining": ("remaining_hours", 1),
    "days_remaining": ("remaining_days", 2),
    "time_remaining": ("remaining_time", 2.5),
    "timestamp_remaining": datetime.now(UTC),
    "ac_power_in": 3,
    "ac_power_out": 4,
    "usb_c1_power": 5,
    "usb_c2_power": 6,
    "usb_a1_power": 7,
    "usb_a2_power": 8,
    "solar_power_in": 10,
    "power_in": ("total_power_in", 11),
    "power_out": ("total_power_out", 12),
    # TODO: Solar port is broken in underlying library
    # "solar_port": ("status_solar", PortStatus.INPUT),
    "ac_output": ("status_ac_out", PortStatus.NOT_CONNECTED),
    "battery_percentage": 13,
}

# Sometimes the method name we are patching and the
# entity ID do not line up, so a tuple is used to
# manually specify it
MOCK_PRIME_160_TEST_DATA = {
    "usb_c1_power": 5.0,
    "usb_c2_power": 0.0,
    "usb_c3_power": 7.67,
    "usb_c1_current": 4.99,
    "usb_c2_current": 0.0,
    "usb_c3_current": 5.3,
    "usb_c1_voltage": 24.5,
    "usb_c2_voltage": 0.0,
    "usb_c3_voltage": 24.4,
    "usb_port_c1": ("status_usb_c1", PortStatus.OUTPUT),
    "usb_port_c2": ("status_usb_c2", PortStatus.NOT_CONNECTED),
    "usb_port_c3": ("status_usb_c3", PortStatus.OUTPUT),
}

# Sometimes the method name we are patching and the
# entity ID do not line up, so a tuple is used to
# manually specify it
MOCK_PRIME_250_TEST_DATA = {
    "usb_c1_power": 0.0,
    "usb_c2_power": 24.5,
    "usb_c3_power": 120.4,
    "usb_c4_power": 12.2,
    "usb_a1_power": 8.65,
    "usb_a2_power": 0.0,
    "usb_c1_current": 0.0,
    "usb_c2_current": 2.9,
    "usb_c3_current": 5.3,
    "usb_c4_current": 1.0,
    "usb_a1_current": 0.1,
    "usb_a2_current": 0.0,
    "usb_c1_voltage": 0.0,
    "usb_c2_voltage": 2.5,
    "usb_c3_voltage": 24.4,
    "usb_c4_voltage": 20.0,
    "usb_a1_voltage": 4.65,
    "usb_a2_voltage": 5.11,
    "usb_port_c1": ("status_usb_c1", PortStatus.NOT_CONNECTED),
    "usb_port_c2": ("status_usb_c2", PortStatus.OUTPUT),
    "usb_port_c3": ("status_usb_c3", PortStatus.OUTPUT),
    "usb_port_c4": ("status_usb_c4", PortStatus.OUTPUT),
    "usb_port_a1": ("status_usb_a1", PortStatus.OUTPUT),
    "usb_port_a2": ("status_usb_a2", PortStatus.NOT_CONNECTED),
}


# Sometimes the method name we are patching and the
# entity ID do not line up, so a tuple is used to
# manually specify it
MOCK_SOLAR_BANK_2_TEST_DATA = {
    "battery_percentage": 56,
    "software_version": ("firmware_version", "0.0.1"),
    "software_version_expansion": ("expansion_battery_firmware_version", "0.0.2"),
    "serial_number": "0.1.2.3",
    "temperature": -5,
    "solar_power_in": 150.3,
    "ac_power_out": 700.1,
    "battery_percentage_aggregate": ("average_battery_percentage", 90),
    "battery_charge_power": 0,
    "pv_yield": 1053.2,
    "charged_energy": ("battery_input_energy", 124.3),
    "output_energy": ("total_output_energy", 12.7),
    "output_cutoff_data": ("output_cutoff_threshold", SBPowerCutoff.P5, "5%"),
    "input_cutoff_data": ("input_cutoff_threshold", SBPowerCutoff.P10, "10%"),
    "battery_discharge_power": 12.4,
    "grid_to_home_power": 12.5,
    "pv_to_grid_power": 1245.1,
    "grid_import_energy": 12.3,
    "grid_export_energy": 1257.3,
    "house_demand": ("house_demand_power", 124.6),
    "ac_power_out_sockets": 1.67,
    "max_load": ("maximum_load", MaxLoadSB2.W350, "350w"),
    "usage_mode": ("usage_mode", SBUsageMode.MANUAL, "Manual"),
    "consumed_energy": ("house_consumed_energy", 124.5),
    "solar_pv_1_power_in": ("solar_power_in_port_1", 13.1),
    "solar_pv_2_power_in": ("solar_power_in_port_2", 13.2),
    "solar_pv_3_power_in": ("solar_power_in_port_3", 13.3),
    "solar_pv_4_power_in": ("solar_power_in_port_4", 13.4),
    "power_out": ("total_power_out", 14.745),
    "error_code": 0,
    "light_mode": ("status_light", LightMode.NORMAL, "Normal"),
    "grid_status": ("grid_status", GridStatus.OK, "Ok"),
    "battery_heating": True,
}

MOCK_UNKNOWN_TEST_DATA = {}
