"""Test the FTP Client config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.components.ftp_client.const import CONF_BACKUP_PATH, DOMAIN
from homeassistant.components.ftp_client.helpers import CannotConnect, InvalidAuth
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SSL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("mock_setup_entry")
async def test_form(hass: HomeAssistant, ftp_client: AsyncMock) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.ftp_client.helpers.FTPClient.async_connect",
        return_value=ftp_client.client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_BACKUP_PATH: "backup-folder",
                CONF_SSL: True,
            },
        )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-username@1.1.1.1"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
        CONF_BACKUP_PATH: "backup-folder",
        CONF_SSL: True,
    }
    assert len(ftp_client.mock_calls) == 2


@pytest.mark.usefixtures("mock_setup_entry")
async def test_form_fail(hass: HomeAssistant, ftp_client: AsyncMock) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ftp_client.helpers.FTPClient.async_connect",
        side_effect=InvalidAuth,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_BACKUP_PATH: "backup-folder",
                CONF_SSL: True,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    # Make sure the config flow tests finish with either an
    # FlowResultType.CREATE_ENTRY or FlowResultType.ABORT so
    # we can show the config flow is able to recover from an error.
    with patch(
        "homeassistant.components.ftp_client.helpers.FTPClient.async_connect",
        return_value=ftp_client.client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_BACKUP_PATH: "backup-folder",
                CONF_SSL: True,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-username@1.1.1.1"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
        CONF_BACKUP_PATH: "backup-folder",
        CONF_SSL: True,
    }
    assert len(ftp_client.mock_calls) == 2


@pytest.mark.usefixtures("mock_setup_entry")
async def test_form_cannot_connect(hass: HomeAssistant, ftp_client: AsyncMock) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ftp_client.helpers.FTPClient.async_connect",
        side_effect=CannotConnect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_BACKUP_PATH: "backup-folder",
                CONF_SSL: True,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Make sure the config flow tests finish with either an
    # FlowResultType.CREATE_ENTRY or FlowResultType.ABORT so
    # we can show the config flow is able to recover from an error.

    with patch(
        "homeassistant.components.ftp_client.helpers.FTPClient.async_connect",
        return_value=ftp_client.client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_BACKUP_PATH: "backup-folder",
                CONF_SSL: True,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-username@1.1.1.1"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
        CONF_BACKUP_PATH: "backup-folder",
        CONF_SSL: True,
    }
    assert len(ftp_client.mock_calls) == 2


@pytest.mark.usefixtures("mock_setup_entry")
async def test_form_unknown(hass: HomeAssistant, ftp_client: AsyncMock) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ftp_client.helpers.FTPClient.async_connect",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_BACKUP_PATH: "backup-folder",
                CONF_SSL: True,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}

    # Make sure the config flow tests finish with either an
    # FlowResultType.CREATE_ENTRY or FlowResultType.ABORT so
    # we can show the config flow is able to recover from an error.

    with patch(
        "homeassistant.components.ftp_client.helpers.FTPClient.async_connect",
        return_value=ftp_client.client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_BACKUP_PATH: "backup-folder",
                CONF_SSL: True,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-username@1.1.1.1"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
        CONF_BACKUP_PATH: "backup-folder",
        CONF_SSL: True,
    }
    assert len(ftp_client.mock_calls) == 2


@pytest.mark.usefixtures("mock_setup_entry")
async def test_duplicate_entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, ftp_client: AsyncMock
) -> None:
    """Test we get the form and create a entry on success."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    with patch(
        "homeassistant.components.ftp_client.helpers.FTPClient.async_connect",
        return_value=ftp_client.client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_BACKUP_PATH: "backup-folder",
                CONF_SSL: True,
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
