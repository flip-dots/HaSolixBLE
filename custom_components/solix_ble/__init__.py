"""SolixBLE integration."""

import logging

from SolixBLE import SolixBLEDevice, Generic, C300, C1000

from .const import Models
from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
    async_scanner_count,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)

type SolixBLEConfigEntry = ConfigEntry[SolixBLEDevice]


def get_power_station_class(model: Models) -> SolixBLEDevice:
    """Return correct class for power station from model."""

    if model is Models.C300:
        return C300
    elif model is Models.C1000:
        return C1000
    elif model is Models.UNKNOWN:
        return Generic
    else:
        raise NotImplementedError(f"Unexpected model. Got: '{type(model)}'!")


async def async_setup_entry(hass: HomeAssistant, entry: SolixBLEConfigEntry) -> bool:
    """Set up the integration from a config entry."""

    assert entry.unique_id is not None
    address = entry.unique_id.upper()
    model = entry.data["model"]

    ble_device = async_ble_device_from_address(hass, address, connectable=True)

    if ble_device is None:
        count_scanners = async_scanner_count(hass, connectable=True)
        _LOGGER.debug("Count of BLE scanners: %i", count_scanners)

        if count_scanners < 1:
            raise ConfigEntryNotReady(
                "No Bluetooth scanners are available to search for the device."
            )
        raise ConfigEntryNotReady("The device was not found.")

    PowerStationClass = get_power_station_class(model)
    if PowerStationClass is Generic:
        _LOGGER.warning(
            f"The device '{ble_device.name}' is not supported and values will not be available to Home Assistant! "
            f"However when the integration is in debug mode the raw telemetry data and differences between status "
            f"updates will be printed in the log and this can be used to aid in adding support for new devices."
        )

    device = PowerStationClass(ble_device)
    if not await device.connect():
        raise ConfigEntryNotReady("Device found but unable to connect.")

    if not device.available:
        raise ConfigEntryNotReady(
            "Device connected but unable to subscribe to telemetry."
        )

    entry.runtime_data = device

    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SolixBLEConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_forward_entry_unload(
        entry, Platform.SENSOR
    )

    await entry.runtime_data.disconnect()

    return unload_ok
