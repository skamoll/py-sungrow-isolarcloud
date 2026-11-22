"""End-to-end Home Assistant Core integration test (runs when homeassistant is installed)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

if importlib.util.find_spec("homeassistant") is None:
    pytest.skip("homeassistant package not installed", allow_module_level=True)

from homeassistant import bootstrap, loader
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.py_sungrow_isolarcloud.api.models import (
    DeviceSummary,
    PlantData,
    PlantFlow,
    PlantSummary,
    ValueUnit,
)
from custom_components.py_sungrow_isolarcloud.const import (
    CONF_GATEWAY,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)


def _sample_plant_data() -> dict[str, PlantData]:
    return {
        "6116893": PlantData(
            summary=PlantSummary(
                ps_id="6116893",
                ps_name="Casa",
                ps_status=1,
                design_capacity_kwp=6.0,
            ),
            flow=PlantFlow(
                pv_power=ValueUnit(2.45, "kW"),
                load_power=ValueUnit(1.10, "kW"),
                grid_power=ValueUnit(-1.35, "kW"),
                battery_power=ValueUnit(0.0, "kW"),
                battery_soc=88.0,
                daily_pv_energy=ValueUnit(14.2, "kWh"),
                total_pv_energy=ValueUnit(4863.0, "kWh"),
                last_update_time="2026-11-23 00:30:00",
            ),
            devices=[
                DeviceSummary(
                    ps_id="6116893",
                    ps_key="6116893_14_1_1",
                    uuid="8633308",
                    device_name="Inverter SH6.0RS",
                    device_model="SH6.0RS",
                    device_sn="SN123456",
                    device_type=14,
                    dev_status=1,
                )
            ],
        )
    }


@pytest.mark.asyncio
async def test_ha_setup_devices_entities_and_unload(tmp_path: Path) -> None:
    """Verify full setup, device hierarchy, entities, and unload on real HA Core."""
    (tmp_path / "custom_components").symlink_to(
        Path(__file__).resolve().parent.parent / "custom_components"
    )
    hass = HomeAssistant(str(tmp_path))
    loader.async_setup(hass)
    await bootstrap.async_from_config_dict({}, hass)
    await hass.async_start()
    try:
        entry = ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="iSolarCloud (test@example.com)",
            data={
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "secret",
                CONF_GATEWAY: "eu",
            },
            options={CONF_SCAN_INTERVAL: 120},
            source="user",
            unique_id="999:test@example.com",
            discovery_keys={},
            subentries_data=None,
        )
        with patch(
            "custom_components.py_sungrow_isolarcloud.api.client.ISolarCloudClient.async_fetch_all_plants",
            new=AsyncMock(return_value=_sample_plant_data()),
        ):
            await hass.config_entries.async_add(entry)
            await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED

        dev_reg = dr.async_get(hass)
        devices = dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
        assert len(devices) == 2

        plant_dev = dev_reg.async_get_device(identifiers={(DOMAIN, "plant_6116893")})
        child_dev = dev_reg.async_get_device(identifiers={(DOMAIN, "device_6116893_14_1_1")})
        assert plant_dev is not None
        assert child_dev is not None
        assert child_dev.via_device_id == plant_dev.id

        ent_reg = er.async_get(hass)
        entities = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
        assert len(entities) == 22
        assert not any(e.entity_id.endswith("_2") for e in entities)

        pv_state = hass.states.get("sensor.casa_pv_power")
        assert pv_state is not None
        assert pv_state.state == "2.45"
        assert pv_state.attributes["unit_of_measurement"] == "kW"

        soc_state = hass.states.get("sensor.casa_battery_soc")
        assert soc_state is not None
        assert soc_state.state == "88.0"

        online_state = hass.states.get("binary_sensor.casa_online")
        assert online_state is not None
        assert online_state.state == "on"

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.NOT_LOADED
    finally:
        await hass.async_stop()
