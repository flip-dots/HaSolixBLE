"""Tests for the SolixBLE Bluetooth integration."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from bleak.backends.scanner import AdvertisementData, BLEDevice
from habluetooth import BluetoothServiceInfoBleak
from SolixBLE import LightStatus, PortStatus

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
    "solar_port": ("status_solar", PortStatus.INPUT),
    "battery_percentage": 13,
    "usb_port_c1": ("status_usb_c1", PortStatus.OUTPUT),
    "usb_port_c2": ("status_usb_c2", PortStatus.NOT_CONNECTED),
    "usb_port_c3": ("status_usb_c3", PortStatus.INPUT),
    "usb_port_a1": ("status_usb_a1", PortStatus.OUTPUT),
    "dc_port": ("status_dc_out", PortStatus.OUTPUT),
    "light": ("status_light", LightStatus.HIGH),
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
    "solar_port": ("status_solar", PortStatus.INPUT),
    "battery_percentage": 13,
}

MOCK_UNKNOWN_TEST_DATA = {}
