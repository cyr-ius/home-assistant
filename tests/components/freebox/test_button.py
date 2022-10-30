"""Tests for the Freebox config flow."""
from unittest.mock import Mock

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.freebox.const import DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


async def test_reboot_button(hass: HomeAssistant, router: Mock, config_entry: Mock):
    """Test reboot button."""
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        service_data={
            ATTR_ENTITY_ID: "button.reboot_freebox",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
