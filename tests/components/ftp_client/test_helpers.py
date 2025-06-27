"""Test the FTP Client setup."""

from unittest.mock import patch

from homeassistant.components.ftp_client.helpers import StatusCodeError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration

from tests.common import MockConfigEntry


async def test_load_config_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test loading and unloading the integration."""

    with patch(
        "homeassistant.components.ftp_client.helpers.Client.connect",
        side_effect=StatusCodeError(530, 530, "Permission denied"),
    ) as mock_connect:
        await setup_integration(hass, mock_config_entry)
        assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
        assert mock_connect.call_count == 1
