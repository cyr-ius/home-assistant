"""The tests for the Proximity component."""

from homeassistant.components.proximity.const import DOMAIN

from tests.common import MockConfigEntry

MOCK_ENTRY = {
    "zone": "home",
    "ignored_zones": ["work"],
    "devices": ["device_tracker.test1", "device_tracker.test2"],
    "tolerance": 1,
}

MOCK_ENTRY_ONE_TRACKER = {
    "zone": "home",
    "ignored_zones": ["work"],
    "devices": ["device_tracker.test1"],
    "tolerance": 1,
}

MOCK_ENTRY_TOLERANCE = {
    "zone": "home",
    "ignored_zones": ["work"],
    "devices": ["device_tracker.test1"],
    "tolerance": 1000,
}


async def test_proximity(hass):
    """Test the proximity."""
    mock_entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY)
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.proximity_home")
    assert state.state == "0"
    assert state.attributes.get("nearest") == "not set"
    assert state.attributes.get("dir_of_travel") == "not set"

    hass.states.async_set("sensor.proximity_home", "10")
    state = hass.states.get("sensor.proximity_home")
    assert state.state == "10"


async def test_device_tracker_test1_in_zone(hass):
    """Test for tracker in zone."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY_ONE_TRACKER
    )
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "home",
        {"friendly_name": "test1", "latitude": 2.1, "longitude": 1.1},
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.proximity_home")
    assert state.state == "0"
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "arrived"


async def test_device_trackers_in_zone(hass):
    """Test for trackers in zone."""
    mock_entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY)
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "home",
        {"friendly_name": "test1", "latitude": 2.1, "longitude": 1.1},
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "device_tracker.test2",
        "home",
        {"friendly_name": "test2", "latitude": 2.1, "longitude": 1.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.state == "0"
    assert (state.attributes.get("nearest") == "test1, test2") or (
        state.attributes.get("nearest") == "test2, test1"
    )
    assert state.attributes.get("dir_of_travel") == "arrived"


async def test_device_tracker_test1_away(hass):
    """Test for tracker state away."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY_ONE_TRACKER
    )
    mock_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1, "longitude": 10.1},
    )

    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "unknown"


async def test_device_tracker_test1_awayfurther(hass):
    """Test for tracker state away further."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY_ONE_TRACKER
    )
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    config_zones(hass)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1, "longitude": 10.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "unknown"

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 40.1, "longitude": 20.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "away_from"


async def test_device_tracker_test1_awaycloser(hass):
    """Test for tracker state away closer."""
    config_zones(hass)
    await hass.async_block_till_done()

    mock_entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY_ONE_TRACKER
    )
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 40.1, "longitude": 20.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "unknown"

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1, "longitude": 10.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "towards"


async def test_all_device_trackers_in_ignored_zone(hass):
    """Test for tracker in ignored zone."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY_ONE_TRACKER
    )
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("device_tracker.test1", "work", {"friendly_name": "test1"})
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.state == "0"
    assert state.attributes.get("nearest") == "not set"
    assert state.attributes.get("dir_of_travel") == "not set"


async def test_device_tracker_test1_no_coordinates(hass):
    """Test for tracker with no coordinates."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY_ONE_TRACKER
    )
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1", "not_home", {"friendly_name": "test1"}
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "not set"
    assert state.attributes.get("dir_of_travel") == "not set"


async def test_device_tracker_test1_awayfurther_than_test2_first_test1(hass):
    """Test for tracker ordering."""
    config_zones(hass)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1", "not_home", {"friendly_name": "test1"}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "device_tracker.test2", "not_home", {"friendly_name": "test2"}
    )
    await hass.async_block_till_done()

    mock_entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY)
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1, "longitude": 10.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "unknown"

    hass.states.async_set(
        "device_tracker.test2",
        "not_home",
        {"friendly_name": "test2", "latitude": 40.1, "longitude": 20.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "unknown"


async def test_device_tracker_test1_awayfurther_than_test2_first_test2(hass):
    """Test for tracker ordering."""
    config_zones(hass)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1", "not_home", {"friendly_name": "test1"}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "device_tracker.test2", "not_home", {"friendly_name": "test2"}
    )
    await hass.async_block_till_done()

    mock_entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY)
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test2",
        "not_home",
        {"friendly_name": "test2", "latitude": 40.1, "longitude": 20.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test2"
    assert state.attributes.get("dir_of_travel") == "unknown"

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1, "longitude": 10.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "unknown"


async def test_device_tracker_test1_awayfurther_test2_in_ignored_zone(hass):
    """Test for tracker states."""
    hass.states.async_set(
        "device_tracker.test1", "not_home", {"friendly_name": "test1"}
    )
    await hass.async_block_till_done()
    hass.states.async_set("device_tracker.test2", "work", {"friendly_name": "test2"})
    await hass.async_block_till_done()

    mock_entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY)
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1, "longitude": 10.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "unknown"


async def test_device_tracker_test1_awayfurther_test2_first(hass):
    """Test for tracker state."""
    config_zones(hass)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1", "not_home", {"friendly_name": "test1"}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "device_tracker.test2", "not_home", {"friendly_name": "test2"}
    )
    await hass.async_block_till_done()

    mock_entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY)
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 10.1, "longitude": 5.1},
    )
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test2",
        "not_home",
        {"friendly_name": "test2", "latitude": 20.1, "longitude": 10.1},
    )
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 40.1, "longitude": 20.1},
    )
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 35.1, "longitude": 15.1},
    )
    await hass.async_block_till_done()

    hass.states.async_set("device_tracker.test1", "work", {"friendly_name": "test1"})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test2"
    assert state.attributes.get("dir_of_travel") == "unknown"


async def test_device_tracker_test1_awayfurther_a_bit(hass):
    """Test for tracker states."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY_TOLERANCE
    )
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1000001, "longitude": 10.1000001},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "unknown"

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1000002, "longitude": 10.1000002},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "stationary"


async def test_device_tracker_test1_nearest_after_test2_in_ignored_zone(hass):
    """Test for tracker states."""
    config_zones(hass)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1", "not_home", {"friendly_name": "test1"}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "device_tracker.test2", "not_home", {"friendly_name": "test2"}
    )
    await hass.async_block_till_done()

    mock_entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data=MOCK_ENTRY)
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1, "longitude": 10.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "unknown"

    hass.states.async_set(
        "device_tracker.test2",
        "not_home",
        {"friendly_name": "test2", "latitude": 10.1, "longitude": 5.1},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test2"
    assert state.attributes.get("dir_of_travel") == "unknown"

    hass.states.async_set(
        "device_tracker.test2",
        "work",
        {"friendly_name": "test2", "latitude": 12.6, "longitude": 7.6},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.proximity_home")
    assert state.attributes.get("nearest") == "test1"
    assert state.attributes.get("dir_of_travel") == "unknown"


def config_zones(hass):
    """Set up zones for test."""
    hass.config.components.add("zone")
    hass.states.async_set(
        "zone.home",
        "zoning",
        {"name": "home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )
    hass.states.async_set(
        "zone.work",
        "zoning",
        {"name": "work", "latitude": 2.3, "longitude": 1.3, "radius": 10},
    )
