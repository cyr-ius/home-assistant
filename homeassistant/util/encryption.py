"""Function to encrypt and decrypt data."""
from __future__ import annotations

import base64
from inspect import stack
import logging
from types import ModuleType

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .. import core
from ..exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


@core.callback
def async_enable_encryption(
    hass: core.HomeAssistant, passphrase: str | None = None
) -> None:
    """Add methods on-the-fly for Hass object.

    This method avoids having the passphrase stored in an object, method or attribute
    """
    # Only bootstrap module can call this method
    if stack()[1].filename[-26:] != "homeassistant/bootstrap.py":
        raise VaultException("Access is denied")

    if passphrase is None:
        _LOGGER.warning("No passphrase, please add environment variable: PASSPHRASE")
        return
    _salt = b"Homeassistant"
    _kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=_salt, iterations=390000
    )
    _key = base64.urlsafe_b64encode(_kdf.derive(passphrase.encode()))
    fernet = Fernet(_key)

    async def async_encrypt_fields(
        data: dict[str, str], fields: list[str]
    ) -> dict[str, str]:
        """Encrypt fields from create_entry of ConfigFlow ."""
        for field in fields:
            if value := data.get(field):
                enc_value = fernet.encrypt(value.encode())
                data[field] = enc_value.decode()
        return data

    async def async_reveal_fields(component: ModuleType) -> dict[str, str]:
        """Decrypt fields in data component."""
        # Only config_entries module can call this method
        if stack()[1].filename[-31:] != "homeassistant/config_entries.py":
            raise VaultException("Access is denied")

        decrypt_fields: dict[str, str] = {}
        if hasattr(component, "config_flow") and hasattr(
            component.config_flow, "config_entries"
        ):
            config_entry = component.config_flow.config_entries.current_entry.get()
            if config_entry.encrypt_fields is None:
                return decrypt_fields
            try:
                for field in config_entry.encrypt_fields:
                    if value := config_entry.data.get(field):
                        decrypt_fields.update(
                            {field: fernet.decrypt(value.encode()).decode()}
                        )
            except Exception as error:
                raise VaultException from error

        return decrypt_fields

    hass.async_encrypt_fields = async_encrypt_fields  # type: ignore[attr-defined]
    hass.async_reveal_fields = async_reveal_fields  # type: ignore[attr-defined]
    hass.encryption_enabled = True


class VaultException(HomeAssistantError):
    """Vault exception."""
