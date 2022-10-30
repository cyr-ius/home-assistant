"""Support for Freebox Delta, Revolution and Mini 4K."""
from __future__ import annotations

import logging
from typing import Any

from freebox_api.exceptions import InsufficientPermissionsError

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FreeboxEntity
from .const import DOMAIN
from .coordinator import FreeboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


SWITCH_DESCRIPTIONS = [
    SwitchEntityDescription(
        key="wifi",
        name="Freebox WiFi",
        entity_category=EntityCategory.CONFIG,
    )
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the switch."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FreeboxWifiSwitch(coordinator)])


class FreeboxWifiSwitch(FreeboxEntity, SwitchEntity):
    """Representation of a freebox wifi switch."""

    _attr_name = "WiFi"

    def __init__(self, coordinator: FreeboxDataUpdateCoordinator) -> None:
        """Initialize the Wifi switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.coordinator.entry.entry_id} {self.name}"
        self._attr_device_info = coordinator.data["device_info"]

    @callback
    async def _async_set_state(self, enabled: bool):
        """Turn the switch on or off."""
        try:
            await self.coordinator.async_execute(
                "wifi", "set_global_config", {"enabled": enabled}
            )
            await self.coordinator.async_request_refresh()
        except InsufficientPermissionsError:
            _LOGGER.warning(
                "Home Assistant does not have permissions to modify the Freebox settings. Please refer to documentation"
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_set_state(False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Get the state and update it."""
        self._attr_is_on = bool(self.coordinator.data["wifi"].get("enabled", False))
        super()._handle_coordinator_update()
