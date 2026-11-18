"""Update throttling for sensor entities."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.helpers.event import async_call_later

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import CALLBACK_TYPE, HomeAssistant
    from SolixBLE import SolixBLEDevice

_LOGGER = logging.getLogger(__name__)


class SolixThrottle:
    """Rate limits device state notifications on their way to entities.

    Registers a single callback with the device and fans out to its own
    subscribers at most once per interval.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        device: SolixBLEDevice,
        interval: float,
    ) -> None:
        """Initialize the throttle and subscribe to the device."""

        self._hass = hass
        self._device = device
        self._interval = interval
        self._callbacks: list[Callable[[], None]] = []
        self._last_fanout: float | None = None
        self._pending = False
        self._unsub_timer: CALLBACK_TYPE | None = None
        self._last_available: bool = device.available
        self._shutdown = False

        device.add_callback(self._device_updated)

    def add_callback(self, callback: Callable[[], None]) -> None:
        """Register a subscriber to be run on a throttled update."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """De-register a subscriber."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def set_interval(self, interval: float) -> None:
        """Apply a new throttle interval, flushing anything currently held."""

        self._interval = interval
        self._cancel_timer()

        if self._pending:
            self._fan_out()

    def async_shutdown(self) -> None:
        """Stop the throttle and release everything it holds."""

        self._cancel_timer()

        if not self._shutdown:
            self._shutdown = True
            self._device.remove_callback(self._device_updated)

        self._pending = False
        self._callbacks = []

    def _device_updated(self) -> None:
        """Run when the device reports a state change."""

        # Throttling disabled
        if self._interval <= 0:
            self._fan_out()
            return

        # Availability transitions must never wait for the window
        if self._device.available != self._last_available:
            self._fan_out()
            return

        # First update, or the window has elapsed
        now = time.monotonic()
        if self._last_fanout is None or now - self._last_fanout >= self._interval:
            self._fan_out()
            return

        # Inside the window, hold it for the flush
        self._pending = True
        if self._unsub_timer is None:
            remaining = self._interval - (now - self._last_fanout)
            self._unsub_timer = async_call_later(self._hass, remaining, self._flush)

    @callback
    def _flush(self, _now: object) -> None:
        """Run when the throttle window closes."""
        self._unsub_timer = None

        if self._pending:
            self._fan_out()

    def _cancel_timer(self) -> None:
        """Cancel a pending flush timer if there is one."""

        if self._unsub_timer is not None:
            self._unsub_timer()
            self._unsub_timer = None

    def _fan_out(self) -> None:
        """Run every registered subscriber and restart the window."""

        self._last_fanout = time.monotonic()
        self._pending = False
        self._last_available = self._device.available

        for subscriber in self._callbacks:
            try:
                subscriber()
            except Exception:
                _LOGGER.exception(
                    f"Exception raised by a throttled callback '{subscriber}'!",
                )
