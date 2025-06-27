"""Common fixtures for the FTP Client tests."""

from collections.abc import Generator
from json import dumps
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.ftp_client.const import CONF_BACKUP_PATH, DOMAIN
from homeassistant.components.ftp_client.helpers import FTPClient
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SSL, CONF_USERNAME

from .const import BACKUP_METADATA, MOCK_LIST_FILES

from tests.common import MockConfigEntry


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ftp_client.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="test-username@1.1.1.1",
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_BACKUP_PATH: "backup-folder",
            CONF_SSL: True,
        },
        entry_id="01JKXV07ASC62D620DGYNG2R8H",
    )


def mock_stream(path: str) -> MagicMock:
    """Return a mock stream for the FTPClient.client."""
    chunks = (
        [dumps(BACKUP_METADATA).encode("utf-8"), b""]
        if path.endswith(".json")
        else [b"backup data", b""]
    )

    stream = MagicMock()

    async def aenter(*args, **kwargs):
        return stream

    async def aexit(*args, **kwargs):
        return None

    async def iter_blocks(block_size):
        for chunk in chunks.copy():
            yield chunk

    stream.__aenter__ = aenter
    stream.__aexit__ = aexit
    stream.iter_by_block = iter_blocks
    stream.read = AsyncMock(side_effect=chunks)
    stream.finish = AsyncMock(return_value=None)

    return stream


@pytest.fixture(name="mock_ftp_client_client")
def mock_ftp_client_client() -> FTPClient:
    """Return a mock FTPClient.client."""
    client = MagicMock(spec=FTPClient)
    client.download_stream = AsyncMock(side_effect=mock_stream)
    client.upload_stream = AsyncMock(return_value=True)
    client.remove = AsyncMock(return_value=None)
    client.quit = AsyncMock(return_value=None)
    client.close = AsyncMock(return_value=None)
    client.list = AsyncMock(return_value=MOCK_LIST_FILES)

    return client


@pytest.fixture(name="ftp_client")
def mock_ftp_client(mock_ftp_client_client) -> Generator[AsyncMock]:
    """Mock the sftp client."""
    with patch(
        "homeassistant.components.ftp_client.FTPClient", autospec=True
    ) as mock_ftp_client:
        mock = mock_ftp_client.return_value
        mock.async_close.return_value = None
        mock.async_ensure_path_exists.return_value = True
        mock.client = mock_ftp_client_client
        mock.async_connect.return_value = mock.client

        yield mock
