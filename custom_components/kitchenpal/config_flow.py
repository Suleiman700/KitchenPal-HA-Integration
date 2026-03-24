"""
Author: Suleiman
Email:  soleman630@gmail.com
GitHub: https://github.com/Suleiman700/KitchenPal-HA-Integration
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .api import KitchenPalClient, KitchenPalAuthError, KitchenPalApiError
from .const import DOMAIN, CONF_BEARER_TOKEN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BEARER_TOKEN): str,
    }
)


class KitchenPalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the setup UI flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the form and validate the bearer token."""
        errors: dict[str, str] = {}

        if user_input is not None:
            token = user_input[CONF_BEARER_TOKEN].strip()
            client = KitchenPalClient(token)
            try:
                valid = await client.validate_token()
                if not valid:
                    errors[CONF_BEARER_TOKEN] = "invalid_auth"
            except KitchenPalAuthError:
                errors[CONF_BEARER_TOKEN] = "invalid_auth"
            except KitchenPalApiError:
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

            if not errors:
                # Prevent duplicate entries
                await self.async_set_unique_id(token[:32])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="KitchenPal",
                    data={CONF_BEARER_TOKEN: token},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/yourusername/ha-kitchenpal"
            },
        )
