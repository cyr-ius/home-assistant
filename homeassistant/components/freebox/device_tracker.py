"""Support for Freebox devices (Freebox v6 and Freebox mini 4K)."""
from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_DEVICE_NAME, DEVICE_ICONS, DOMAIN
from .coordinator import FreeboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up device tracker for Freebox component."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for mac in coordinator.data["device_trackers"].keys():
        entities.append(FreeboxDevice(coordinator, mac))

    async_add_entities(entities)


class FreeboxDevice(CoordinatorEntity[FreeboxDataUpdateCoordinator], ScannerEntity):
    """Representation of a Freebox device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: FreeboxDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize a Freebox device."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.device_id = self._attr_unique_id = device_id
        device = coordinator.data["device_trackers"][device_id]
        self._attr_name = device.get("primary_name", DEFAULT_DEVICE_NAME).strip()
        self._attr_icon = DEVICE_ICONS.get(device["host_type"], "mdi:help-network")

    @property
    def mac_address(self):
        """Return mac address."""
        return self.device_id

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        device = self.coordinator.data["device_trackers"][self.device_id]
        return device.get("active", False)

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.ROUTER

    @callback
    def _handle_coordinator_update(self) -> None:
        device = self.coordinator.data["device_trackers"][self.unique_id]
        if attrs := device.get("attrs"):
            self._attr_extra_state_attributes = attrs
            if (last_time_reachable := attrs.get("last_time_reachable")) and (
                last_time_activity := attrs.get("last_activity")
            ):
                # device
                self._attr_extra_state_attributes.update(
                    {
                        "last_time_reachable": datetime.fromtimestamp(
                            last_time_reachable
                        ),
                        "last_time_activity": datetime.fromtimestamp(
                            last_time_activity
                        ),
                    }
                )
        super()._handle_coordinator_update()
