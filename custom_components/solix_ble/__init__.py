"""SolixBLE integration."""

import logging

from SolixBLE import SolixBLEDevice

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


async def async_setup_entry(hass: HomeAssistant, entry: SolixBLEConfigEntry) -> bool:
    """Set up the integration from a config entry."""

    assert entry.unique_id is not None
    address = entry.unique_id.upper()

    ble_device = async_ble_device_from_address(hass, address, connectable=True)

    if ble_device is None:
        count_scanners = async_scanner_count(hass, connectable=True)
        _LOGGER.debug("Count of BLE scanners: %i", count_scanners)

        if count_scanners < 1:
            raise ConfigEntryNotReady(
                "No Bluetooth scanners are available to search for the device."
            )
        raise ConfigEntryNotReady("The device was not found.")

    if ble_device.name is None:
        raise ConfigEntryNotReady(
            "The device was found but its name is unknown. Waiting until name is discovered..."
        )

    device = SolixBLEDevice(ble_device)

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
