"""Base entity classes for Sungrow iSolarCloud."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DeviceSummary, PlantData
from .const import DOMAIN
from .coordinator import ISolarCloudCoordinator


def format_plant_device_name(ps_name: str | None, ps_id: str) -> str:
    """Return a consistent PV-prefixed plant device name."""
    raw = (ps_name or "").strip() or f"Plant {ps_id}"
    if raw.lower().startswith("pv "):
        return raw
    return f"PV {raw}"


class ISolarCloudPlantEntity(CoordinatorEntity[ISolarCloudCoordinator]):
    """Base entity attached to a Sungrow Plant device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ISolarCloudCoordinator,
        ps_id: str,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._ps_id = ps_id
        self._attr_unique_id = f"plant_{ps_id}_{key}"

    @property
    def plant_data(self) -> PlantData | None:
        """Return current PlantData for this entity's plant."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._ps_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return stable Plant DeviceInfo."""
        plant = self.plant_data
        name = format_plant_device_name(plant.summary.ps_name if plant else None, self._ps_id)
        return DeviceInfo(
            identifiers={(DOMAIN, f"plant_{self._ps_id}")},
            manufacturer="Sungrow",
            model="Power Station",
            name=name,
        )


class ISolarCloudDeviceEntity(CoordinatorEntity[ISolarCloudCoordinator]):
    """Base entity attached to a child Sungrow device (inverter, battery, meter)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ISolarCloudCoordinator,
        ps_id: str,
        ps_key: str,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._ps_id = ps_id
        self._ps_key = ps_key
        self._attr_unique_id = f"device_{ps_key}_{key}"

    @property
    def device_summary(self) -> DeviceSummary | None:
        """Return current DeviceSummary for this entity's device."""
        if not self.coordinator.data:
            return None
        plant = self.coordinator.data.get(self._ps_id)
        if not plant:
            return None
        for dev in plant.devices:
            if dev.ps_key == self._ps_key:
                return dev
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return stable child DeviceInfo linked to its Plant."""
        dev = self.device_summary
        kwargs: dict[str, Any] = {
            "identifiers": {(DOMAIN, f"device_{self._ps_key}")},
            "manufacturer": "Sungrow",
            "model": (dev.device_model if dev and dev.device_model else "Sungrow Device"),
            "name": (dev.device_name if dev else self._ps_key),
            "serial_number": (dev.device_sn if dev else None),
            "sw_version": (dev.firmware_version if dev else None),
        }
        if "via_device_id" in DeviceInfo.__annotations__:
            if self.hass is not None:
                plant_dev = dr.async_get(self.hass).async_get_device(
                    identifiers={(DOMAIN, f"plant_{self._ps_id}")}
                )
                if plant_dev is not None:
                    kwargs["via_device_id"] = plant_dev.id
        else:
            kwargs["via_device"] = (DOMAIN, f"plant_{self._ps_id}")
        return DeviceInfo(**kwargs)
