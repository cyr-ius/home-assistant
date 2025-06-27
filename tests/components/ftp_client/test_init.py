"""Test the FTP Client setup."""

from homeassistant.components.ftp_client.helpers import InvalidAuth
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration

from tests.common import AsyncMock, MockConfigEntry


async def test_load_config_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    ftp_client: AsyncMock,
) -> None:
    """Test loading and unloading the integration."""
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_load_invalid_auth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    ftp_client: AsyncMock,
) -> None:
    """Test invalid authentication."""
    ftp_client.async_connect.side_effect = InvalidAuth("Invalid username or password")
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_load_create_folder_not_exists(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    ftp_client: AsyncMock,
) -> None:
    """Test folder backup not exists."""
    ftp_client.async_ensure_path_exists.return_value = False
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
