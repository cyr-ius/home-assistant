"""The tests config_flow for Proximity component."""
from collections import OrderedDict

from homeassistant import config_entries, data_entry_flow
from homeassistant.components.proximity.const import DOMAIN
from homeassistant.helpers import entity_registry

from tests.common import MockEntity, MockEntityPlatform, mock_registry

MOCK_IMPORT = {
    "home": {
        "ignored_zones": ["work", "school"],
        "devices": ["device_tracker.car1", "device_tracker.iphone1"],
        "tolerance": 50,
        "unit_of_measurement": "mi",
    },
    "work": {"zone": "work", "devices": ["person.paulus"], "tolerance": 10},
}

MOCK_MANUAL = {
    "zone": "test home",
    "ignored_zones": ["work"],
    "devices": ["device_tracker.car1", "device_tracker.iphone1"],
    "tolerance": 50,
    "unit_of_measurement": "mi",
}


async def test_form_import(hass):
    """Test we get the form with import source."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=MOCK_MANUAL,
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_form(hass):
    """Test we get the form with user source."""
    entities = OrderedDict()
    entities["device_tracker.car1"] = entity_registry.RegistryEntry(
        entity_id="device_tracker.car1",
        unique_id="test-unique-id",
        platform="test-platform",
    )
    entities["device_tracker.car2"] = entity_registry.RegistryEntry(
        entity_id="device_tracker.car2",
        unique_id="test-unique-id",
        platform="test-platform",
    )
    entities["device_tracker.iphone1"] = entity_registry.RegistryEntry(
        entity_id="device_tracker.iphone1",
        unique_id="test-unique-id",
        platform="test-platform",
    )
    mock_registry(hass, entities)

    platform = MockEntityPlatform(hass, domain="zone", platform_name="zone")
    entities = [
        MockEntity(entity_id="zone.work", name="work", unique_id="test-unique-id-2"),
    ]
    await platform.async_add_entities(entities)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_MANUAL,
    )

    await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
