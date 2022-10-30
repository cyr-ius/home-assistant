"""Config flow to configure the Freebox integration."""
from contextlib import suppress
import logging

from freebox_api.exceptions import AuthorizationError, HttpRequestError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .coordinator import get_api

_LOGGER = logging.getLogger(__name__)


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): int,
    }
)


class FreeboxFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize Freebox config flow."""
        self._host = None
        self._port = None

    def _show_setup_form(self, user_input=None, errors=None):
        """Show the setup form to the user."""
        if user_input is None:
            user_input = {}

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}
        if user_input is None:
            return self._show_setup_form(user_input, errors)

        self._host = user_input[CONF_HOST]
        self._port = user_input[CONF_PORT]

        await self.async_set_unique_id(self._host)
        self._abort_if_unique_id_configured()

        return await self.async_step_link()

    async def async_step_link(self, user_input=None):
        """Attempt to link with the Freebox router.

        Given a configured host, will ask the user to press the button
        to connect to the router.
        """
        errors = {}
        if user_input is None:
            return self.async_show_form(step_id="link", errors=errors)

        fbx = await self.hass.async_add_executor_job(get_api, self.hass, self._host)
        try:
            await fbx.open(self._host, self._port)
            await fbx.system.get_config()
        except AuthorizationError as error:
            _LOGGER.error(error)
            errors["base"] = "register_failed"

        except HttpRequestError:
            _LOGGER.error("Error connecting to the Freebox router at %s", self._host)
            errors["base"] = "cannot_connect"

        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Unknown error connecting with Freebox router at %s", self._host
            )
            errors["base"] = "unknown"

        else:
            return self.async_create_entry(
                title=self._host,
                data={CONF_HOST: self._host, CONF_PORT: self._port},
            )
        finally:
            with suppress(Exception):
                # Close connection
                await fbx.close()

        return self.async_show_form(step_id="link", errors=errors)

    async def async_step_import(self, user_input=None):
        """Import a config entry."""
        return await self.async_step_user(user_input)

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Initialize flow from zeroconf."""
        zeroconf_properties = discovery_info.properties
        host = zeroconf_properties["api_domain"]
        port = zeroconf_properties["https_port"]
        return await self.async_step_user({CONF_HOST: host, CONF_PORT: port})
