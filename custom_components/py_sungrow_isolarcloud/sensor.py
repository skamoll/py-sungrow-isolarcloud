"""Sensor platform for Sungrow iSolarCloud."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import DeviceSummary, PlantData, ValueUnit
from .const import DOMAIN
from .coordinator import ISolarCloudCoordinator
from .entity import ISolarCloudDeviceEntity, ISolarCloudPlantEntity


@dataclass(frozen=True, kw_only=True)
class PlantSensorDescription(SensorEntityDescription):
    """Describe a curated plant-level sensor."""

    value_fn: Callable[[PlantData], Any]
    unit_fn: Callable[[PlantData], str | None] | None = None


@dataclass(frozen=True, kw_only=True)
class DeviceSensorDescription(SensorEntityDescription):
    """Describe a curated child-device sensor."""

    value_fn: Callable[[DeviceSummary], Any]


def _vu_value(vu: ValueUnit) -> float | None:
    return vu.value


def _vu_unit(vu: ValueUnit, fallback: str) -> str:
    return vu.unit or fallback


def _parse_iso_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = raw.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).astimezone()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


PLANT_SENSORS: tuple[PlantSensorDescription, ...] = (
    PlantSensorDescription(
        key="pv_power",
        translation_key="pv_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value_fn=lambda p: _vu_value(p.flow.pv_power),
        unit_fn=lambda p: _vu_unit(p.flow.pv_power, UnitOfPower.KILO_WATT),
    ),
    PlantSensorDescription(
        key="load_power",
        translation_key="load_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value_fn=lambda p: _vu_value(p.flow.load_power),
        unit_fn=lambda p: _vu_unit(p.flow.load_power, UnitOfPower.KILO_WATT),
    ),
    PlantSensorDescription(
        key="grid_power",
        translation_key="grid_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value_fn=lambda p: _vu_value(p.flow.grid_power),
        unit_fn=lambda p: _vu_unit(p.flow.grid_power, UnitOfPower.KILO_WATT),
    ),
    PlantSensorDescription(
        key="battery_power",
        translation_key="battery_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value_fn=lambda p: _vu_value(p.flow.battery_power),
        unit_fn=lambda p: _vu_unit(p.flow.battery_power, UnitOfPower.KILO_WATT),
    ),
    PlantSensorDescription(
        key="battery_soc",
        translation_key="battery_soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda p: p.flow.battery_soc,
    ),
    PlantSensorDescription(
        key="daily_pv_energy",
        translation_key="daily_pv_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.daily_pv_energy),
        unit_fn=lambda p: _vu_unit(p.flow.daily_pv_energy, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="total_pv_energy",
        translation_key="total_pv_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.total_pv_energy),
        unit_fn=lambda p: _vu_unit(p.flow.total_pv_energy, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="daily_battery_charge",
        translation_key="daily_battery_charge",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.daily_battery_charge),
        unit_fn=lambda p: _vu_unit(p.flow.daily_battery_charge, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="total_battery_charge",
        translation_key="total_battery_charge",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.total_battery_charge),
        unit_fn=lambda p: _vu_unit(p.flow.total_battery_charge, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="daily_battery_discharge",
        translation_key="daily_battery_discharge",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.daily_battery_discharge),
        unit_fn=lambda p: _vu_unit(p.flow.daily_battery_discharge, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="total_battery_discharge",
        translation_key="total_battery_discharge",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.total_battery_discharge),
        unit_fn=lambda p: _vu_unit(p.flow.total_battery_discharge, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="daily_grid_import",
        translation_key="daily_grid_import",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.daily_grid_import),
        unit_fn=lambda p: _vu_unit(p.flow.daily_grid_import, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="total_grid_import",
        translation_key="total_grid_import",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.total_grid_import),
        unit_fn=lambda p: _vu_unit(p.flow.total_grid_import, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="daily_grid_export",
        translation_key="daily_grid_export",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.daily_grid_export),
        unit_fn=lambda p: _vu_unit(p.flow.daily_grid_export, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="total_grid_export",
        translation_key="total_grid_export",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.total_grid_export),
        unit_fn=lambda p: _vu_unit(p.flow.total_grid_export, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="daily_load_energy",
        translation_key="daily_load_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.daily_load_energy),
        unit_fn=lambda p: _vu_unit(p.flow.daily_load_energy, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="total_load_energy",
        translation_key="total_load_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda p: _vu_value(p.flow.total_load_energy),
        unit_fn=lambda p: _vu_unit(p.flow.total_load_energy, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="installed_capacity",
        translation_key="installed_capacity",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="kWp",
        icon="mdi:solar-panel",
        value_fn=lambda p: p.flow.design_capacity_kwp or p.summary.design_capacity_kwp,
    ),
    PlantSensorDescription(
        key="last_update",
        translation_key="last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda p: _parse_iso_dt(p.flow.last_update_time),
    ),
)

DEVICE_SENSORS: tuple[DeviceSensorDescription, ...] = (
    DeviceSensorDescription(
        key="device_status_code",
        translation_key="device_status_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.dev_status,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sungrow iSolarCloud sensors from a config entry."""
    coordinator: ISolarCloudCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for ps_id, plant in (coordinator.data or {}).items():
        for desc in PLANT_SENSORS:
            entities.append(ISolarCloudPlantSensor(coordinator, ps_id, desc))
        for dev in plant.devices:
            for dev_desc in DEVICE_SENSORS:
                entities.append(ISolarCloudDeviceSensor(coordinator, ps_id, dev.ps_key, dev_desc))

    async_add_entities(entities)


class ISolarCloudPlantSensor(ISolarCloudPlantEntity, SensorEntity):
    """Plant-level iSolarCloud sensor."""

    entity_description: PlantSensorDescription

    def __init__(
        self,
        coordinator: ISolarCloudCoordinator,
        ps_id: str,
        description: PlantSensorDescription,
    ) -> None:
        super().__init__(coordinator, ps_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        plant = self.plant_data
        if plant is None:
            return None
        return self.entity_description.value_fn(plant)

    @property
    def native_unit_of_measurement(self) -> str | None:
        plant = self.plant_data
        if plant is not None and self.entity_description.unit_fn is not None:
            return self.entity_description.unit_fn(plant)
        return self.entity_description.native_unit_of_measurement


class ISolarCloudDeviceSensor(ISolarCloudDeviceEntity, SensorEntity):
    """Child-device iSolarCloud sensor."""

    entity_description: DeviceSensorDescription

    def __init__(
        self,
        coordinator: ISolarCloudCoordinator,
        ps_id: str,
        ps_key: str,
        description: DeviceSensorDescription,
    ) -> None:
        super().__init__(coordinator, ps_id, ps_key, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        dev = self.device_summary
        if dev is None:
            return None
        return self.entity_description.value_fn(dev)
