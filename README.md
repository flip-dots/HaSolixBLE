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

- C300(X)
- C1000(X)
- Maybe more? IDK

## Installation (HACS)

1. Ensure [HACS](https://custom-components.github.io/hacs/installation/manual/) is installed.
2. Add `https://github.com/flip-dots/HaSolixBLE` as a [custom repository](https://custom-components.github.io/hacs/usage/settings/#add-custom-repositories)
3. Install integration.
4. Restart your instance.

## Setup

1. Ensure the connection light is blinking. This can be achieved by pressing the IoT button or holding it to reset Bluetooth. The device indicator on the screen should be flashing.
2. Go to the devices page in Home Assistant and click Add on the power station. It should be automatically detected.
3. Select the correct model for your power station in the drop down. If your model is not supported select unknown and follow the steps for adding support for a new device below.
4. Click confirm, the device should be added, this may take a while as a connection is negotiated.
5. Profit???

## Limitations

- This integration can only monitor the power station, it cannot control it (i.e turn things on and off).
- It is not possible to use Bluetooth and Wi-Fi at the same time.

I ran into some issues connecting a C1000 power station with the default configuration for ESP32 Bluetooth proxies, though my C300 worked fine. The following configuration fixed it:

```yaml
bluetooth_proxy:
  cache_services: false

esp32_ble_tracker:
  scan_parameters:
    active: true
```

## Adding support for new devices

Support for new devices can be added by setting up this integration with an unsupported device and enabling debug logging, this causes the raw telemetry data and differences between values between updates to be printed to the debug log, this can be used to determine what bytes mean what by turning things on and off and finding what value change corresponds with that in the log. You are welcome to submit a PR to the underlying library [SolixBLE](https://github.com/flip-dots/SolixBLE) to add support or to raise a GitHub issue with all of the indexes of the values and what they correspond to and I am happy to add support myself.
