"""Config flow and options flow for Sungrow iSolarCloud."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import (
    GATEWAY_AUTO,
    GATEWAYS,
    ISolarCloudAuthError,
    ISolarCloudClient,
    ISolarCloudConnectionError,
    ISolarCloudError,
)
from .const import (
    CONF_GATEWAY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

GATEWAY_OPTIONS = [GATEWAY_AUTO, *GATEWAYS.keys()]


class ISolarCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sungrow iSolarCloud."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            gateway = user_input[CONF_GATEWAY]

            session = async_get_clientsession(self.hass)
            client = ISolarCloudClient(
                session=session,
                username=username,
                password=password,
                gateway=gateway,
            )
            try:
                auth = await client.async_login()
                await client.async_get_ps_list()
            except ISolarCloudAuthError:
                errors["base"] = "invalid_auth"
            except ISolarCloudConnectionError:
                errors["base"] = "cannot_connect"
            except ISolarCloudError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(f"{auth.user_id}:{username.lower()}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"iSolarCloud ({username})",
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_GATEWAY: gateway,
                    },
                    options={
                        CONF_SCAN_INTERVAL: int(
                            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        ),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_GATEWAY, default=GATEWAY_AUTO): SelectSelector(
                    SelectSelectorConfig(
                        options=GATEWAY_OPTIONS,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="gateway",
                    )
                ),
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=10,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return ISolarCloudOptionsFlow()


class ISolarCloudOptionsFlow(OptionsFlow):
    """Handle options flow for Sungrow iSolarCloud."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the integration options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                },
            )

        current_interval = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current_interval): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=10,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
