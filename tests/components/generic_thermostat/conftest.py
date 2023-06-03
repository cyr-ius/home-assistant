"""Common fixtures and objects for integration tests."""
import pytest

from homeassistant.components.climate import HVACMode
from homeassistant.components.generic_thermostat.const import DOMAIN
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.unit_system import METRIC_SYSTEM

from tests.common import MockConfigEntry

ENT_SENSOR = "sensor.test"
ENT_SWITCH = "switch.test"


@pytest.fixture
async def setup_comp_1(hass: HomeAssistant):
    """Initialize components."""
    hass.config.units = METRIC_SYSTEM
    assert await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()


@pytest.fixture
async def setup_comp_2(hass: HomeAssistant):
    """Initialize components."""
    hass.config.units = METRIC_SYSTEM
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "test"},
        options={
            "name": "test",
            "cold_tolerance": 2,
            "hot_tolerance": 4,
            "heater": ENT_SWITCH,
            "target_sensor": ENT_SENSOR,
            "away_temp": 16,
            "sleep_temp": 17,
            "home_temp": 19,
            "comfort_temp": 20,
            "activity_temp": 21,
            "initial_hvac_mode": HVACMode.HEAT,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
async def setup_comp_3(hass: HomeAssistant):
    """Initialize components."""
    hass.config.temperature_unit = UnitOfTemperature.CELSIUS
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "test"},
        options={
            "name": "test",
            "cold_tolerance": 2,
            "hot_tolerance": 4,
            "away_temp": 30,
            "heater": ENT_SWITCH,
            "target_sensor": ENT_SENSOR,
            "ac_mode": True,
            "initial_hvac_mode": HVACMode.COOL,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
async def setup_comp_4(hass: HomeAssistant):
    """Initialize components."""
    hass.config.temperature_unit = UnitOfTemperature.CELSIUS
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "test"},
        options={
            "name": "test",
            "cold_tolerance": 0.3,
            "hot_tolerance": 0.3,
            "heater": ENT_SWITCH,
            "target_sensor": ENT_SENSOR,
            "ac_mode": True,
            "min_cycle_duration": "00:10:00",
            "initial_hvac_mode": HVACMode.COOL,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
async def setup_comp_5(hass: HomeAssistant):
    """Initialize components."""
    hass.config.temperature_unit = UnitOfTemperature.CELSIUS
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "test"},
        options={
            "name": "test",
            "cold_tolerance": 0.3,
            "hot_tolerance": 0.3,
            "heater": ENT_SWITCH,
            "target_sensor": ENT_SENSOR,
            "ac_mode": True,
            "min_cycle_duration": "00:10:00",
            "initial_hvac_mode": HVACMode.COOL,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
async def setup_comp_6(hass: HomeAssistant):
    """Initialize components."""
    hass.config.temperature_unit = UnitOfTemperature.CELSIUS
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "test"},
        options={
            "name": "test",
            "cold_tolerance": 0.3,
            "hot_tolerance": 0.3,
            "heater": ENT_SWITCH,
            "target_sensor": ENT_SENSOR,
            "min_cycle_duration": "00:10:00",
            "initial_hvac_mode": HVACMode.HEAT,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
async def setup_comp_7(hass: HomeAssistant):
    """Initialize components."""
    hass.config.temperature_unit = UnitOfTemperature.CELSIUS
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "test"},
        options={
            "name": "test",
            "cold_tolerance": 0.3,
            "hot_tolerance": 0.3,
            "heater": ENT_SWITCH,
            "target_temp": 25,
            "target_sensor": ENT_SENSOR,
            "ac_mode": True,
            "min_cycle_duration": "00:10:00",
            "keep_alive": "00:10:00",
            "initial_hvac_mode": HVACMode.COOL,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
async def setup_comp_8(hass: HomeAssistant):
    """Initialize components."""
    hass.config.temperature_unit = UnitOfTemperature.CELSIUS
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "test"},
        options={
            "name": "test",
            "cold_tolerance": 0.3,
            "hot_tolerance": 0.3,
            "heater": ENT_SWITCH,
            "target_temp": 25,
            "target_sensor": ENT_SENSOR,
            "min_cycle_duration": "00:15:00",
            "keep_alive": "00:10:00",
            "initial_hvac_mode": HVACMode.HEAT,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
async def setup_comp_9(hass):
    """Initialize components."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "test"},
        options={
            "name": "test",
            "cold_tolerance": 0.3,
            "hot_tolerance": 0.3,
            "target_temp": 25,
            "heater": ENT_SWITCH,
            "target_sensor": ENT_SENSOR,
            "min_cycle_duration": "00:15:00",
            "keep_alive": "00:10:00",
            "precision": 0.1,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
