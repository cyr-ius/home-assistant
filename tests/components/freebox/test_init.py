"""Tests for the Freebox config flow."""
from unittest.mock import Mock

from homeassistant.components.freebox.const import DOMAIN as DOMAIN, SERVICE_REBOOT
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .const import MOCK_HOST, MOCK_PORT


async def test_setup(hass: HomeAssistant, router: Mock, config_entry: Mock):
    """Test setup of integration."""
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE_REBOOT)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_REBOOT,
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_setup_import(hass: HomeAssistant, router: Mock, config_entry: Mock):
    """Test setup of integration from import."""
    assert await async_setup_component(
        hass, DOMAIN, {DOMAIN: {CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT}}
    )
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE_REBOOT)
