"""
Author: Suleiman
Email:  soleman630@gmail.com
GitHub: https://github.com/Suleiman700/KitchenPal-HA-Integration
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import KitchenPalCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: KitchenPalCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        KitchenPalExpiryBinarySensor(coordinator, record_id)
        for record_id in coordinator.data
    ]
    async_add_entities(entities)

    def _handle_coordinator_update() -> None:
        current_ids = {e.unique_id for e in entities}
        new_entities = [
            KitchenPalExpiryBinarySensor(coordinator, record_id)
            for record_id in coordinator.data
            if f"kitchenpal_integration_expired_{record_id}" not in current_ids
        ]
        if new_entities:
            async_add_entities(new_entities)
            entities.extend(new_entities)

    coordinator.async_add_listener(_handle_coordinator_update)


class KitchenPalExpiryBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor: ON = expired, OFF = fresh."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: KitchenPalCoordinator, record_id: str) -> None:
        super().__init__(coordinator)
        self._record_id = record_id
        # unique_id has prefix → entity_id becomes binary_sensor.kitchenpal_integration_expired_<id>
        self._attr_unique_id = f"kitchenpal_integration_expired_{record_id}"

    @property
    def _item(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._record_id, {})

    @property
    def name(self) -> str:
        # Friendly name is clean — just "Curd with Milk Expired"
        item_name = self._item.get("kitchen_record_name", f"Item {self._record_id}")
        return f"{item_name} Expired"

    @property
    def is_on(self) -> bool:
        expiry_ms = self._item.get("expiryDate")
        if expiry_ms is None:
            return False
        expiry_dt = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc)
        return datetime.now(tz=timezone.utc) > expiry_dt

    @property
    def icon(self) -> str:
        if self.is_on:
            return "mdi:clock-alert"
        days_ms = self._item.get("expiryDate")
        if days_ms:
            days = (datetime.fromtimestamp(days_ms / 1000, tz=timezone.utc) - datetime.now(tz=timezone.utc)).days
            if days <= 3:
                return "mdi:clock-end"
            if days <= 7:
                return "mdi:clock-outline"
        return "mdi:clock-check"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = self._item
        expiry_ms = item.get("expiryDate")
        days_left = None
        if expiry_ms:
            expiry_dt = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc)
            days_left = (expiry_dt - datetime.now(tz=timezone.utc)).days

        return {
            "kitchen_record_id": item.get("kitchen_record_id"),
            "item_name": item.get("kitchen_record_name"),
            "days_until_expiry": days_left,
            "storage": (item.get("defaultStorage") or {}).get("name"),
            "barcode": item.get("barcode"),
            "category": item.get("prioritization_cooking_name"),
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "kitchenpal_kitchen")},
            "name": "KitchenPal Kitchen",
            "manufacturer": MANUFACTURER,
            "model": "Cloud Kitchen",
        }
