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

    if stack()[1].filename[-26:] != "homeassistant/bootstrap.py":
        raise VaultException("Access is denied")

    if passphrase is None:
        _LOGGER.warning(
            "No passphrase detected, please add environment variable named: PASSPHRASE"
        )
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
        # Only the config_entries module can call this method
        if stack()[1].filename[-31:] != "homeassistant/config_entries.py":
            raise VaultException("Access is denied")

        decrypt_fields: dict[str, str] = {}
        if hasattr(component, "config_flow") and hasattr(
            component.config_flow, "config_entries"
        ):

            try:
                current_entry = component.config_flow.config_entries.current_entry.get()
                data = current_entry.data
                options = current_entry.options
                if current_entry.encrypt_fields is None:
                    return decrypt_fields
            except Exception as error:
                raise VaultException from error

            try:
                for field in current_entry.encrypt_fields:
                    if value := data.get(field):
                        decrypt_fields.update(
                            {field: fernet.decrypt(value.encode()).decode()}
                        )
                    if value := options.get(field):
                        decrypt_fields.update(
                            {field: fernet.decrypt(value.encode()).decode()}
                        )

            except Exception as error:
                raise EncryptException from error

        return decrypt_fields

    hass.async_encrypt_fields = async_encrypt_fields  # type: ignore[attr-defined]
    hass.async_reveal_fields = async_reveal_fields  # type: ignore[attr-defined]


class VaultException(HomeAssistantError):
    """Vault exception."""


class EncryptException(VaultException):
    """Fernet exception."""
