"""Test the Qnap config flow."""
from unittest.mock import patch

import pytest
from requests.exceptions import ConnectTimeout

from homeassistant import config_entries, setup
from homeassistant.components.qnap.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_MONITORED_CONDITIONS,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.data_entry_flow import RESULT_TYPE_CREATE_ENTRY, RESULT_TYPE_FORM

from tests.common import MockConfigEntry

API_RETURN = {
    "system": {
        "model": "TS-419P II",
        "name": "QNAP_NAS",
        "serial_number": "123456",
        "temp_c": 36,
        "temp_f": 97,
        "timezone": "(GMT+01:00) Brussels...rid, Paris",
    },
    "firmware": {
        "build": "20191107",
        "build_time": "07/11/2019",
        "patch": "0",
        "version": "4.3.3",
    },
    "uptime": {"days": 99, "hours": 1, "minutes": 30, "seconds": 30},
    "cpu": {"model": None, "temp_c": None, "temp_f": None, "usage_percent": 23.6},
    "memory": {"free": 271.6, "total": 503.4},
    "nics": {
        "eth0": {
            "err_packets": 0,
            "ip": "192.168.1.1",
            "link_status": "Up",
            "mac": "00:01:02:03:04:EF",
            "mask": "255.255.255.0",
            "max_speed": 1000,
            "rx_packets": 100,
            "tx_packets": 100,
            "usage": "STATIC",
        },
        "eth1": {
            "err_packets": 0,
            "ip": "0.0.0.0",
            "link_status": "Down",
            "mac": "00:01:02:03:04:FF",
            "mask": "0.0.0.0",
            "max_speed": 1000,
            "rx_packets": 0,
            "tx_packets": 0,
            "usage": "DHCP",
        },
    },
    "dns": ["1.1.1.1", "8.8.8.8"],
}

YAML_CONFIG = {
    "platform": "qnap",
    CONF_HOST: "1.2.3.4",
    CONF_USERNAME: "myuser",
    CONF_PASSWORD: "password",
    CONF_MONITORED_CONDITIONS: [
        "status",
        "cpu_usage",
        "memory_percent_used",
        "network_tx",
        "volume_percentage_used",
    ],
}

MANUAL_CONFIG = {
    CONF_HOST: "1.2.3.4",
    CONF_USERNAME: "myuser",
    CONF_PASSWORD: "password",
}


async def test_form_import(hass):
    """Test we can import yaml config."""

    with patch(
        "homeassistant.components.qnap.config_flow.QNAPStats.get_system_stats",
        return_value=API_RETURN,
    ), patch(
        "homeassistant.components.qnap.async_setup", return_value=True
    ) as mock_setup, patch(
        "homeassistant.components.qnap.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=YAML_CONFIG,
        )
        await hass.async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "Qnap_nas"
    assert result["data"] == {
        "platform": "qnap",
        CONF_HOST: "1.2.3.4",
        CONF_USERNAME: "myuser",
        CONF_PASSWORD: "password",
        CONF_MONITORED_CONDITIONS: [
            "status",
            "cpu_usage",
            "memory_percent_used",
            "network_tx",
            "volume_percentage_used",
        ],
    }

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form(hass):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.qnap.config_flow.QNAPStats.get_system_stats",
        return_value=API_RETURN,
    ), patch(
        "homeassistant.components.qnap.async_setup", return_value=True
    ) as mock_setup, patch(
        "homeassistant.components.qnap.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"], user_input=MANUAL_CONFIG
        )
        await hass.async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "Qnap_nas"
    assert result["data"] == {
        CONF_HOST: "1.2.3.4",
        CONF_USERNAME: "myuser",
        CONF_PASSWORD: "password",
        CONF_PORT: 8080,
        CONF_SSL: False,
        CONF_VERIFY_SSL: True,
    }
    assert result["result"].unique_id == "123456"

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    "error",
    [
        (ConnectTimeout, "cannot_connect"),
        (TypeError, "invalid_auth"),
        (Exception, "unknown"),
    ],
)
async def test_form_errors(hass, error):
    """Test we handle errors."""
    exc, base_error = error
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.qnap.config_flow.QNAPStats.get_system_stats",
        side_effect=exc,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MANUAL_CONFIG,
        )
    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": base_error}


async def test_form_already_configured(hass):
    """Test a duplicate id aborts and updates existing entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="123456",
        data={CONF_HOST: "1.2.3.4", CONF_USERNAME: "myuser", CONF_PASSWORD: "password"},
    )

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.qnap.config_flow.QNAPStats.get_system_stats",
        return_value=API_RETURN,
    ), patch("homeassistant.components.qnap.async_setup", return_value=True), patch(
        "homeassistant.components.qnap.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=YAML_CONFIG,
        )
        await hass.async_block_till_done()

    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"
