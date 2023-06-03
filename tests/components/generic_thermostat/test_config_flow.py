"""Test the Generic Thermostat config flow."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.generic_thermostat.const import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DOMAIN,
)
from homeassistant.const import PRECISION_TENTHS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry

CONFIG_OPTIONS = {
    "name": "Default Thermostat",
    "heater": "switch.any",
    "target_sensor": "sensor.any",
    "away_temp": 14.0,
    "comfort_temp": 19.5,
    "sleep_temp": 17.5,
    "hot_tolerance": 0.5,
    "cold_tolerance": 0.5,
    "keep_alive": "00:05:00",
    "min_cycle_duration": "00:05:00",
}

CONFIG_OPTIONS_CHANGE = {
    "heater": "switch.any",
    "target_sensor": "sensor.any",
    "comfort_temp": 20,
    "hot_tolerance": 0.1,
    "cold_tolerance": 0.1,
    "keep_alive": "00:01:00",
}

CONFIG_OPTIONS_RETURN = {
    "heater": "switch.any",
    "target_sensor": "sensor.any",
    "comfort_temp": 20.0,
    "hot_tolerance": 0.1,
    "cold_tolerance": 0.1,
    "keep_alive": "00:01:00",
    "ac_mode": False,
    "min_temp": DEFAULT_MIN_TEMP,
    "max_temp": DEFAULT_MAX_TEMP,
    "target_temp_step": str(PRECISION_TENTHS),
}


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the forms."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "homeassistant.components.generic_thermostat.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG_OPTIONS
        )
        await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1
    assert result["type"] == FlowResultType.CREATE_ENTRY


async def test_already_configured(hass: HomeAssistant) -> None:
    """Test we get the forms."""

    entry = MockConfigEntry(
        domain=DOMAIN, data={"name": "Default Thermostat"}, options=CONFIG_OPTIONS
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "homeassistant.components.generic_thermostat.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG_OPTIONS
        )
        await hass.async_block_till_done()
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_import_step(hass: HomeAssistant) -> None:
    """Test initializing via import step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=CONFIG_OPTIONS
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY


async def test_options(hass: HomeAssistant) -> None:
    """Test updating options."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={"name": "Default Thermostat"}, options=CONFIG_OPTIONS
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=CONFIG_OPTIONS_CHANGE,
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == CONFIG_OPTIONS_RETURN
