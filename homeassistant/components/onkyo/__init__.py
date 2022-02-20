"""The onkyo component."""
import asyncio
import logging

from eiscp import eISCP as onkyo_rcv
from eiscp.commands import COMMANDS

from homeassistant import config_entries, exceptions
from homeassistant.components.media_player.const import DOMAIN as media_domain
from homeassistant.const import CONF_HOST
from homeassistant.helpers import config_per_platform, device_registry as dr

from .const import COMPONENTS, CONF_SOURCES, DOMAIN

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


async def async_setup_entry(hass, config_entry):
    """Set the config entry up."""
    if not config_entry.options:
        sources = config_entry.data.get(CONF_SOURCES, {})
        if isinstance(sources, list):
            sources = list2dict(sources)
        hass.config_entries.async_update_entry(
            config_entry,
            options={CONF_SOURCES: sources},
        )

    try:
        receiver = onkyo_rcv(config_entry.data[CONF_HOST])
    except CannotConnect as error:
        raise exceptions.ConfigEntryNotReady from error

    hass.data[DOMAIN][config_entry.unique_id] = receiver

    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, receiver.identifier)},
        manufacturer="Onkyo",
        model=receiver.model_name,
    )

    for component in COMPONENTS:
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
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, component)
                for component in COMPONENTS
            ]
        )
    )
    if unload_ok:
        receiver = hass.data[DOMAIN][config_entry.unique_id]
        await hass.async_add_executor_job(receiver.disconnect)
    return unload_ok


def default_sources() -> dict:
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


def list2dict(sources: list) -> dict:
    """Reduce selected sources in default sources."""
    return {key: value for key, value in default_sources().items() if key in sources}


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
