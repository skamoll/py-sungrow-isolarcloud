"""Typed models and unit normalization for iSolarCloud responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

_UNIT_MAP: dict[str, str] = {
    "℃": "°C",
    "C": "°C",
    "℉": "°F",
    "F": "°F",
    "kvar": "var",
    "KVAR": "var",
    "W/㎡": "W/m²",
    "Wh/㎡": "Wh/m²",
}


def normalize_unit(unit: str | None) -> str | None:
    """Normalize Sungrow unit strings to Home Assistant canonical units."""
    if unit is None:
        return None
    cleaned = unit.strip()
    if not cleaned or cleaned == "--":
        return None
    return _UNIT_MAP.get(cleaned, cleaned)


def parse_float(raw: Any) -> float | None:
    """Parse numeric API values safely, treating '--' and blanks as None."""
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if not text or text == "--":
        return None
    try:
        return float(text)
    except ValueError:
        return None


@dataclass(slots=True)
class AuthSession:
    """Authenticated iSolarCloud session details."""

    token: str
    user_id: str
    gateway: str
    login_at: datetime


@dataclass(slots=True)
class ValueUnit:
    """Typed value + normalized unit extracted from iSolarCloud maps."""

    value: float | None
    unit: str | None = None

    @classmethod
    def from_raw(cls, raw: Any, default_unit: str | None = None) -> ValueUnit:
        """Parse either a {value, unit} dict or a scalar value."""
        if isinstance(raw, dict):
            val = parse_float(raw.get("value"))
            unit = normalize_unit(raw.get("unit")) or normalize_unit(default_unit)
            return cls(value=val, unit=unit)
        return cls(value=parse_float(raw), unit=normalize_unit(default_unit))

    def in_kw(self) -> ValueUnit:
        """Convert W/kW/MW value to canonical kW."""
        if self.value is None:
            return ValueUnit(None, "kW")
        if self.unit == "W":
            return ValueUnit(round(self.value / 1000.0, 4), "kW")
        if self.unit == "MW":
            return ValueUnit(round(self.value * 1000.0, 4), "kW")
        return ValueUnit(self.value, "kW")

    def in_kwh(self) -> ValueUnit:
        """Convert Wh/kWh/MWh value to canonical kWh."""
        if self.value is None:
            return ValueUnit(None, "kWh")
        if self.unit == "Wh":
            return ValueUnit(round(self.value / 1000.0, 4), "kWh")
        if self.unit == "MWh":
            return ValueUnit(round(self.value * 1000.0, 4), "kWh")
        return ValueUnit(self.value, "kWh")


@dataclass(slots=True)
class PlantSummary:
    """Plant metadata from getPsList."""

    ps_id: str
    ps_name: str
    ps_status: int | None = None
    ps_type: int | None = None
    design_capacity_kwp: float | None = None
    timezone: str | None = None

    @property
    def is_online(self) -> bool:
        """Return True when plant status indicates normal/online operation."""
        return self.ps_status == 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlantSummary:
        """Build PlantSummary from a getPsList item."""
        cap = ValueUnit.from_raw(data.get("design_capacity"), "kWp")
        if cap.value is None:
            cap = ValueUnit.from_raw(data.get("total_capcity"), "kWp")
        status_raw = parse_float(data.get("ps_status"))
        ps_type_raw = parse_float(data.get("ps_type"))
        return cls(
            ps_id=str(data.get("ps_id", "")),
            ps_name=str(data.get("ps_name") or data.get("ps_id") or "iSolarCloud Plant"),
            ps_status=int(status_raw) if status_raw is not None else None,
            ps_type=int(ps_type_raw) if ps_type_raw is not None else None,
            design_capacity_kwp=cap.value,
            timezone=data.get("time_zone") or data.get("ps_time_zone"),
        )


@dataclass(slots=True)
class PlantFlow:
    """Curated plant power flow & energy metrics from getPsDetailWithPsType."""

    pv_power: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kW"))
    load_power: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kW"))
    grid_power: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kW"))
    battery_power: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kW"))
    battery_soc: float | None = None
    daily_pv_energy: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    total_pv_energy: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    daily_battery_charge: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    total_battery_charge: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    daily_battery_discharge: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    total_battery_discharge: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    daily_grid_import: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    total_grid_import: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    daily_grid_export: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    total_grid_export: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    daily_load_energy: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    total_load_energy: ValueUnit = field(default_factory=lambda: ValueUnit(None, "kWh"))
    design_capacity_kwp: float | None = None
    last_update_time: str | None = None
    ps_fault_status: str | None = None

    @property
    def has_fault(self) -> bool:
        """Return True when plant fault status indicates an active fault or alarm."""
        return self.ps_fault_status in ("1", "2")

    @classmethod
    def from_detail_dict(cls, data: dict[str, Any]) -> PlantFlow:
        """Parse PsDetailBeanOversea fields into PlantFlow with canonical kW/kWh units."""
        pv = ValueUnit.from_raw(
            data.get("pv_power_map") or data.get("curr_power"),
            "kW",
        ).in_kw()
        load = ValueUnit.from_raw(data.get("load_power_map"), "kW").in_kw()
        grid = ValueUnit.from_raw(data.get("power_grid_power_map"), "kW").in_kw()
        battery = ValueUnit.from_raw(
            data.get("charging_discharging_power_map") or data.get("es_active_power_map"),
            "kW",
        ).in_kw()
        soc = parse_float(data.get("battery_level_percent"))
        cap = ValueUnit.from_raw(data.get("design_capacity"), "kWp")

        daily_pv = ValueUnit.from_raw(
            data.get("today_energy_virgin")
            or data.get("today_energy")
            or data.get("pv_energy_map"),
            "kWh",
        ).in_kwh()
        total_pv = ValueUnit.from_raw(
            data.get("total_energy_virgin") or data.get("total_energy"),
            "kWh",
        ).in_kwh()

        return cls(
            pv_power=pv,
            load_power=load,
            grid_power=grid,
            battery_power=battery,
            battery_soc=soc,
            daily_pv_energy=daily_pv,
            total_pv_energy=total_pv,
            daily_battery_charge=ValueUnit.from_raw(
                data.get("battery_charge_energy_map")
                or data.get("dc_charge_today_energy")
                or data.get("today_es_charge_energy"),
                "kWh",
            ).in_kwh(),
            total_battery_charge=ValueUnit.from_raw(
                data.get("dc_charge_total_energy") or data.get("total_es_charge_energy"),
                "kWh",
            ).in_kwh(),
            daily_battery_discharge=ValueUnit.from_raw(
                data.get("battery_discharge_energy_map") or data.get("today_es_discharge_energy"),
                "kWh",
            ).in_kwh(),
            total_battery_discharge=ValueUnit.from_raw(
                data.get("total_es_discharge_energy"),
                "kWh",
            ).in_kwh(),
            daily_grid_import=ValueUnit.from_raw(
                data.get("purchased_energy_map") or data.get("today_buy_energy"),
                "kWh",
            ).in_kwh(),
            total_grid_import=ValueUnit.from_raw(
                data.get("total_buy_energy"),
                "kWh",
            ).in_kwh(),
            daily_grid_export=ValueUnit.from_raw(
                data.get("feed_in_energy_map") or data.get("today_sell_energy"),
                "kWh",
            ).in_kwh(),
            total_grid_export=ValueUnit.from_raw(
                data.get("total_sell_energy"),
                "kWh",
            ).in_kwh(),
            daily_load_energy=ValueUnit.from_raw(
                data.get("load_energy_map") or data.get("today_use_energy"),
                "kWh",
            ).in_kwh(),
            total_load_energy=ValueUnit.from_raw(
                data.get("total_use_energy"),
                "kWh",
            ).in_kwh(),
            design_capacity_kwp=cap.value,
            last_update_time=data.get("data_last_update_time") or data.get("update_time"),
            ps_fault_status=(
                str(data.get("ps_fault_status"))
                if data.get("ps_fault_status") is not None
                else None
            ),
        )


@dataclass(slots=True)
class DevicePoint:
    """Generic curated device telemetry point from /v1/devService/getDevicePoints."""

    point_id: int
    name: str
    value: float | str | None
    unit: str | None = None
    is_numeric: bool = False
    is_enum: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DevicePoint | None:
        """Parse one getDevicePoints row, returning None for unsupported '--' points."""
        point_id_raw = data.get("point_id")
        if point_id_raw is None:
            return None
        try:
            point_id = int(point_id_raw)
        except (TypeError, ValueError):
            return None

        raw_val = data.get("value")
        if raw_val is None or str(raw_val).strip() in ("", "--"):
            return None

        name = str(
            data.get("alias_point_name") or data.get("point_name") or f"Point {point_id}"
        ).strip()
        unit = normalize_unit(data.get("unit"))
        is_enum = str(data.get("flag") or "").lower() == "enum"

        parsed_num = None if is_enum else parse_float(raw_val)
        if parsed_num is not None:
            return cls(
                point_id=point_id,
                name=name,
                value=parsed_num,
                unit=unit,
                is_numeric=True,
                is_enum=False,
            )

        desc = str(data.get("value_description") or "").strip()
        text_val = desc if desc and is_enum else str(raw_val).strip()
        return cls(
            point_id=point_id,
            name=name,
            value=text_val,
            unit=None,
            is_numeric=False,
            is_enum=is_enum,
        )


@dataclass(slots=True)
class DeviceSummary:
    """Device inventory entry from getPsAllDeviceList."""

    ps_id: str
    ps_key: str
    uuid: str
    device_name: str
    device_model: str | None = None
    device_sn: str | None = None
    device_type: int | None = None
    dev_status: int | None = None
    fault_status: str | None = None
    firmware_version: str | None = None
    points: dict[int, DevicePoint] = field(default_factory=dict)

    @property
    def is_online(self) -> bool:
        """Return True when device status indicates online/normal."""
        return self.dev_status == 1

    @property
    def has_fault(self) -> bool:
        """Return True when device fault status indicates an active fault or alarm."""
        return self.fault_status in ("1", "2")

    @classmethod
    def from_dict(cls, ps_id: str, data: dict[str, Any]) -> DeviceSummary:
        """Build DeviceSummary from a getPsAllDeviceList row."""
        dev_type_raw = parse_float(data.get("device_type"))
        status_raw = parse_float(
            data.get("device_status")
            if data.get("device_status") is not None
            else (data.get("dev_status") or data.get("dev_run_status"))
        )
        ps_key = str(data.get("ps_key") or data.get("uuid") or "")
        return cls(
            ps_id=str(data.get("ps_id") or ps_id),
            ps_key=ps_key,
            uuid=str(data.get("uuid") or ps_key),
            device_name=str(data.get("device_name") or data.get("device_model") or ps_key),
            device_model=data.get("device_model") or data.get("type_name"),
            device_sn=data.get("device_sn") or data.get("sn"),
            device_type=int(dev_type_raw) if dev_type_raw is not None else None,
            dev_status=int(status_raw) if status_raw is not None else None,
            fault_status=(
                str(data.get("fault_status")) if data.get("fault_status") is not None else None
            ),
            firmware_version=data.get("firmware_version_info") or data.get("soft_version"),
        )


@dataclass(slots=True)
class PlantData:
    """Combined plant snapshot consumed by Home Assistant entities."""

    summary: PlantSummary
    flow: PlantFlow
    devices: list[DeviceSummary] = field(default_factory=list)
