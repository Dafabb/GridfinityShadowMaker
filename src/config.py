"""GSM configuration constants and defaults."""

# Default processing parameters
DEFAULT_THRESHOLD = 145
DEFAULT_OFFSET = 0.04
DEFAULT_TOKEN = 2.89
DEFAULT_RESOLUTION = 20

# Brand codes
BRAND_CODES = {
    "CL": "Channellock",
    "MW": "Milwaukee",
    "DW": "DeWalt",
    "WRA": "Wera",
    "TEK": "Tekton",
    "KNX": "Knipex",
    "HDX": "HDX",
    "ST": "Stanley",
}

# Token sizes by tool class
TOKEN_SUB_10 = 2.89   # inches, for tools under 10"
TOKEN_10_INCH = 2.82   # inches, for 10" class tools

# Gridfinity bin defaults
DEFAULT_BIN_HEIGHT = 2.8  # GF units
DEFAULT_CHAMFER_HEIGHT = 3
FILAMENT_CHANGE_HEIGHT = 19.8  # mm
