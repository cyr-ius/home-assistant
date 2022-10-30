"""Support for Freebox devices (Freebox v6 and Freebox mini 4K)."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging

from freebox_api.exceptions import InsufficientPermissionsError

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FreeboxEntity
from .const import DOMAIN
from .coordinator import FreeboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class FreeboxButtonRequiredKeysMixin:
    """Mixin for required keys."""

    async_press: Callable[[FreeboxDataUpdateCoordinator], Awaitable]


@dataclass
class FreeboxButtonEntityDescription(
    ButtonEntityDescription, FreeboxButtonRequiredKeysMixin
):
    """Class describing Freebox button entities."""


BUTTON_DESCRIPTIONS: tuple[FreeboxButtonEntityDescription, ...] = (
    FreeboxButtonEntityDescription(
        key="reboot",
        name="Reboot",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        async_press=lambda coordinator: coordinator.async_execute("system", "reboot"),
    ),
    FreeboxButtonEntityDescription(
        key="mark_calls_as_read",
        name="Mark calls as read",
        entity_category=EntityCategory.DIAGNOSTIC,
        async_press=lambda coordinator: coordinator.async_execute(
            "call", "mark_calls_log_as_read"
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the buttons."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        FreeboxButton(coordinator, description) for description in BUTTON_DESCRIPTIONS
    ]
    async_add_entities(entities)


class FreeboxButton(FreeboxEntity, ButtonEntity):
    """Representation of a Freebox button."""

    entity_description: FreeboxButtonEntityDescription

    def __init__(
        self,
        coordinator: FreeboxDataUpdateCoordinator,
        description: FreeboxButtonEntityDescription,
    ) -> None:
        """Initialize a Freebox button."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id} {self.name}"

    async def async_press(self) -> None:
        """Press the button."""
        try:
            await self.entity_description.async_press(self.coordinator)
            await self.coordinator.async_request_refresh()
        except InsufficientPermissionsError:
            _LOGGER.warning(
                "Home Assistant does not have permissions to modify the Freebox settings. Please refer to documentation"
            )
