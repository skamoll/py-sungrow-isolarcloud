"""Diagnostics support for Sungrow iSolarCloud."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import ISolarCloudCoordinator

TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    "token",
    "user_id",
    "device_sn",
    "sn",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return redacted diagnostics for a Sungrow iSolarCloud config entry."""
    coordinator: ISolarCloudCoordinator = hass.data[DOMAIN][entry.entry_id]
    plants_dump: dict[str, Any] = {}
    for ps_id, plant in (coordinator.data or {}).items():
        plants_dump[ps_id] = {
            "summary": asdict(plant.summary),
            "flow": asdict(plant.flow),
            "devices": [
                {
                    "ps_key": dev.ps_key,
                    "device_name": dev.device_name,
                    "device_type": dev.device_type,
                    "device_model": dev.device_model,
                    "type_name": dev.type_name,
                    "dev_status": dev.dev_status,
                    "fault_status": dev.fault_status,
                    "point_count": len(dev.points),
                    "points": {
                        str(pid): {
                            "name": pt.name,
                            "value": pt.value,
                            "unit": pt.unit,
                        }
                        for pid, pt in sorted(dev.points.items())
                    },
                }
                for dev in plant.devices
            ],
            "active_faults": [asdict(f) for f in plant.active_faults],
            "weather": asdict(plant.weather) if plant.weather else None,
            "charging_piles": [asdict(p) for p in plant.charging_piles],
            "battery_info": plant.battery_info,
        }

    return {
        "entry": async_redact_data(
            {
                "title": entry.title,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            TO_REDACT,
        ),
        "last_sync_utc": (
            coordinator.last_sync_utc.isoformat() if coordinator.last_sync_utc else None
        ),
        "plants": async_redact_data(plants_dump, TO_REDACT),
    }
