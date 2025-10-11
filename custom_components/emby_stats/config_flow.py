"""Config flow for Emby Library Stats."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_API_KEY
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_USER_ID, CONF_TV_LIBRARY_ID, CONF_MOVIE_LIBRARY_ID
from .emby_api import EmbyApiClient, EmbyApiError

_LOGGER = logging.getLogger(__name__)


class EmbyStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Emby Stats configuration flow."""
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            api_key = user_input[CONF_API_KEY]
            self.test_client = EmbyApiClient(host, api_key)

            try:
                await self.test_client.test_connection()
                self.users = await self.test_client.get_users()
                self.libraries = await self.test_client.get_libraries()
            except EmbyApiError as err:
                errors["base"] = "cannot_connect"
                _LOGGER.error("Emby API error: %s", err)
            except Exception:
                errors["base"] = "unknown"

            if not errors:
                self.config_data = user_input
                return await self.async_step_select_libraries()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_API_KEY): str,
            }),
            errors=errors,
        )

    async def async_step_select_libraries(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        user_options = {v: k for k, v in self.users.items()}
        lib_options = {v: k for k, v in self.libraries.items()}

        if user_input is not None:
            self.config_data[CONF_USER_ID] = user_input[CONF_USER_ID]
            self.config_data[CONF_TV_LIBRARY_ID] = user_input[CONF_TV_LIBRARY_ID]
            self.config_data[CONF_MOVIE_LIBRARY_ID] = user_input[CONF_MOVIE_LIBRARY_ID]

            return self.async_create_entry(
                title=self.config_data[CONF_HOST],
                data=self.config_data,
            )

        return self.async_show_form(
            step_id="select_libraries",
            data_schema=vol.Schema({
                vol.Required(CONF_USER_ID): vol.In(user_options),
                vol.Required(CONF_TV_LIBRARY_ID): vol.In(lib_options),
                vol.Required(CONF_MOVIE_LIBRARY_ID): vol.In(lib_options),
            }),
            errors=errors,
        )
