"""Binary sensor platform for Sungrow iSolarCloud."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ISolarCloudCoordinator
from .entity import ISolarCloudDeviceEntity, ISolarCloudPlantEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sungrow iSolarCloud binary sensors from a config entry."""
    coordinator: ISolarCloudCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = []

    for ps_id, plant in (coordinator.data or {}).items():
        entities.append(ISolarCloudPlantOnlineBinarySensor(coordinator, ps_id))
        entities.append(ISolarCloudPlantFaultBinarySensor(coordinator, ps_id))
        for dev in plant.devices:
            entities.append(ISolarCloudDeviceOnlineBinarySensor(coordinator, ps_id, dev.ps_key))
            entities.append(ISolarCloudDeviceFaultBinarySensor(coordinator, ps_id, dev.ps_key))

    async_add_entities(entities)


class ISolarCloudPlantOnlineBinarySensor(ISolarCloudPlantEntity, BinarySensorEntity):
    """Connectivity binary sensor for a Sungrow plant."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "plant_online"

    def __init__(self, coordinator: ISolarCloudCoordinator, ps_id: str) -> None:
        super().__init__(coordinator, ps_id, "online")

    @property
    def is_on(self) -> bool | None:
        plant = self.plant_data
        if plant is None:
            return None
        return plant.summary.is_online


class ISolarCloudDeviceOnlineBinarySensor(ISolarCloudDeviceEntity, BinarySensorEntity):
    """Connectivity binary sensor for a child Sungrow device."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "device_online"

    def __init__(
        self,
        coordinator: ISolarCloudCoordinator,
        ps_id: str,
        ps_key: str,
    ) -> None:
        super().__init__(coordinator, ps_id, ps_key, "online")

    @property
    def is_on(self) -> bool | None:
        dev = self.device_summary
        if dev is None:
            return None
        return dev.is_online


class ISolarCloudPlantFaultBinarySensor(ISolarCloudPlantEntity, BinarySensorEntity):
    """Problem/fault binary sensor for a Sungrow plant."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "plant_fault"

    def __init__(self, coordinator: ISolarCloudCoordinator, ps_id: str) -> None:
        super().__init__(coordinator, ps_id, "fault")

    @property
    def is_on(self) -> bool | None:
        plant = self.plant_data
        if plant is None:
            return None
        return plant.flow.has_fault


class ISolarCloudDeviceFaultBinarySensor(ISolarCloudDeviceEntity, BinarySensorEntity):
    """Problem/fault binary sensor for a child Sungrow device."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "device_fault"

    def __init__(
        self,
        coordinator: ISolarCloudCoordinator,
        ps_id: str,
        ps_key: str,
    ) -> None:
        super().__init__(coordinator, ps_id, ps_key, "fault")

    @property
    def is_on(self) -> bool | None:
        dev = self.device_summary
        if dev is None:
            return None
        return dev.has_fault
