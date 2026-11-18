"""Test the update throttle for the SolixBLE integration."""

import asyncio
import threading
from contextlib import ExitStack
from datetime import timedelta
from unittest.mock import MagicMock, patch

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.solix_ble.const import CONF_UPDATE_INTERVAL, DOMAIN
from custom_components.solix_ble.throttle import SolixThrottle

from . import MOCK_C300_DETAILS


def make_device() -> MagicMock:
    """Build a mock device that records its registered callback."""
    device = MagicMock()
    device.available = True
    device.add_callback = MagicMock()
    device.remove_callback = MagicMock()
    return device


def fire(device: MagicMock) -> None:
    """Invoke the callback the throttle registered with the device."""
    device.add_callback.call_args[0][0]()


async def test_registers_one_callback_with_device(hass: HomeAssistant) -> None:
    """The throttle subscribes to the device exactly once."""
    device = make_device()

    SolixThrottle(hass, device, 0)

    assert device.add_callback.call_count == 1


async def test_disabled_passes_every_update_through(hass: HomeAssistant) -> None:
    """An interval of zero fans out on every device update."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 0)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    fire(device)
    fire(device)

    assert callback.call_count == 3


async def test_removed_callback_is_not_called(hass: HomeAssistant) -> None:
    """A de-registered subscriber stops receiving updates."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 0)
    callback = MagicMock()
    throttle.add_callback(callback)
    throttle.remove_callback(callback)

    fire(device)

    assert callback.call_count == 0


async def test_first_update_fans_out_immediately(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The first update after construction is published straight away."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)

    assert callback.call_count == 1


async def test_updates_inside_window_are_suppressed(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Updates arriving inside the window do not reach subscribers."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=1))
    fire(device)
    freezer.tick(timedelta(seconds=7))
    fire(device)

    assert callback.call_count == 1


async def test_held_update_is_flushed_when_window_closes(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The most recent suppressed update is published at the end of the window."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=1))
    fire(device)

    assert callback.call_count == 1

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert callback.call_count == 2


async def test_flush_runs_on_the_event_loop(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A flushed update is published from the event loop thread."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    threads: list[int] = []
    throttle.add_callback(lambda: threads.append(threading.get_ident()))

    fire(device)
    freezer.tick(timedelta(seconds=1))
    fire(device)

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert threads == [hass.loop_thread_id, hass.loop_thread_id]


async def test_no_flush_when_nothing_was_held(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A window that suppressed nothing does not publish at its end."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert callback.call_count == 1


async def test_update_after_window_fans_out_immediately(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """An update arriving after the window has elapsed is published at once."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=31))
    fire(device)

    assert callback.call_count == 2


async def test_availability_change_bypasses_window(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A device going unavailable is published immediately, mid-window."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=1))
    device.available = False
    fire(device)

    assert callback.call_count == 2


async def test_availability_bypass_does_not_fire_on_first_update(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Availability unchanged since construction is not treated as a transition."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=1))
    fire(device)

    assert callback.call_count == 1


async def test_availability_bypass_restarts_window(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A bypass restarts the window rather than leaving the old one running."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=1))
    device.available = False
    fire(device)

    assert callback.call_count == 2

    freezer.tick(timedelta(seconds=1))
    fire(device)

    assert callback.call_count == 2


async def test_set_interval_flushes_a_held_update(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Changing the interval publishes anything currently held."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=1))
    fire(device)

    assert callback.call_count == 1

    throttle.set_interval(60)

    assert callback.call_count == 2


async def test_set_interval_with_nothing_held_does_not_fan_out(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Changing the interval with no held update publishes nothing."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    throttle.set_interval(60)

    assert callback.call_count == 1


async def test_set_interval_applies_the_new_window(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Subsequent updates honour the new interval."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    throttle.set_interval(0)
    fire(device)
    fire(device)

    assert callback.call_count == 3


async def test_shutdown_deregisters_from_device(hass: HomeAssistant) -> None:
    """Shutdown removes the throttle's callback from the device."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 0)

    throttle.async_shutdown()

    assert device.remove_callback.call_count == 1
    assert device.remove_callback.call_args[0][0] == device.add_callback.call_args[0][0]


async def test_shutdown_cancels_a_pending_timer(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A held update is not published after shutdown."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 30)
    callback = MagicMock()
    throttle.add_callback(callback)

    fire(device)
    freezer.tick(timedelta(seconds=1))
    fire(device)

    throttle.async_shutdown()

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert callback.call_count == 1


async def test_shutdown_is_idempotent(hass: HomeAssistant) -> None:
    """Calling shutdown twice does not raise."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 0)

    throttle.async_shutdown()
    throttle.async_shutdown()

    assert device.remove_callback.call_count == 1


async def test_raising_subscriber_does_not_block_the_others(
    hass: HomeAssistant,
) -> None:
    """One subscriber raising still lets the rest run."""
    device = make_device()
    throttle = SolixThrottle(hass, device, 0)
    first = MagicMock(side_effect=RuntimeError("boom"))
    second = MagicMock()
    throttle.add_callback(first)
    throttle.add_callback(second)

    fire(device)

    assert first.call_count == 1
    assert second.call_count == 1


def c300_mocks(stack: ExitStack) -> None:
    """Enter the patches needed to set up a mock C300 config entry."""

    stack.enter_context(
        patch(
            "custom_components.solix_ble.async_ble_device_from_address",
            return_value=MOCK_C300_DETAILS.get_ble_device(),
        )
    )
    stack.enter_context(
        patch("custom_components.solix_ble.async_scanner_count", return_value=1)
    )
    stack.enter_context(patch("SolixBLE.C300.connect", side_effect=[True]))
    stack.enter_context(patch("SolixBLE.C300.connected", side_effect=[True]))
    stack.enter_context(patch("SolixBLE.C300.negotiated", side_effect=[True]))
    stack.enter_context(patch("SolixBLE.SolixBLEDevice.available", side_effect=[True]))


async def test_entry_options_are_applied_to_the_throttle(hass: HomeAssistant) -> None:
    """The configured interval reaches the live throttle, and changes apply in place."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=MOCK_C300_DETAILS.name,
        unique_id=MOCK_C300_DETAILS.addr.lower(),
        data={"model": MOCK_C300_DETAILS.model_class},
        options={CONF_UPDATE_INTERVAL: 30},
    )
    entry.add_to_hass(hass)

    with ExitStack() as stack:
        c300_mocks(stack)

        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        assert entry.runtime_data.throttle._interval == 30

        hass.config_entries.async_update_entry(
            entry, options={CONF_UPDATE_INTERVAL: 60}
        )
        await hass.async_block_till_done()

        assert entry.runtime_data.throttle._interval == 60
