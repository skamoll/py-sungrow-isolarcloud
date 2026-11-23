"""DataUpdateCoordinator for Sungrow iSolarCloud."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    ISolarCloudApiError,
    ISolarCloudAuthError,
    ISolarCloudClient,
    ISolarCloudConnectionError,
    PlantData,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ISolarCloudCoordinator(DataUpdateCoordinator[dict[str, PlantData]]):
    """Coordinator that polls iSolarCloud once per interval for all plants."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ISolarCloudClient,
        scan_interval_seconds: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval_seconds),
        )
        self.client = client
        self.last_sync_utc: datetime | None = None

    async def _async_update_data(self) -> dict[str, PlantData]:
        try:
            data = await self.client.async_fetch_all_plants()
            self.last_sync_utc = dt_util.utcnow()
            return data
        except ISolarCloudAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except (ISolarCloudConnectionError, ISolarCloudApiError) as err:
            raise UpdateFailed(f"Error communicating with iSolarCloud: {err}") from err
