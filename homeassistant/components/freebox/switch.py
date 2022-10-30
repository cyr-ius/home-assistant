"""Support for Freebox Delta, Revolution and Mini 4K."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

from freebox_api.exceptions import InsufficientPermissionsError

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FreeboxEntity
from .const import DOMAIN
from .coordinator import FreeboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class FreeboxSwitchRequiredKeysMixin:
    """Mixin for required keys."""

    async_turn_on: Callable[[FreeboxDataUpdateCoordinator], Awaitable]
    async_turn_off: Callable[[FreeboxDataUpdateCoordinator], Awaitable]
    is_on: Callable[[FreeboxDataUpdateCoordinator], bool]


@dataclass
class FreeboxSwitchEntityDescription(
    SwitchEntityDescription, FreeboxSwitchRequiredKeysMixin
):
    """Class describing Freebox button entities."""


SWITCH_DESCRIPTIONS: tuple[FreeboxSwitchEntityDescription, ...] = (
    FreeboxSwitchEntityDescription(
        key="wifi",
        name="WiFi",
        entity_category=EntityCategory.CONFIG,
        async_turn_on=lambda coordinator: coordinator.async_execute(
            "wifi", "set_global_config", {"enabled": True}
        ),
        async_turn_off=lambda coordinator: coordinator.async_execute(
            "wifi", "set_global_config", {"enabled": False}
        ),
        is_on=lambda coordinator: coordinator.data["wifi"].get("enabled", False)
        is True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the switch."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        FreeboxSwitch(coordinator, entity_description)
        for entity_description in SWITCH_DESCRIPTIONS
    ]
    async_add_entities(entities)


class FreeboxSwitch(FreeboxEntity, SwitchEntity):
    """Representation of a freebox wifi switch."""

    entity_description: FreeboxSwitchEntityDescription

    def __init__(
        self,
        coordinator: FreeboxDataUpdateCoordinator,
        description: FreeboxSwitchEntityDescription,
    ) -> None:
        """Initialize the Wifi switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self.coordinator.entry.entry_id} {self.name}"
        self._attr_device_info = coordinator.data["device_info"]

    async def _async_set_state(self, method_execute: Callable):
        """Turn the switch on or off."""
        try:
            await method_execute(self.coordinator)
            await self.coordinator.async_request_refresh()
        except InsufficientPermissionsError:
            _LOGGER.warning(
                "Home Assistant does not have permissions to modify the Freebox settings. Please refer to documentation"
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_set_state(self.entity_description.async_turn_on)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_set_state(self.entity_description.async_turn_off)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Get the state and update it."""
        self._attr_is_on = self.entity_description.is_on(self.coordinator)
        super()._handle_coordinator_update()
