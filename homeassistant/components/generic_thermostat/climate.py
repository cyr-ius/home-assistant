"""Adds support for generic thermostat units."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
import math
from typing import Any

import voluptuous as vol

from homeassistant.components.climate import (
    ATTR_PRESET_MODE,
    PLATFORM_SCHEMA,
    PRESET_ACTIVITY,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_HOME,
    PRESET_NONE,
    PRESET_SLEEP,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    CONF_NAME,
    CONF_UNIQUE_ID,
    EVENT_HOMEASSISTANT_START,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import DOMAIN as HA_DOMAIN, CoreState, HomeAssistant, callback
from homeassistant.exceptions import ConditionError
from homeassistant.helpers import condition
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

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
    DEFAULT_NAME,
    DEFAULT_TOLERANCE,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


CONF_PRESETS = {
    p: f"{p}_temp"
    for p in (
        PRESET_AWAY,
        PRESET_COMFORT,
        PRESET_HOME,
        PRESET_SLEEP,
        PRESET_ACTIVITY,
    )
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HEATER): cv.entity_id,
        vol.Required(CONF_SENSOR): cv.entity_id,
        vol.Optional(CONF_AC_MODE): cv.boolean,
        vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
        vol.Optional(CONF_MIN_DUR): cv.positive_time_period,
        vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_COLD_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
        vol.Optional(CONF_HOT_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
        vol.Optional(CONF_TARGET_TEMP): vol.Coerce(float),
        vol.Optional(CONF_KEEP_ALIVE): cv.positive_time_period,
        vol.Optional(CONF_INITIAL_HVAC_MODE): vol.In(
            [HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF]
        ),
        vol.Optional(CONF_PRECISION): vol.In(
            [PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE]
        ),
        vol.Optional(CONF_TEMP_STEP): vol.In(
            [PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE]
        ),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
).extend({vol.Optional(v): vol.Coerce(float) for (k, v) in CONF_PRESETS.items()})


# Deprecated in Home Assistant 2023.9
async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the generic thermostat platform."""
    async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml",
        breaks_in_ha_version="2023.9.0",
        is_fixable=False,
        severity=IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
    )

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


