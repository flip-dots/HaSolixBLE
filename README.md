# Home Assistant Solix BLE

Home Assistant integration which allows for the monitoring of Anker Solix devices using a Bluetooth connection.


## Features

- 🔋 Battery percentage
- ⚡ Total Power In/Out
- 🔌 AC Power In/Out
- 🚗 DC Power In/Out
- ⏰ AC/DC Timer value
- ⏲️ Time remaining to full/empty
- ☀️ Solar Power In
- 📱 USB Port Status
- 💡 Light bar status


## Supported devices

- C300X
- C1000
- Maybe more? IDK


## Installation (HACS)

1. Ensure [HACS](https://custom-components.github.io/hacs/installation/manual/) is installed.
2. Add `https://github.com/flip-dots/HaSolixBLE` as a [custom repository](https://custom-components.github.io/hacs/usage/settings/#add-custom-repositories)
3. Install integration.
4. Restart your instance.


## Setup

1. Ensure device is in pairing mode. This can be achieved by pressing the IoT button or holding it to reset Bluetooth. The device indicator on the screen should be flashing.
2. Select the device in Home Assistant. It should be automatically detected.
3. Add the device and press confirm once prompted.


## Limitations

- This integration can only monitor the power station, it cannot control it (i.e turn things on and off).
- It is not possible to use Bluetooth and Wi-Fi at the same time.

I ran into some issues connecting using C1000 power station with the default configuration for ESP32 Bluetooth proxies, though my C300 worked fine. The following configuration fixed it:
```yaml
bluetooth_proxy:
  cache_services: false

esp32_ble_tracker:
  scan_parameters:
    active: true
```


## Adding support for new devices

Support for new devices can be added by setting up this integration with an unsupported device and enabling debug logging, this causes the raw telemetry data and differences between values between updates to be printed to the debug log, this can be used to determine what bytes mean what by turning things on and off and finding what corresponds with that in the log. You are welcome to submit a PR to the underlying library [SolixBLE](https://github.com/flip-dots/SolixBLE) to add support or to raise a GitHub issue with all of the indexes of the values and what they correspond to and I am happy to add support myself.
