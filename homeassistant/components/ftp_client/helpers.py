"""Helper functions for the FTPClient component."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

# from contextlib import asynccontextmanager
from ssl import SSLError

from aioftp import AIOFTPException, Client, StatusCodeError

from homeassistant.exceptions import HomeAssistantError

# _LOGGER = logging.getLogger(__name__)


class FTPClient:
    """Client."""

    def __init__(
        self, *, host: str, username: str, password: str, ssl: bool = False
    ) -> None:
        """Initialize."""
        self.host = host
        self._username = username
        self._password = password
        self._ssl = ssl
        self.client = Client(ssl=self._ssl)
        self._lock = asyncio.Lock()

    async def async_connect(self) -> Client:
        """Create a FTP client."""
        try:
            await self.client.connect(self.host)
            await self.client.login(self._username, self._password)
        except (ConnectionError, TimeoutError, OSError, SSLError) as err:
            raise CannotConnect from err
        except StatusCodeError as err:
            if err.received_codes and "530" in map(str, err.received_codes):
                raise InvalidAuth from err
            raise CannotConnect from err
        except AIOFTPException as err:
            raise CannotConnect from err
        return self.client

    async def async_close(self) -> None:
        """Close ftp session."""
        try:
            await self.client.quit()
            self.client.close()
        except (ConnectionError, TimeoutError):
            pass

    async def async_ensure_path_exists(self, path: str) -> bool:
        """Ensure that a path exists recursively on the FTP server."""
        try:
            await self.client.is_dir(path)
        except StatusCodeError:
            if not await self.client.make_directory(path):
                return False
        return True

    # async def _connect(self) -> None:
    #     await self.client.connect(self.host)
    #     await self.client.login(self._username, self._password)
    #     _LOGGER.info("FTP connected")

    # async def _ensure_connection(self) -> None:
    #     if self.client is None or self.client.stream is None:
    #         _LOGGER.warning("FTP not connected, reconnecting")
    #         try:
    #             await self._connect()
    #         except Exception as e:
    #             _LOGGER.error("Reconnection failed: %s", e)
    #             raise

    # @asynccontextmanager
    # async def connect(self) -> AsyncIterator[FTPClient]:
    #     """Context manager to ensure FTP connection."""
    #     await self._connect()
    #     try:
    #         yield self
    #     finally:
    #         if self.client is not None:
    #             await self.client.quit()
    #             self.client = None
    #             _LOGGER.info("FTP disconnected")

    # async def safe_call(self, func, *args, **kwargs) -> None:
    #     """Execute a client method with reconnection on failure."""
    #     await self._ensure_connection()

    #     async with self._lock:
    #         try:
    #             return await func(*args, **kwargs)
    #         except (ConnectionResetError, StatusCodeError, RuntimeError):
    #             # _LOGGER.warning("Connection lost during operation: %s", e)
    #             await self._connect()
    #             return await func(*args, **kwargs)
    #         except AIOFTPException as e:
    #             _LOGGER.error("AIOFTPException during operation: %s", e)
    #             raise CannotConnect from e


def json_to_stream(json_str: str, chunk_size: int = 8192) -> AsyncIterator[bytes]:
    """Convert a JSON string into an async iterator of bytes."""

    async def generator() -> AsyncIterator[bytes]:
        encoded = json_str.encode("utf-8")
        for i in range(0, len(encoded), chunk_size):
            yield encoded[i : i + chunk_size]

    return generator()


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class BackupFolderError(HomeAssistantError):
    """Error indicating that the directory being backed up is incorrect."""
