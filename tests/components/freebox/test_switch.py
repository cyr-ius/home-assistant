"""Tests for the Freebox config flow."""
from unittest.mock import Mock

from homeassistant.components.freebox.const import DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


async def test_switch(hass: HomeAssistant, router: Mock, config_entry: Mock):
    """Test reboot button."""
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "switch.freebox_wifi",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("switch.freebox_wifi").state == "on"
