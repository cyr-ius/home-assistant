"""Support for LG WebOS TV notification service."""
import asyncio
import logging

from aiopylgtv import PyLGTVCmdException, PyLGTVPairException
from websockets.exceptions import ConnectionClosed

from homeassistant.components.notify import ATTR_DATA, BaseNotificationService
from homeassistant.const import CONF_ICON, CONF_NAME

from .const import ATTR_CONFIG_ENTRY_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_get_service(hass, config, discovery_info=None):
    """Return the notify service."""
    if discovery_info is None:
        return None
    icon_path = discovery_info.get(CONF_ICON, "")
    name = discovery_info.get(CONF_NAME)
    client = hass.data[DOMAIN][discovery_info[ATTR_CONFIG_ENTRY_ID]]

    return LgWebOSNotificationService(client, name, icon_path)


class LgWebOSNotificationService(BaseNotificationService):
    """Implement the notification service for LG WebOS TV."""

    def __init__(self, client, name, icon_path):
        """Initialize the service."""
        self._name = name
        self._client = client
        self._icon_path = icon_path

    async def async_send_message(self, message="", **kwargs):
        """Send a message to the tv."""
        try:
            if not self._client.is_connected():
                await self._client.connect()

            data = kwargs.get(ATTR_DATA)
            icon_path = (
                data.get(CONF_ICON, self._icon_path) if data else self._icon_path
            )
            await self._client.send_message(message, icon_path=icon_path)
        except PyLGTVPairException:
            _LOGGER.error("Pairing with TV failed")
        except FileNotFoundError:
            _LOGGER.error("Icon %s not found", icon_path)
        except (
            OSError,
            ConnectionClosed,
            asyncio.TimeoutError,
            asyncio.CancelledError,
            PyLGTVCmdException,
        ):
            _LOGGER.error("TV unreachable")
