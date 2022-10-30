"""Support for Freebox devices (Freebox v6 and Freebox mini 4K)."""
from __future__ import annotations

import logging

from freebox_api.exceptions import InsufficientPermissionsError

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FreeboxEntity
from .const import DOMAIN
from .coordinator import FreeboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the buttons."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FreeboxButton(coordinator)])


class FreeboxButton(FreeboxEntity, ButtonEntity):
    """Representation of a Freebox button."""

    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_name = "Reboot"

    def __init__(
        self,
        coordinator: FreeboxDataUpdateCoordinator,
    ) -> None:
        """Initialize a Freebox button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id} {self.name}"

    async def async_press(self) -> None:
        """Press the button."""
        try:
            await self.coordinator.async_execute("system", "reboot")
            await self.coordinator.async_request_refresh()
        except InsufficientPermissionsError:
            _LOGGER.warning(
                "Home Assistant does not have permissions to modify the Freebox settings. Please refer to documentation"
            )
