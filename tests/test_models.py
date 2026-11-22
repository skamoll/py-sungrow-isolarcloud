"""Tests for iSolarCloud models and unit normalization."""

from __future__ import annotations

from custom_components.py_sungrow_isolarcloud.api.models import (
    DeviceSummary,
    PlantFlow,
    PlantSummary,
    ValueUnit,
    normalize_unit,
    parse_float,
)


def test_normalize_unit() -> None:
    """Sungrow legacy units normalize to Home Assistant canonical units."""
    assert normalize_unit("℃") == "°C"
    assert normalize_unit("C") == "°C"
    assert normalize_unit("℉") == "°F"
    assert normalize_unit("kvar") == "var"
    assert normalize_unit("W/㎡") == "W/m²"
    assert normalize_unit("--") is None
    assert normalize_unit("  ") is None
    assert normalize_unit("kWh") == "kWh"


def test_parse_float() -> None:
    """parse_float handles numbers, strings, '--', and invalid values."""
    assert parse_float(12) == 12.0
    assert parse_float("3.14") == 3.14
    assert parse_float("--") is None
    assert parse_float("") is None
    assert parse_float(True) is None
    assert parse_float("abc") is None


def test_value_unit_from_raw() -> None:
    """ValueUnit parses both dict maps and scalar inputs."""
    vu_dict = ValueUnit.from_raw({"value": "1.25", "unit": "kW"})
    assert vu_dict.value == 1.25
    assert vu_dict.unit == "kW"

    vu_scalar = ValueUnit.from_raw("42.5", "℃")
    assert vu_scalar.value == 42.5
    assert vu_scalar.unit == "°C"

    assert ValueUnit(715.0, "W").in_kw() == ValueUnit(0.715, "kW")
    assert ValueUnit(4880500.0, "Wh").in_kwh() == ValueUnit(4880.5, "kWh")
    assert ValueUnit(4.9, "MWh").in_kwh() == ValueUnit(4900.0, "kWh")


def test_plant_summary_and_flow() -> None:
    """PlantSummary and PlantFlow parse curated endpoint payloads."""
    summary = PlantSummary.from_dict(
        {
            "ps_id": 6116893,
            "ps_name": "Casa",
            "ps_status": "1",
            "design_capacity": {"value": "6.0", "unit": "kWp"},
        }
    )
    assert summary.ps_id == "6116893"
    assert summary.ps_name == "Casa"
    assert summary.is_online is True
    assert summary.design_capacity_kwp == 6.0

    flow = PlantFlow.from_detail_dict(
        {
            "pv_power_map": {"value": "2.45", "unit": "kW"},
            "load_power_map": {"value": "1.10", "unit": "kW"},
            "power_grid_power_map": {"value": "-1.35", "unit": "kW"},
            "charging_discharging_power_map": {"value": "0.0", "unit": "kW"},
            "battery_level_percent": "88",
            "today_energy": {"value": "14.2", "unit": "kWh"},
            "total_energy": {"value": "4863.0", "unit": "kWh"},
            "data_last_update_time": "2026-11-23 00:30:00",
        }
    )
    assert flow.pv_power.value == 2.45
    assert flow.load_power.value == 1.10
    assert flow.grid_power.value == -1.35
    assert flow.battery_soc == 88.0
    assert flow.daily_pv_energy.value == 14.2
    assert flow.total_pv_energy.value == 4863.0


def test_device_summary() -> None:
    """DeviceSummary preserves stable ps_key and metadata."""
    dev = DeviceSummary.from_dict(
        "6116893",
        {
            "ps_key": "6116893_14_1_1",
            "uuid": "8633308",
            "device_name": "SH6.0RS",
            "device_model": "SH6.0RS",
            "device_sn": "A123456789",
            "device_type": 14,
            "dev_status": 1,
        },
    )
    assert dev.ps_key == "6116893_14_1_1"
    assert dev.is_online is True
    assert dev.device_model == "SH6.0RS"
