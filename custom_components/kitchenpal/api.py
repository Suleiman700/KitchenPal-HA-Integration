"""
Author: Suleiman
Email:  soleman630@gmail.com
GitHub: https://github.com/Suleiman700/KitchenPal-HA-Integration
"""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api-dot-kitchenpal-engine-prod.nw.r.appspot.com"


class KitchenPalApiError(Exception):
    """Raised when API returns an error."""


class KitchenPalAuthError(KitchenPalApiError):
    """Raised when authentication fails (401)."""


class KitchenPalClient:
    """Async KitchenPal API client."""

    def __init__(self, bearer_token: str) -> None:
        self._token = bearer_token
        self._session: aiohttp.ClientSession | None = None

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip",
            "country": "il",
            "language": "en",
            "new-application": "true",
            "Connection": "Keep-Alive",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_records(self, last_updated: int = 0) -> dict[str, Any]:
        """
        Fetch kitchen records since last_updated (ms timestamp).
        Returns payload with keys: created, updated, deleted, total_records.
        Pass last_updated=0 to get all records on first fetch.
        """
        url = f"{BASE_URL}/v3/kitchens/get-records-by-last-updated/"
        params = {"last_updated": last_updated}

        session = await self._get_session()
        try:
            async with session.get(url, headers=self._headers(), params=params) as resp:
                if resp.status == 401:
                    raise KitchenPalAuthError("Bearer token is invalid or expired")
                if resp.status != 200:
                    text = await resp.text()
                    raise KitchenPalApiError(f"API error {resp.status}: {text}")
                payload = await resp.json(content_type=None)
                _LOGGER.debug(
                    "KitchenPal API: created=%d updated=%d deleted=%d",
                    len(payload.get("created", [])),
                    len(payload.get("updated", [])),
                    len(payload.get("deleted", [])),
                )
                return payload
        except aiohttp.ClientError as err:
            raise KitchenPalApiError(f"Connection error: {err}") from err

    async def validate_token(self) -> bool:
        """Return True if the token is accepted by the API."""
        try:
            await self.get_records(last_updated=0)
            return True
        except KitchenPalAuthError:
            return False
        except KitchenPalApiError:
            return True