def convert_timedelta(value: str) -> timedelta:
    """Convert string to deltatime."""
    return (
        datetime.combine(datetime.min, datetime.strptime(value, "%H:%M:%S").time())
        - datetime.min
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a generic Thermostat."""
    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)
    unit = hass.config.units.temperature_unit
    async_add_entities([GenericThermostat(entry, unit)])


class GenericThermostat(ClimateEntity, RestoreEntity):
    """Representation of a Generic Thermostat device."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, unit: str) -> None:
        """Initialize the thermostat."""
        entity_config = entry.options
        presets = {
            key: entity_config[value]
            for key, value in CONF_PRESETS.items()
            if value in entity_config
        }

        self.heater_entity_id = entity_config[CONF_HEATER]
        self.sensor_entity_id = entity_config[CONF_SENSOR]
        self.ac_mode = entity_config[CONF_AC_MODE]
        self._cold_tolerance = entity_config.get(CONF_COLD_TOLERANCE)
        self._hot_tolerance = entity_config.get(CONF_HOT_TOLERANCE)
        self._keep_alive = (
            convert_timedelta(keep_alive)
            if (keep_alive := entity_config.get(CONF_KEEP_ALIVE))
            else None
        )
        self.min_cycle_duration = (
            convert_timedelta(min_cycle_duration)
            if (min_cycle_duration := entity_config.get(CONF_MIN_DUR))
            else None
        )
        self._active = False
        self._temp_lock = asyncio.Lock()

        self._attr_name = entry.data.get(CONF_NAME)
        self._attr_temperature_unit = unit
        self._attr_unique_id = entity_config.get(CONF_UNIQUE_ID, entry.entry_id)
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_current_temperature = None
        self._attr_min_temp: float = entity_config[CONF_MIN_TEMP]
        self._attr_max_temp: float = entity_config[CONF_MAX_TEMP]
        self._attr_target_temperature_step = float(
            entity_config.get(CONF_TEMP_STEP, 0.5)
        )
        self._attr_target_temperature = entity_config.get(CONF_TARGET_TEMP)
        self._attr_precision = float(entity_config.get(CONF_PRECISION, 0.5))
        self._attr_hvac_mode = entity_config.get(CONF_INITIAL_HVAC_MODE)
        self._attr_hvac_modes = (
            [HVACMode.COOL, HVACMode.OFF]
            if self.ac_mode
            else [HVACMode.HEAT, HVACMode.OFF]
        )
        self._attr_preset_mode = PRESET_NONE
        self._attr_preset_modes = [PRESET_NONE]
        if len(presets):
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
            self._attr_preset_modes = [PRESET_NONE] + list(presets.keys())

        self._presets = presets
        self._saved_target_temp = self._attr_target_temperature or next(
            iter(presets.values()), None
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Add listener
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.sensor_entity_id], self._async_sensor_changed
            )
        )
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.heater_entity_id], self._async_switch_changed
            )
        )

        if self._keep_alive:
            self.async_on_remove(
                async_track_time_interval(
                    self.hass, self._async_control_heating, self._keep_alive
                )
            )

        @callback
        def _async_startup(*_):
            """Init on startup."""
            sensor_state = self.hass.states.get(self.sensor_entity_id)
            if sensor_state and sensor_state.state not in (
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                self._async_update_temp(sensor_state)
                self.async_write_ha_state()
            switch_state = self.hass.states.get(self.heater_entity_id)
            if switch_state and switch_state.state not in (
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                self.hass.create_task(self._check_switch_initial_state())

        if self.hass.state == CoreState.running:
            _async_startup()
        else:
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _async_startup)

        # Check If we have an old state
        if (old_state := await self.async_get_last_state()) is not None:
            # If we have no initial temperature, restore
            if self._attr_target_temperature is None:
                # If we have a previously saved temperature
                if old_state.attributes.get(ATTR_TEMPERATURE) is None:
                    if self.ac_mode:
                        self._attr_target_temperature = self._attr_max_temp
                    else:
                        self._attr_target_temperature = self._attr_min_temp
                    _LOGGER.warning(
                        "Undefined target temperature, falling back to %s",
                        self._attr_target_temperature,
                    )
                else:
                    self._attr_target_temperature = float(
                        old_state.attributes[ATTR_TEMPERATURE]
                    )
            if (
                self._attr_preset_modes
                and old_state.attributes.get(ATTR_PRESET_MODE)
                in self._attr_preset_modes
            ):
                self._attr_preset_mode = old_state.attributes.get(ATTR_PRESET_MODE)
            if not self._attr_hvac_mode and old_state.state:
                self._attr_hvac_mode = old_state.state

        else:
            # No previous state, try and restore defaults
            if self._attr_target_temperature is None:
                if self.ac_mode:
                    self._attr_target_temperature = self._attr_max_temp
                else:
                    self._attr_target_temperature = self._attr_min_temp
            _LOGGER.warning(
                "No previously saved temperature, setting to %s",
                self._attr_target_temperature,
            )

        # Set default state to off
        if not self._attr_hvac_mode:
            self._attr_hvac_mode = HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation if supported.

        Need to be one of CURRENT_HVAC_*.
        """
        if self._attr_hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if not self._is_device_active:
            return HVACAction.IDLE
        if self.ac_mode:
            return HVACAction.COOLING
        return HVACAction.HEATING

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            self._attr_hvac_mode = HVACMode.HEAT
            await self._async_control_heating(force=True)
        elif hvac_mode == HVACMode.COOL:
            self._attr_hvac_mode = HVACMode.COOL
            await self._async_control_heating(force=True)
        elif hvac_mode == HVACMode.OFF:
            self._attr_hvac_mode = HVACMode.OFF
            if self._is_device_active:
                await self._async_heater_turn_off()
        else:
            _LOGGER.error("Unrecognized hvac mode: %s", hvac_mode)
            return
        # Ensure we update the current operation after changing the mode
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._attr_target_temperature = temperature
        await self._async_control_heating(force=True)
        self.async_write_ha_state()

    async def _async_sensor_changed(self, event) -> None:
        """Handle temperature changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self._async_update_temp(new_state)
        await self._async_control_heating()
        self.async_write_ha_state()

    async def _check_switch_initial_state(self) -> None:
        """Prevent the device from keep running if HVACMode.OFF."""
        if self._attr_hvac_mode == HVACMode.OFF and self._is_device_active:
            _LOGGER.warning(
                (
                    "The climate mode is OFF, but the switch device is ON. Turning off"
                    " device %s"
                ),
                self.heater_entity_id,
            )
            await self._async_heater_turn_off()

    @callback
    def _async_switch_changed(self, event) -> None:
        """Handle heater switch state changes."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None:
            return
        if old_state is None:
            self.hass.create_task(self._check_switch_initial_state())
        self.async_write_ha_state()

    @callback
    def _async_update_temp(self, state) -> None:
        """Update thermostat with latest state from sensor."""
        try:
            cur_temp = float(state.state)
            if math.isnan(cur_temp) or math.isinf(cur_temp):
                raise ValueError(f"Sensor has illegal state {state.state}")
            self._attr_current_temperature = cur_temp
        except ValueError as ex:
            _LOGGER.error("Unable to update from sensor: %s", ex)

    async def _async_control_heating(self, time=None, force=False):
        """Check if we need to turn heating on or off."""
        async with self._temp_lock:
            if not self._active and None not in (
                self._attr_current_temperature,
                self._attr_target_temperature,
            ):
                self._active = True
                _LOGGER.info(
                    (
                        "Obtained current and target temperature. "
                        "Generic thermostat active. %s, %s"
                    ),
                    self._attr_current_temperature,
                    self._attr_target_temperature,
                )

            if not self._active or self._attr_hvac_mode == HVACMode.OFF:
                return

            # If the `force` argument is True, we
            # ignore `min_cycle_duration`.
            # If the `time` argument is not none, we were invoked for
            # keep-alive purposes, and `min_cycle_duration` is irrelevant.
            if not force and time is None and self.min_cycle_duration:
                if self._is_device_active:
                    current_state = STATE_ON
                else:
                    current_state = HVACMode.OFF
                try:
                    long_enough = condition.state(
                        self.hass,
                        self.heater_entity_id,
                        current_state,
                        self.min_cycle_duration,
                    )
                except ConditionError:
                    long_enough = False

                if not long_enough:
                    return

            too_cold = (
                self._attr_target_temperature
                >= self._attr_current_temperature + self._cold_tolerance
            )
            too_hot = (
                self._attr_current_temperature
                >= self._attr_target_temperature + self._hot_tolerance
            )
            if self._is_device_active:
                if (self.ac_mode and too_cold) or (not self.ac_mode and too_hot):
                    _LOGGER.info("Turning off heater %s", self.heater_entity_id)
                    await self._async_heater_turn_off()
                elif time is not None:
                    # The time argument is passed only in keep-alive case
                    _LOGGER.info(
                        "Keep-alive - Turning on heater heater %s",
                        self.heater_entity_id,
                    )
                    await self._async_heater_turn_on()
            else:
                if (self.ac_mode and too_hot) or (not self.ac_mode and too_cold):
                    _LOGGER.info("Turning on heater %s", self.heater_entity_id)
                    await self._async_heater_turn_on()
                elif time is not None:
                    # The time argument is passed only in keep-alive case
                    _LOGGER.info(
                        "Keep-alive - Turning off heater %s", self.heater_entity_id
                    )
                    await self._async_heater_turn_off()

    @property
    def _is_device_active(self) -> bool | None:
        """If the toggleable device is currently active."""
        if not self.hass.states.get(self.heater_entity_id):
            return None

        return self.hass.states.is_state(self.heater_entity_id, STATE_ON)

    async def _async_heater_turn_on(self) -> None:
        """Turn heater toggleable device on."""
        data = {ATTR_ENTITY_ID: self.heater_entity_id}
        await self.hass.services.async_call(
            HA_DOMAIN, SERVICE_TURN_ON, data, context=self._context
        )

    async def _async_heater_turn_off(self) -> None:
        """Turn heater toggleable device off."""
        data = {ATTR_ENTITY_ID: self.heater_entity_id}
        await self.hass.services.async_call(
            HA_DOMAIN, SERVICE_TURN_OFF, data, context=self._context
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in (self._attr_preset_modes or []):
            raise ValueError(
                f"Got unsupported preset_mode {preset_mode}. Must be one of"
                f" {self._attr_preset_modes}"
            )
        if preset_mode == self._attr_preset_mode:
            # I don't think we need to call async_write_ha_state if we didn't change the state
            return
        if preset_mode == PRESET_NONE:
            self._attr_preset_mode = PRESET_NONE
            self._attr_target_temperature = self._saved_target_temp
            await self._async_control_heating(force=True)
        else:
            if self._attr_preset_mode == PRESET_NONE:
                self._saved_target_temp = self._attr_target_temperature
            self._attr_preset_mode = preset_mode
            self._attr_target_temperature = self._presets[preset_mode]
            await self._async_control_heating(force=True)

        self.async_write_ha_state()
