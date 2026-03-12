"""SolixBLE integration."""

import logging

from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
    async_scanner_count,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from SolixBLE import (
    C300,
    C300DC,
    C800,
    C1000,
    C1000G2,
    F2000,
    F3800,
    Generic,
    SolixBLEDevice,
)

from .const import Models

_LOGGER = logging.getLogger(__name__)

type SolixBLEConfigEntry = ConfigEntry[SolixBLEDevice]


def get_power_station_class(model: Models) -> SolixBLEDevice:
    """Return correct class for power station from model."""

    if model is Models.C300:
        return C300
    elif model is Models.C300DC:
        return C300DC
    elif model is Models.C800:
        return C800
    elif model is Models.C1000:
        return C1000
    elif model is Models.C1000G2:
        return C1000G2
    elif model is Models.F2000:
        return F2000
    elif model is Models.F3800:
        return F3800
    elif model is Models.UNKNOWN:
        return Generic
    else:
        raise NotImplementedError(f"Unexpected model. Got: '{type(model)}'!")


async def async_setup_entry(hass: HomeAssistant, entry: SolixBLEConfigEntry) -> bool:
    """Set up the integration from a config entry."""

    assert entry.unique_id is not None
    address = entry.unique_id.upper()
    model = Models(entry.data["model"])

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
    if model is Models.UNKNOWN:
        _LOGGER.warning(
            f"The device '{ble_device.name}' is not supported and values will not be available to Home Assistant! "
            f"However when the integration is in debug mode the raw telemetry data and differences between status "
            f"updates will be printed in the log and this can be used to aid in adding support for new devices."
        )

    device = PowerStationClass(ble_device)
    try:
        await device.connect()
    except Exception as e:
        raise ConfigEntryNotReady(
            "Unexpected exception when connecting to device."
        ) from e

    if not device.connected:
        raise ConfigEntryNotReady("Device found but unable to connect.")

    if not device.negotiated:
        raise ConfigEntryNotReady(
            "Device connected but failed to negotiate encryption."
        )

    entry.runtime_data = device

    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform.SENSOR, Platform.SWITCH]
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SolixBLEConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok_sensor = await hass.config_entries.async_forward_entry_unload(
        entry, Platform.SENSOR
    )
    unload_ok_switch = await hass.config_entries.async_forward_entry_unload(
        entry, Platform.SWITCH
    )

    await entry.runtime_data.disconnect()

    entry.runtime_data = None

    return unload_ok_sensor and unload_ok_switch
