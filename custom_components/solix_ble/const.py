"""Constants for the SolixBLE integration."""

from enum import Enum

DOMAIN = "solix_ble"

PORT_STATUS_STRINGS = ["Unknown", "Not connected", "Output", "Input"]

CHARGING_STATUS_C300_STRINGS = ["Unknown", "Idle", "Discharging", "Charging"]

CHARGING_STATUS_C300DC_STRINGS = [
    "Unknown",
    "Idle",
    "Charging (Solar)",
    "Charging (DC)",
    "Charging (Both)",
]

CHARGING_STATUS_F3800_STRINGS = [
    "Unknown",
    "Idle",
    "Charging (Solar)",
    "Charging (AC)",
    "Charging (Both)",
]

LIGHT_STATUS_STRINGS = ["Unknown", "Off", "Low", "Medium", "High"]


class Models(Enum):
    C300 = "C300(X)"
    C300DC = "C300(X) DC"
    C800 = "C800(X)"
    C1000 = "C1000(X)"
    C1000G2 = "C1000(X) Gen 2"
    F2000 = "F2000 (767)"
    F3800 = "F3800"
    PRIME_CHARGER_160 = "Prime Charger (160w)"
    PRIME_CHARGER_250 = "Prime Charger (250w)"
    UNKNOWN = "Unknown"
