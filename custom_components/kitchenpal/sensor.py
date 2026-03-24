"""
Author: Suleiman
Email:  soleman630@gmail.com
GitHub: https://github.com/Suleiman700/KitchenPal-HA-Integration
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorEntity
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
        KitchenPalItemSensor(coordinator, record_id)
        for record_id in coordinator.data
    ]
    async_add_entities(entities)

    def _handle_coordinator_update() -> None:
        current_ids = {e.unique_id for e in entities}
        new_entities = [
            KitchenPalItemSensor(coordinator, record_id)
            for record_id in coordinator.data
            if f"kitchenpal_integration_{record_id}" not in current_ids
        ]
        if new_entities:
            async_add_entities(new_entities)
            entities.extend(new_entities)

    coordinator.async_add_listener(_handle_coordinator_update)


def _ms_to_datetime(ms: int | None) -> datetime | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def _days_until(ms: int | None) -> int | None:
    if ms is None:
        return None
    expiry = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return (expiry - datetime.now(tz=timezone.utc)).days


def _item_icon(category: str | None, days: int | None) -> str:
    if days is not None and days < 0:
        return "mdi:food-off"
    if days is not None and days <= 3:
        return "mdi:alert-circle-outline"
    category_icons = {
        "Dairy": "mdi:cow",
        "Meat": "mdi:food-steak",
        "Fish": "mdi:fish",
        "Vegetables": "mdi:carrot",
        "Fruits": "mdi:fruit-cherries",
        "Bakery": "mdi:bread-slice",
        "Beverages": "mdi:cup",
        "Frozen": "mdi:snowflake",
        "Snacks": "mdi:popcorn",
        "Condiments": "mdi:bottle-soda",
    }
    for key, icon in category_icons.items():
        if category and key.lower() in category.lower():
            return icon
    return "mdi:food"


class KitchenPalItemSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing a single KitchenPal item — state is expiry date."""

    def __init__(self, coordinator: KitchenPalCoordinator, record_id: str) -> None:
        super().__init__(coordinator)
        self._record_id = record_id
        # unique_id has prefix → entity_id becomes sensor.kitchenpal_integration_<id>
        self._attr_unique_id = f"kitchenpal_integration_{record_id}"

    @property
    def _item(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._record_id, {})

    @property
    def name(self) -> str:
        # Friendly name is clean — no prefix
        return self._item.get("kitchen_record_name", f"Item {self._record_id}")

    @property
    def native_value(self) -> str | None:
        ms = self._item.get("expiryDate")
        if ms is None:
            return "No expiry"
        days = _days_until(ms)
        if days is not None and days < 0:
            return "Expired"
        dt = _ms_to_datetime(ms)
        return dt.strftime("%Y-%m-%d") if dt else None

    @property
    def icon(self) -> str:
        return _item_icon(
            self._item.get("prioritization_cooking_name"),
            _days_until(self._item.get("expiryDate")),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = self._item
        expiry_ms = item.get("expiryDate")
        expiry_dt = _ms_to_datetime(expiry_ms)
        days_left = _days_until(expiry_ms)
        storage = item.get("defaultStorage") or {}

        return {
            "kitchen_record_id": item.get("kitchen_record_id"),
            "barcode": item.get("barcode"),
            "type": item.get("kitchen_record_type"),
            "storage": storage.get("name"),
            "storage_id": storage.get("id"),
            "quantity": item.get("quantity"),
            "unit": item.get("unit"),
            "pieces": item.get("pieces"),
            "filling": item.get("filling"),
            "expiry_date": expiry_dt.isoformat() if expiry_dt else None,
            "expiry_date_ms": expiry_ms,
            "days_until_expiry": days_left,
            "category": item.get("prioritization_cooking_name"),
            "image_url": item.get("kitchen_record_image"),
            "updated_at": _ms_to_datetime(item.get("updatedAt")),
            "created_at": _ms_to_datetime(item.get("createdAt")),
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "kitchenpal_kitchen")},
            "name": "KitchenPal Kitchen",
            "manufacturer": MANUFACTURER,
            "model": "Cloud Kitchen",
        }
