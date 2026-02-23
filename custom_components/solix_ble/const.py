"""Constants for the SolixBLE integration."""

from enum import Enum

DOMAIN = "solix_ble"

PORT_STATUS_STRINGS = ["Unknown", "Not connected", "Output", "Input"]

LIGHT_STATUS_STRINGS = ["Unknown", "Off", "Low", "Medium", "High"]


class Models(Enum):
    C300 = "C300(X)"
    C1000 = "C1000(X)"
    UNKNOWN = "Unknown"
