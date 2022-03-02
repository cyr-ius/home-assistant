"""The onkyo component."""
import logging

from eiscp import eISCP as onkyo_rcv
from eiscp.commands import COMMANDS

from homeassistant import config_entries
from homeassistant.components.media_player.const import DOMAIN as media_domain
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_per_platform

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up the onkyo environment."""
    hass.data.setdefault(DOMAIN, {})

    # Import configuration from media_player platform
    config_platform = config_per_platform(config, media_domain)
    for p_type, p_config in config_platform:
        if p_type != DOMAIN:
            continue

        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=p_config,
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set the config entry up."""
    try:
        receiver = onkyo_rcv(config_entry.data[CONF_HOST])
    except CannotConnect as error:
        raise ConfigEntryNotReady from error

    hass.data[DOMAIN][config_entry.unique_id] = receiver

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    if not config_entry.update_listeners:
        config_entry.add_update_listener(async_update_options)

    return True


async def async_update_options(hass, config_entry):
    """Update options."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        receiver = hass.data[DOMAIN][config_entry.unique_id]
        await hass.async_add_executor_job(receiver.disconnect)
    return unload_ok


def _build_sources_list() -> dict:
    """Retrieve default sources."""
    sources_list = {}
    for value in COMMANDS["main"]["SLI"]["values"].values():
        name = value["name"]
        desc = value["description"].replace("sets ", "")
        if isinstance(name, tuple):
            name = name[0]
        if name in ["07", "08", "09", "up", "down", "query"]:
            continue
        sources_list.update({name: desc})
    return sources_list


def _build_sounds_mode_list() -> dict:
    """Retrieve sound mode list."""
    sounds_list = []
    for value in COMMANDS["main"]["LMD"]["values"].values():
        name = value["name"]
        if isinstance(name, tuple):
            name = name[-1]
        if name in ["up", "down", "query"]:
            continue
        sounds_list.append(name)
    sounds_list = list(set(sounds_list))
    sounds_list.sort()
    sounds_mode = {name: name.replace("-", " ").title() for name in sounds_list}
    return sounds_mode


def build_selected_dict(sources: list = None, sounds: list = None) -> dict[str, str]:
    """Return selected dictionary."""
    if sources:
        return {k: v for k, v in _build_sources_list().items() if (k in sources)}
    if sounds:
        return {k: v for k, v in _build_sounds_mode_list().items() if (k in sounds)}
    return {}


def reverse_mapping(ssdict) -> dict[str, str]:
    """Reverse dictionary."""
    return {v: k for k, v in ssdict.items()}


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
