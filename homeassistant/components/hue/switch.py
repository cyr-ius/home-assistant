"""Hue sensor entities."""
from homeassistant.helpers.entity import Entity
from homeassistant.components.hue.sensor_base import (
    GenericZLLSensor, async_setup_entry as shared_async_setup_entry)


BUTTON_EVENT_NAME_FORMAT = "{}"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Defer sensor setup to the shared sensor module."""
    await shared_async_setup_entry(
        hass, config_entry, async_add_entities, binary=False)

class GenericHueGaugeSensorEntity(GenericZLLSensor, Entity):
    """Parent class for all 'gauge' Hue device sensors."""

    async def _async_update_ha_state(self, *args, **kwargs):
        await self.async_update_ha_state(self, *args, **kwargs)

class HueSwitch(GenericHueGaugeSensorEntity):
    """The dimmer sensor entity for a Hue sensor device."""

    @property
    def state(self):
        BUTTONS = {
                    34: "1_click", 16: "2_click", 17: "3_click", 18: "4_click",
                    1000: "1_click", 2000: "2_click", 3000: "3_click", 4000: "4_click",
                    1001: "1_hold", 2001: "2_hold", 3001: "3_hold", 4001: "4_hold",
                    1002: "1_click_up", 2002: "2_click_up", 3002: "3_click_up", 4002: "4_click_up",
                    1003: "1_hold_up", 2003: "2_hold_up", 3003: "3_hold_up", 4003: "4_hold_up",
        }
        """Return the state of the device."""
        return BUTTONS[self.sensor.buttonevent]

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return 'mdi:remote'
