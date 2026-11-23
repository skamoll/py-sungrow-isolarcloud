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

from .api import DevicePoint, DeviceSummary, PlantData, ValueUnit
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
        suggested_display_precision=2,
        icon="mdi:solar-panel",
        value_fn=lambda p: p.flow.design_capacity_kwp or p.summary.design_capacity_kwp,
    ),
    PlantSensorDescription(
        key="month_pv_energy",
        translation_key="month_pv_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda p: _vu_value(p.flow.month_pv_energy),
        unit_fn=lambda p: _vu_unit(p.flow.month_pv_energy, UnitOfEnergy.KILO_WATT_HOUR),
    ),
    PlantSensorDescription(
        key="today_income",
        translation_key="today_income",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda p: _vu_value(p.flow.today_income),
        unit_fn=lambda p: _vu_unit(p.flow.today_income, "EUR"),
    ),
    PlantSensorDescription(
        key="total_income",
        translation_key="total_income",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda p: _vu_value(p.flow.total_income),
        unit_fn=lambda p: _vu_unit(p.flow.total_income, "EUR"),
    ),
    PlantSensorDescription(
        key="co2_reduced_total",
        translation_key="co2_reduced_total",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        icon="mdi:molecule-co2",
        value_fn=lambda p: _vu_value(p.flow.co2_reduced_total),
        unit_fn=lambda p: _vu_unit(p.flow.co2_reduced_total, "t"),
    ),
    PlantSensorDescription(
        key="plant_status",
        translation_key="plant_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:solar-power-variant",
        value_fn=lambda p: p.summary.status_text,
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
            if (
                desc.key.startswith(("total_", "month_", "today_income", "co2_"))
                and desc.value_fn(plant) is None
            ):
                continue
            entities.append(ISolarCloudPlantSensor(coordinator, ps_id, desc))
        for dev in plant.devices:
            for dev_desc in DEVICE_SENSORS:
                entities.append(ISolarCloudDeviceSensor(coordinator, ps_id, dev.ps_key, dev_desc))
            for point_id in sorted(dev.points):
                entities.append(
                    ISolarCloudDevicePointSensor(coordinator, ps_id, dev.ps_key, point_id)
                )

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
        value = self.entity_description.value_fn(plant)
        if value is None and self.entity_description.key == "last_update":
            return self.coordinator.last_sync_utc
        return value

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


_UNIT_DEVICE_CLASS: dict[str, tuple[SensorDeviceClass | None, SensorStateClass | None]] = {
    "W": (SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    "kW": (SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    "MW": (SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    "Wh": (SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    "kWh": (SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    "MWh": (SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    "V": (SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    "A": (SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    "Hz": (SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),
    "°C": (SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "°F": (SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "var": (SensorDeviceClass.REACTIVE_POWER, SensorStateClass.MEASUREMENT),
    "VA": (SensorDeviceClass.APPARENT_POWER, SensorStateClass.MEASUREMENT),
    "W/m²": (SensorDeviceClass.IRRADIANCE, SensorStateClass.MEASUREMENT),
}


def _classify_point(
    point: DevicePoint,
) -> tuple[SensorDeviceClass | None, SensorStateClass | None]:
    if not point.is_numeric:
        return None, None
    if point.unit == "%":
        lower_name = point.name.lower()
        if "soc" in lower_name or "battery" in lower_name:
            return SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT
        return None, SensorStateClass.MEASUREMENT
    if point.unit and point.unit in _UNIT_DEVICE_CLASS:
        return _UNIT_DEVICE_CLASS[point.unit]
    return None, SensorStateClass.MEASUREMENT


_DIAGNOSTIC_POINT_KEYWORDS: tuple[str, ...] = (
    "wlan",
    "signal",
    "meter type",
    "insulation",
    "resistance",
    "bms",
    "max. charging",
    "max. discharging",
    "operating status",
    "fault",
    "alarm",
    "firmware",
    "software",
    "version",
    "serial",
    "contactor",
)


def _is_diagnostic_point(name: str) -> bool:
    lower = name.lower()
    return any(keyword in lower for keyword in _DIAGNOSTIC_POINT_KEYWORDS)


class ISolarCloudDevicePointSensor(ISolarCloudDeviceEntity, SensorEntity):
    """Generic telemetry sensor backed by /v1/devService/getDevicePoints."""

    def __init__(
        self,
        coordinator: ISolarCloudCoordinator,
        ps_id: str,
        ps_key: str,
        point_id: int,
    ) -> None:
        super().__init__(coordinator, ps_id, ps_key, f"p{point_id}")
        self._point_id = point_id
        pt = self._current_point()
        if pt is not None:
            self._attr_name = pt.name
            self._attr_native_unit_of_measurement = pt.unit
            dc, sc = _classify_point(pt)
            self._attr_device_class = dc
            self._attr_state_class = sc
            if _is_diagnostic_point(pt.name):
                self._attr_entity_category = EntityCategory.DIAGNOSTIC
            if pt.is_numeric and pt.unit not in ("%", None):
                self._attr_suggested_display_precision = 2
        else:
            self._attr_name = f"Point {point_id}"

    def _current_point(self) -> DevicePoint | None:
        dev = self.device_summary
        if dev is None:
            return None
        return dev.points.get(self._point_id)

    @property
    def native_value(self) -> float | str | None:
        pt = self._current_point()
        if pt is None:
            return None
        return pt.value
