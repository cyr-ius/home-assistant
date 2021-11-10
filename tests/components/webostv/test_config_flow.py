"""Test the WebOS Tv config flow."""
from aiopylgtv import PyLGTVPairException
import pytest

from homeassistant import config_entries, setup
from homeassistant.components.webostv import CannotConnect
from homeassistant.components.webostv.const import (
    CONF_ON_ACTION,
    DOMAIN,
    TURN_ON_DATA,
    TURN_ON_SERVICE,
)
from homeassistant.const import CONF_HOST, CONF_ICON, CONF_NAME
from homeassistant.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from tests.async_mock import patch
from tests.common import MockConfigEntry

MOCK_YAML_CONFIG = {
    CONF_HOST: "1.2.3.4",
    CONF_NAME: "fake",
    CONF_ICON: "mdi:test",
}


@pytest.fixture(name="client")
def client_fixture():
    """Patch of client library for tests."""
    with patch(
        "homeassistant.components.webostv.WebOsClient", autospec=True
    ) as mock_client_class:
        client = mock_client_class.return_value
        client.software_info = {"device_id": "a1:b1:c1:d1:e1:f1"}
        client.client_key = "0123456789"
        client.apps = {0: {"title": "Applicaiton01"}}
        client.inputs = {0: {"label": "Input01"}}
        yield client


async def test_form_import(hass, client):
    """Test we can import yaml config."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=MOCK_YAML_CONFIG,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "pairing"

    with patch(
        "homeassistant.components.webostv.config_flow.async_control_connect",
        return_value=client,
    ), patch(
        "homeassistant.components.webostv.async_setup", return_value=True
    ) as mock_setup, patch(
        "homeassistant.components.webostv.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    await hass.async_block_till_done()
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["data"]["name"] == "fake"

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form(hass, client):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_YAML_CONFIG,
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "pairing"

    with patch(
        "homeassistant.components.webostv.config_flow.async_control_connect",
        return_value=client,
    ), patch(
        "homeassistant.components.webostv.async_setup", return_value=True
    ) as mock_setup, patch(
        "homeassistant.components.webostv.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    await hass.async_block_till_done()
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["data"]["name"] == "fake"

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_options_flow(hass, client):
    """Test options config flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.2.3.4",
        },
        unique_id="1.2.3.4",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.webostv.config_flow.async_control_connect",
        return_value=client,
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    with patch(
        "homeassistant.components.webostv.config_flow.async_control_connect",
        return_value=client,
    ):
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                TURN_ON_SERVICE: "service.test",
                TURN_ON_DATA: '{"title":"Hello","message":"World"}',
            },
        )

    await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result2["data"][CONF_ON_ACTION] == {
        "data": {"message": "World", "title": "Hello"},
        "service": "service.test",
    }


async def test_options_jsonformat_incorrect_flow(hass, client):
    """Test json format incorrect in options config flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.2.3.4",
        },
        unique_id="1.2.3.4",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.webostv.config_flow.async_control_connect",
        return_value=client,
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    with patch(
        "homeassistant.components.webostv.config_flow.async_control_connect",
        return_value=client,
    ):
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                TURN_ON_SERVICE: "service.test",
                TURN_ON_DATA: '{"title":Hello,}',
            },
        )
    await hass.async_block_till_done()
    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "encode_json"}


async def test_form_cannot_connect(hass):
    """Test we handle cannot connect error."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_YAML_CONFIG,
    )
    with patch(
        "homeassistant.components.webostv.config_flow.async_control_connect",
        side_effect=CannotConnect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_pairexception(hass):
    """Test pairing exception."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_YAML_CONFIG,
    )

    with patch(
        "homeassistant.components.webostv.config_flow.async_control_connect",
        side_effect=PyLGTVPairException("error"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    assert result2["type"] == RESULT_TYPE_ABORT
    assert result2["reason"] == "error_pairing"


async def test_form_updates_unique_id(hass, client):
    """Test duplicated unique_id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.2.3.4",
        },
        unique_id="1.2.3.4",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_YAML_CONFIG,
    )

    await hass.async_block_till_done()

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
