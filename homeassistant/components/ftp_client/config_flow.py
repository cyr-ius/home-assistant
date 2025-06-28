"""Config flow for the FTP Client integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SSL, CONF_USERNAME
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import CONF_BACKUP_PATH, DEFAULT_BACKUP_PATH, DEFAULT_SSL, DOMAIN
from .helpers import CannotConnect, FTPClient, InvalidAuth

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD,
            )
        ),
        vol.Required(CONF_BACKUP_PATH, default=DEFAULT_BACKUP_PATH): str,
        vol.Optional(CONF_SSL, default=DEFAULT_SSL): bool,
    }
)


class FTPDriveConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FTPClient."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                ftp = FTPClient(
                    host=user_input[CONF_HOST],
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    ssl=user_input[CONF_SSL],
                )
                client = await ftp.async_connect()
                result = await client.list()
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"
            else:
                if result:
                    self._async_abort_entries_match(
                        {
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_USERNAME: user_input[CONF_USERNAME],
                        }
                    )
                    await client.quit()

                    return self.async_create_entry(
                        title=f"{user_input[CONF_USERNAME]}@{user_input[CONF_HOST]}",
                        data=user_input,
                    )

                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
