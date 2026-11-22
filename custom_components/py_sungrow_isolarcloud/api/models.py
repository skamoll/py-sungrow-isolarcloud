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

    @classmethod
    def from_detail_dict(cls, data: dict[str, Any]) -> PlantFlow:
        """Parse PsDetailBeanOversea fields into PlantFlow."""
        pv = ValueUnit.from_raw(
            data.get("pv_power_map") or data.get("curr_power"),
            "kW",
        )
        load = ValueUnit.from_raw(data.get("load_power_map"), "kW")
        grid = ValueUnit.from_raw(data.get("power_grid_power_map"), "kW")
        battery = ValueUnit.from_raw(
            data.get("charging_discharging_power_map") or data.get("es_active_power_map"),
            "kW",
        )
        soc = parse_float(data.get("battery_level_percent"))
        cap = ValueUnit.from_raw(data.get("design_capacity"), "kWp")

        return cls(
            pv_power=pv,
            load_power=load,
            grid_power=grid,
            battery_power=battery,
            battery_soc=soc,
            daily_pv_energy=ValueUnit.from_raw(
                data.get("today_energy") or data.get("p83022_map"),
                "kWh",
            ),
            total_pv_energy=ValueUnit.from_raw(
                data.get("total_energy") or data.get("p83024_map"),
                "kWh",
            ),
            daily_battery_charge=ValueUnit.from_raw(
                data.get("dc_charge_today_energy") or data.get("today_es_charge_energy"),
                "kWh",
            ),
            total_battery_charge=ValueUnit.from_raw(
                data.get("dc_charge_total_energy") or data.get("total_es_charge_energy"),
                "kWh",
            ),
            daily_battery_discharge=ValueUnit.from_raw(
                data.get("today_es_discharge_energy"),
                "kWh",
            ),
            total_battery_discharge=ValueUnit.from_raw(
                data.get("total_es_discharge_energy"),
                "kWh",
            ),
            daily_grid_import=ValueUnit.from_raw(
                data.get("today_buy_energy"),
                "kWh",
            ),
            total_grid_import=ValueUnit.from_raw(
                data.get("total_buy_energy"),
                "kWh",
            ),
            daily_grid_export=ValueUnit.from_raw(
                data.get("today_sell_energy"),
                "kWh",
            ),
            total_grid_export=ValueUnit.from_raw(
                data.get("total_sell_energy"),
                "kWh",
            ),
            daily_load_energy=ValueUnit.from_raw(
                data.get("today_use_energy"),
                "kWh",
            ),
            total_load_energy=ValueUnit.from_raw(
                data.get("total_use_energy"),
                "kWh",
            ),
            design_capacity_kwp=cap.value,
            last_update_time=data.get("data_last_update_time") or data.get("update_time"),
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
    firmware_version: str | None = None

    @property
    def is_online(self) -> bool:
        """Return True when device status indicates online/normal."""
        return self.dev_status == 1

    @classmethod
    def from_dict(cls, ps_id: str, data: dict[str, Any]) -> DeviceSummary:
        """Build DeviceSummary from a getPsAllDeviceList row."""
        dev_type_raw = parse_float(data.get("device_type"))
        status_raw = parse_float(data.get("dev_status") or data.get("dev_run_status"))
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
            firmware_version=data.get("firmware_version_info") or data.get("soft_version"),
        )


@dataclass(slots=True)
class PlantData:
    """Combined plant snapshot consumed by Home Assistant entities."""

    summary: PlantSummary
    flow: PlantFlow
    devices: list[DeviceSummary] = field(default_factory=list)
