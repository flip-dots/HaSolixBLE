"""Constants for the SolixBLE integration."""

from enum import Enum

DOMAIN = "solix_ble"


###############
# Port status #
###############

PORT_STATUS_STRINGS = ["Unknown", "Not connected", "Output", "Input"]


###################
# Charging status #
###################

CHARGING_STATUS_C300_STRINGS = ["Unknown", "Idle", "Discharging", "Charging"]

CHARGING_STATUS_F3800_STRINGS = [
    "Unknown",
    "Idle",
    "Charging (Solar)",
    "Charging (AC)",
    "Charging (Both)",
]


################
# Light status #
################

LIGHT_STATUS_STRINGS = ["Unknown", "Off", "Low", "Medium", "High"]

LIGHT_STATUS_SB2_STRINGS = ["Unknown", "Normal", "Mood"]


###################
# Overload status #
###################

OVERLOAD_STATUS_C300DC_STRINGS = ["Unknown", "None", "USB C1", "USB C2", "USB C3"]


###################
# Max load status #
###################

MAX_LOAD_SB2_STRINGS = ["Unknown", "350w", "600w", "800w", "1000w"]


###############
# Grid status #
###############

GRID_STATUS_STRINGS = ["Unknown", "Ok", "Ok?", "Connecting", "No grid"]


##############
# Usage mode #
##############

USAGE_MODE_SB2_STRINGS = [
    "Unknown",
    "Manual",
    "Smart meter",
    "Smart plugs",
    "Backup",
    "Use Time",
    "Smart",
    "Time slot",
]


##################
# Battery cutoff #
##################

CUT_OFF_SB2_STRINGS = ["Unknown", "5%", "10%"]


####################
# Supported models #
####################


class Models(Enum):
    C300 = "C300(X)"
    C300DC = "C300(X) DC"
    C800 = "C800(X)"
    C1000 = "C1000(X)"
    C1000G2 = "C1000(X) Gen 2"
    F2000 = "F2000 (767)"
    F2000_OLD = "F2000 (767) (old firmware)"
    F2600 = "F2600"
    F3800 = "F3800"
    PRIME_CHARGER_160 = "Prime Charger (160w)"
    PRIME_CHARGER_250 = "Prime Charger (250w)"
    PRIME_POWER_BANK_20K = "Prime Power Bank 20k (220w)"
    SOLARBANK_2 = "Solarbank 2"
    MAGGO_3IN1 = "MagGo 3-in-1 Wireless Charger (A25x7)"
    UNKNOWN = "Unknown"
