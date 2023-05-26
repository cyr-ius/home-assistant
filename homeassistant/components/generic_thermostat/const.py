"""Add constants for generic thermostat integration."""
from homeassistant.const import Platform

DOMAIN = "generic_thermostat"
PLATFORMS = [Platform.CLIMATE]

CONF_AC_MODE = "ac_mode"
CONF_COLD_TOLERANCE = "cold_tolerance"
CONF_HEATER = "heater"
CONF_HOT_TOLERANCE = "hot_tolerance"
CONF_INITIAL_HVAC_MODE = "initial_hvac_mode"
CONF_KEEP_ALIVE = "keep_alive"
CONF_MAX_TEMP = "max_temp"
CONF_MIN_DUR = "min_cycle_duration"
CONF_MIN_TEMP = "min_temp"
CONF_PRECISION = "precision"
CONF_SENSOR = "target_sensor"
CONF_TARGET_TEMP = "target_temp"
CONF_TEMP_STEP = "target_temp_step"
DEFAULT_MAX_TEMP = 30
DEFAULT_MIN_TEMP = 7
DEFAULT_NAME = "Generic Thermostat"
DEFAULT_TOLERANCE = 0.3
