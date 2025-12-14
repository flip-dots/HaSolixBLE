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


## Adding support for new devices

Support for new devices can be added by setting up this integration with an unsupported device and enabling debug logging, this causes the raw telemetry data and differences between values between updates to be printed to the debug log, this can be used to determine what bytes mean what by turning things on and off and finding what corresponds with that in the log. You are welcome to submit a PR to the underlying library [SolixBLE](https://github.com/flip-dots/SolixBLE) to add support or to raise a GitHub issue with all of the indexes of the values and what they correspond to and I am happy to add support myself.
