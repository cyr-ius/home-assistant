"""Config flow for generic Thermostat."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.climate import (
    PRESET_ACTIVITY,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_HOME,
    PRESET_SLEEP,
    HVACMode,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlowWithConfigEntry,
)
from homeassistant.const import (
    CONF_NAME,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TimeSelector,
)

from .const import (
    CONF_AC_MODE,
    CONF_COLD_TOLERANCE,
    CONF_HEATER,
    CONF_HOT_TOLERANCE,
    CONF_INITIAL_HVAC_MODE,
    CONF_KEEP_ALIVE,
    CONF_MAX_TEMP,
    CONF_MIN_DUR,
    CONF_MIN_TEMP,
    CONF_PRECISION,
    CONF_SENSOR,
    CONF_TARGET_TEMP,
    CONF_TEMP_STEP,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DEFAULT_NAME,
    DEFAULT_TOLERANCE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

HVAC_MODE = [
    SelectOptionDict(value=HVACMode.COOL, label=HVACMode.COOL),
    SelectOptionDict(value=HVACMode.HEAT, label=HVACMode.HEAT),
    SelectOptionDict(value=HVACMode.OFF, label=HVACMode.OFF),
]

PRECISION = [
    SelectOptionDict(value=str(PRECISION_TENTHS), label=str(PRECISION_TENTHS)),
    SelectOptionDict(value=str(PRECISION_HALVES), label=str(PRECISION_HALVES)),
    SelectOptionDict(value=str(PRECISION_WHOLE), label=str(PRECISION_WHOLE)),
]

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HEATER): EntitySelector(),
        vol.Required(CONF_SENSOR): EntitySelector(
            EntitySelectorConfig(device_class=SensorDeviceClass.TEMPERATURE)
        ),
        vol.Required(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Required(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Required(CONF_AC_MODE, default=False): BooleanSelector(),
        vol.Required(CONF_COLD_TOLERANCE, default=DEFAULT_TOLERANCE): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Required(CONF_HOT_TOLERANCE, default=DEFAULT_TOLERANCE): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Optional(CONF_MIN_DUR): TimeSelector(),
        vol.Optional(CONF_TARGET_TEMP): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Optional(CONF_KEEP_ALIVE): TimeSelector(),
        vol.Optional(CONF_INITIAL_HVAC_MODE): SelectSelector(
            SelectSelectorConfig(options=HVAC_MODE, mode=SelectSelectorMode.DROPDOWN)
        ),
        vol.Optional(CONF_PRECISION): SelectSelector(
            SelectSelectorConfig(options=PRECISION, mode=SelectSelectorMode.DROPDOWN)
        ),
        vol.Optional(CONF_TEMP_STEP): SelectSelector(
            SelectSelectorConfig(options=PRECISION, mode=SelectSelectorMode.DROPDOWN)
        ),
        vol.Optional(f"{PRESET_AWAY}_temp"): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Optional(f"{PRESET_COMFORT}_temp"): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Optional(f"{PRESET_HOME}_temp"): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Optional(f"{PRESET_SLEEP}_temp"): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=0.1)
        ),
        vol.Optional(f"{PRESET_ACTIVITY}_temp"): NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=0.1)
        ),
    }
)


class GenericThermostatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for generic Thermostat."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> GenericThermostatOptionsFlowHandler:
        """Get option flow."""
        return GenericThermostatOptionsFlowHandler(config_entry)

    async def async_step_import(self, config: dict[str, Any]) -> FlowResult:
        """Import a config entry from configuration.yaml."""
        self._async_abort_entries_match({CONF_NAME: config[CONF_NAME]})
        if keep_alive := config.get(CONF_KEEP_ALIVE):
            config[CONF_KEEP_ALIVE] = str(
                datetime.strptime(str(keep_alive), "%H:%M:%S").time()
            )
        if min_dur := config.get(CONF_MIN_DUR):
            config[CONF_MIN_DUR] = str(
                datetime.strptime(str(min_dur), "%H:%M:%S").time()
            )
        return await self.async_step_user(user_input=config)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the start of the config flow."""
        if user_input is not None:
            self._async_abort_entries_match(
                {
                    CONF_HEATER: user_input[CONF_HEATER],
                    CONF_SENSOR: user_input[CONF_SENSOR],
                }
            )
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data={CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME)},
                options=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA.extend(
                {vol.Optional(CONF_NAME, default=DEFAULT_NAME): TextSelector()}
            ),
        )


class GenericThermostatOptionsFlowHandler(OptionsFlowWithConfigEntry):
    """Handle option."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, self.options),
        )
