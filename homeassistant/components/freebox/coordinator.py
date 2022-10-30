"""Data Update Coordinator."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
from typing import Any

from freebox_api import Freepybox
from freebox_api.exceptions import AuthorizationError, HttpRequestError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import slugify

from .const import (
    API_VERSION,
    APP_DESC,
    CONNECTION_SENSORS_KEYS,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)

SCAN_INTERVAL = timedelta(seconds=60)
_LOGGER = logging.getLogger(__name__)


def get_api(hass: HomeAssistant, host: str) -> Freepybox:
    """Get the Freebox API."""
    freebox_path = Store(hass, STORAGE_VERSION, STORAGE_KEY).path
    if not os.path.exists(freebox_path):
        os.makedirs(freebox_path)
    token_file = Path(f"{freebox_path}/{slugify(host)}.conf")
    return Freepybox(APP_DESC, token_file, API_VERSION)


class FreeboxDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to fetch datas."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Class to manage fetching data API."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = get_api(hass, entry.data[CONF_HOST])
        self.hass = hass
        self.entry = entry

    async def _async_update_data(self) -> dict[Any, Any]:
        """Update data via API."""
        try:
            await self.api.open(self.entry.data[CONF_HOST], self.entry.data[CONF_PORT])
            return await self._async_update_sensors()
        except HttpRequestError as error:
            raise ConfigEntryAuthFailed from error
        except AuthorizationError as error:
            raise UpdateFailed(f"Error communicating with API: {error}") from error
        finally:
            await self.api.close()

    async def _async_update_sensors(self) -> dict[Any, Any]:
        """Update Freebox sensors."""
        # System sensors
        # According to the doc `syst_datas["sensors"]` is temperature sensors in celsius degree.
        # Name and id of sensors may vary under Freebox devices.
        sensors_temperature: dict[str, int] = {}
        syst_datas: dict[str, Any] = await self.api.system.get_config()
        for sensor in syst_datas["sensors"]:
            sensors_temperature[sensor["name"]] = sensor.get("value")

        # Unique id for Freebox and information.
        unique_id = syst_datas["mac"]
        name = syst_datas["model_info"].get("pretty_name", "Freebox")
        sw_version = syst_datas["firmware_version"]

        # Connection sensors
        sensors_connection: dict[str, float] = {}
        connection_datas: dict[str, Any] = await self.api.connection.get_status()
        for sensor_key in CONNECTION_SENSORS_KEYS:
            sensors_connection[sensor_key] = connection_datas[sensor_key]

        attrs = {
            "IPv4": connection_datas.get("ipv4"),
            "IPv6": connection_datas.get("ipv6"),
            "connection_type": connection_datas["media"],
            "uptime": datetime.fromtimestamp(
                round(datetime.now().timestamp()) - syst_datas["uptime_val"]
            ),
            "firmware_version": syst_datas["firmware_version"],
            "serial": syst_datas["serial"],
        }

        call_list = await self.api.call.get_calls_log()

        # Disks sensors
        disks: dict[int, dict[str, Any]] = {}
        fbx_disks: list[dict[str, Any]] = await self.api.storage.get_disks() or []
        for fbx_disk in fbx_disks:
            disks[fbx_disk["id"]] = fbx_disk

        # Call
        calls = self.api.call

        # Wifi
        wifi = await self.api.wifi.get_global_config()

        devices: dict[str, dict[str, Any]] = {}
        fbx_devices: list[dict[str, Any]] = await self.api.lan.get_hosts_list()
        # Adds the Freebox itself
        fbx_devices.append(
            {
                "primary_name": name,
                "l2ident": {"id": unique_id},
                "vendor_name": "Freebox SAS",
                "host_type": "router",
                "active": True,
                "attrs": attrs,
            }
        )
        for fbx_device in fbx_devices:
            device_mac = fbx_device["l2ident"]["id"]
            devices[device_mac] = fbx_device

        # Device info
        device_info = DeviceInfo(
            configuration_url=f"https://{self.entry.data['host']}:{self.entry.data['port']}/",
            connections={(CONNECTION_NETWORK_MAC, unique_id)},
            identifiers={(DOMAIN, unique_id)},
            manufacturer="Freebox SAS",
            name="Freebox",
            sw_version=sw_version,
        )

        return {
            "sensors": sensors_temperature,
            "sensors_connection": sensors_connection,
            "attrs": attrs,
            "calls": calls,
            "call_list": call_list,
            "disks": disks,
            "wifi": wifi,
            "device_trackers": devices,
            "device_info": device_info,
        }

    async def async_execute(self, service: str, method: str, *args, **kwargs) -> None:
        """Execute method."""
        try:
            await self.api.open(self.entry.data[CONF_HOST], self.entry.data[CONF_PORT])
            api_service = getattr(self.api, service)
            await getattr(api_service, method)(*args, **kwargs)
        except HttpRequestError as error:
            _LOGGER.error(error)
        finally:
            await self.api.close()
