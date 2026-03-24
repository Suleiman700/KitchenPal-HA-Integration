"""
Author: Suleiman
Email:  soleman630@gmail.com
GitHub: https://github.com/Suleiman700/KitchenPal-HA-Integration
"""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KitchenPalClient, KitchenPalApiError
from .const import DOMAIN, SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class KitchenPalCoordinator(DataUpdateCoordinator):
    """
    Polls KitchenPal every 15 minutes.
    Maintains a local cache and applies created/updated/deleted deltas.
    Data is a dict keyed by str(kitchen_record_id).
    """

    def __init__(self, hass: HomeAssistant, client: KitchenPalClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self.client = client
        # ms timestamp of last successful fetch — 0 means "get everything"
        self._last_updated_ms: int = 0
        # Local cache: record_id (str) -> item dict
        self._cache: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch delta from API, apply to cache, return full cache."""
        try:
            payload = await self.client.get_records(last_updated=self._last_updated_ms)
        except KitchenPalApiError as err:
            raise UpdateFailed(f"KitchenPal API error: {err}") from err

        # Apply created items
        for item in payload.get("created", []):
            rid = str(item["kitchen_record_id"])
            self._cache[rid] = item
            _LOGGER.debug("KitchenPal: added item %s (%s)", rid, item.get("kitchen_record_name"))

        # Apply updated items
        for item in payload.get("updated", []):
            rid = str(item["kitchen_record_id"])
            self._cache[rid] = item
            _LOGGER.debug("KitchenPal: updated item %s (%s)", rid, item.get("kitchen_record_name"))

        # Apply deleted items
        for item in payload.get("deleted", []):
            rid = str(item["kitchen_record_id"])
            if rid in self._cache:
                del self._cache[rid]
                _LOGGER.debug("KitchenPal: removed item %s", rid)

        # Next poll: only fetch changes since now
        self._last_updated_ms = int(time.time() * 1000)

        _LOGGER.debug("KitchenPal: cache now has %d items", len(self._cache))
        return dict(self._cache)
