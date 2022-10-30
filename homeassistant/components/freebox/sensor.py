"""Support for Freebox devices (Freebox v6 and Freebox mini 4K)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from . import FreeboxEntity
from .const import CALL_SENSORS, CONNECTION_SENSORS, DISK_PARTITION_SENSORS, DOMAIN
from .coordinator import FreeboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[FreeboxEntity] = []

    temperature_sensors_list = [
        SensorEntityDescription(
            key=sensor_name,
            name=sensor_name,
            native_unit_of_measurement=TEMP_CELSIUS,
        )
        for sensor_name in coordinator.data["sensors"]
    ]
    temperature_sensors: tuple[SensorEntityDescription, ...] = tuple(
        temperature_sensors_list
    )

    entities.extend(
        [
            FreeboxTemperatureSensor(coordinator, description)
            for description in temperature_sensors
        ]
    )
    entities.extend(
        [
            FreeboxConnectionSensor(coordinator, description)
            for description in CONNECTION_SENSORS
        ]
    )
    entities.extend(
        [FreeboxCallSensor(coordinator, description) for description in CALL_SENSORS]
    )
    entities.extend(
        [
            FreeboxDiskSensor(coordinator, description, disk, partition)
            for disk in coordinator.data["disks"].values()
            for partition in disk["partitions"]
            for description in DISK_PARTITION_SENSORS
        ]
    )

    async_add_entities(entities)


class FreeboxTemperatureSensor(FreeboxEntity, SensorEntity):
    """Representation of a Freebox temperature sensor."""

    def __init__(
        self,
        coordinator: FreeboxDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize a Freebox sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id} {description.name}"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the Freebox sensor."""
        self._attr_native_value = self.coordinator.data["sensors"][
            self.entity_description.key
        ]
        super()._handle_coordinator_update()


class FreeboxCallSensor(FreeboxEntity, SensorEntity):
    """Representation of a Freebox call sensor."""

    def __init__(
        self,
        coordinator: FreeboxDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize a Freebox call sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id} {description.name}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the Freebox call sensor."""
        call_list_for_type = []
        if call_list := self.coordinator.data["call_list"]:
            for call in call_list:
                if not call["new"]:
                    continue
                if self.entity_description.key == call["type"]:
                    call_list_for_type.append(call)

        self._attr_extra_state_attributes = {
            dt_util.utc_from_timestamp(call["datetime"]).isoformat(): call["name"]
            for call in call_list_for_type
        }
        self._attr_native_value = len(call_list_for_type)
        super()._handle_coordinator_update()


class FreeboxConnectionSensor(FreeboxEntity, SensorEntity):
    """Representation of a Freebox temperature sensor."""

    def __init__(
        self,
        coordinator: FreeboxDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize a Freebox sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id} {description.name}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the Freebox sensor."""
        state = self.coordinator.data["sensors_connection"][self.entity_description.key]
        self._attr_native_value = round(state / 1000, 2)
        super()._handle_coordinator_update()


class FreeboxDiskSensor(FreeboxEntity, SensorEntity):
    """Representation of a Freebox disk sensor."""

    def __init__(
        self,
        coordinator: FreeboxDataUpdateCoordinator,
        description: SensorEntityDescription,
        disk: dict[str, Any],
        partition: dict[str, Any],
    ) -> None:
        """Initialize a Freebox disk sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._disk = disk
        self._partition = partition
        self._attr_name = f"{partition['label']} {description.name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id} {description.key} {disk['id']} {partition['id']}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._disk["id"])},
            model=self._disk["model"],
            name=f"Disk {self._disk['id']}",
            sw_version=self._disk["firmware"],
            via_device=(DOMAIN, self.coordinator.entry.entry_id),
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the Freebox disk sensor."""
        value = None
        if self._partition.get("total_bytes"):
            value = round(
                self._partition["free_bytes"] * 100 / self._partition["total_bytes"], 2
            )
        self._attr_native_value = value
        super()._handle_coordinator_update()
