"""Config flow for SolixBLE integration."""

from __future__ import annotations

import logging
from typing import Any

from SolixBLE import Generic, C300, C1000
import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.api import (
    async_ble_device_from_address,
    async_scanner_count,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, address: str) -> None:
    """Validate that we can connect."""

    ble_device = async_ble_device_from_address(hass, address.upper(), connectable=True)

    if ble_device is None:
        count_scanners = async_scanner_count(hass, connectable=True)
        _LOGGER.debug("Count of BLE scanners in HA bt: %i", count_scanners)

        if count_scanners < 1:
            raise ScannerNotAvailable
        raise NotFound

    if ble_device.name is None:
        _LOGGER.warning(
            f"The device '{ble_device.address}' was found but its name is not present in the advertisement data. Try again later..."
        )
        raise NotFound

    try:
        device = None
        if "Anker SOLIX C300" in ble_device.name:
            device = C300(ble_device)
        elif "Anker SOLIX C1000" in ble_device.name:
            device = C1000(ble_device)
        else:
            _LOGGER.warning(
                f"The device '{ble_device.name}' is not supported and values will not be available to Home Assistant! "
                f"However when the integration is in debug mode the raw telemetry data and differences between status "
                f"updates will be printed in the log and this can be used to aid in adding support for new devices."
            )
            device = Generic(ble_device)

        if not await device.connect():
            raise CannotConnect

        if not device.available:
            raise CannotSubscribe
    finally:
        await device.disconnect()


class SolixBLEConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolixBLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: bluetooth.BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the home assistant scanner."""

        _LOGGER.debug(
            "HA found Solix device %s. Will show in UI but not auto connect",
            discovery_info.name,
        )

        unique_id = dr.format_mac(discovery_info.address)
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        name = f"{discovery_info.name} ({discovery_info.address})"
        self.context.update({"title_placeholders": {CONF_NAME: name}})

        self._discovery_info = discovery_info

        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a single device."""

        assert self._discovery_info is not None
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                unique_id = dr.format_mac(self._discovery_info.address)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                await validate_input(self.hass, unique_id)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except CannotSubscribe:
                errors["base"] = "cannot_subscribe"
            except ScannerNotAvailable:
                errors["base"] = "no_scanners"
            except NotFound:
                errors["base"] = "not_found"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=self._discovery_info.name, data={})

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={
                CONF_NAME: self._discovery_info.name,
                CONF_MAC: self._discovery_info.address,
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class CannotSubscribe(HomeAssistantError):
    """Error to indicate we cannot get telemetry."""


class ScannerNotAvailable(HomeAssistantError):
    """Error to indicate no bluetooth scanners are available."""


class NotFound(HomeAssistantError):
    """Error to indicate the device could not be found."""
