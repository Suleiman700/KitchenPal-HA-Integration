"""Button platform for KitchenPal — manual refresh.

Author: Suleiman
Email:  soleman630@gmail.com
GitHub: https://github.com/Suleiman700/KitchenPal-HA-Integration
"""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER
from .coordinator import KitchenPalCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: KitchenPalCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KitchenPalRefreshButton(coordinator)])


class KitchenPalRefreshButton(ButtonEntity):
    """Button that triggers an immediate data refresh from KitchenPal API."""

    _attr_unique_id = "kitchenpal_integration_refresh"
    _attr_name = "Manual Refresh"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: KitchenPalCoordinator) -> None:
        self._coordinator = coordinator

    async def async_press(self) -> None:
        """Fetch latest changes from KitchenPal immediately."""
        await self._coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "kitchenpal_kitchen")},
            "name": "KitchenPal Kitchen",
            "manufacturer": MANUFACTURER,
            "model": "Cloud Kitchen",
        }
