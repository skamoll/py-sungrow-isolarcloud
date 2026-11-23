# Sungrow iSolarCloud for Home Assistant

[![CI](https://github.com/skamoll/py-sungrow-isolarcloud/actions/workflows/ci.yml/badge.svg)](https://github.com/skamoll/py-sungrow-isolarcloud/actions/workflows/ci.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight, native Home Assistant custom integration (`py_sungrow_isolarcloud`) for monitoring the full **Sungrow iSolarCloud** ecosystem — PV plants, hybrid and string inverters, batteries, smart meters, EV chargers, and communication modules — without external add-ons or an MQTT broker.

---

## Key Features

- **Full Ecosystem Support:** Works across Sungrow plant types and hardware by combining curated plant-level flow/energy metrics with dynamic per-device telemetry discovery (`/v1/devService/getDevicePoints`), conditional EV charger discovery, and plant battery summaries.
- **Native UI Setup & Options (`ConfigFlow` / `OptionsFlow` / `Reauth`):** Configure credentials, regional gateway (`auto` or `eu`, `com`, `au`, `hk`, `cn`, `in`), and polling interval (`30s`–`600s`, default `120s`) directly in Home Assistant.
- **Stable English `entity_id`s + Localized UI:** All plant devices use a `PV <plant>` prefix (`sensor.pv_<plant>_*`) and Home Assistant derives deterministic English `entity_id`s from `translations/en.json`, while displaying localized names (`en` / `es`) in the UI.
- **Energy Dashboard & Flow Card Ready:** Canonical `kW` / `kWh` units, `TOTAL_INCREASING` energy counters, and split directional power sensors (`grid_import_power`, `grid_export_power`, `battery_charge_power`, `battery_discharge_power`).
- **Clean Entity Categorization:** Technical device telemetry (`WLAN signal`, `Meter type`, `Insulation resistance`, `BMS` limits, `Operating status`, firmware/fault/contactor points) is automatically placed under `EntityCategory.DIAGNOSTIC`.
- **Zero-Overhead Fault Details:** Active fault details (`/v1/faultService/queryFaultList`) are queried **only** when a plant or device reports an active fault, exposing `fault_count` and `faults` as attributes on `binary_sensor.*_fault`.
- **On-Demand Refresh & Redacted Diagnostics:** Includes a `Refresh data` diagnostic button and standard Home Assistant `diagnostics.py` support (redacting credentials, tokens, user IDs, and serial numbers).

---

## Installation

### Option 1: HACS (Custom Repository)

1. Open **HACS** in Home Assistant → **Integrations** → **⋮** → **Custom repositories**.
2. Add `https://github.com/skamoll/py-sungrow-isolarcloud` with category **Integration**.
3. Search for **Sungrow iSolarCloud** and install it.
4. Restart Home Assistant.

### Option 2: Manual Installation

1. Copy `custom_components/py_sungrow_isolarcloud` into `<config>/custom_components/py_sungrow_isolarcloud`.
2. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Sungrow iSolarCloud**.
3. Choose your regional gateway (**Auto** is recommended; it probes `eu`, `com`, `au`, `hk`, `cn`, `in` in order) and enter your iSolarCloud email and password.
4. Optional: Click **Configure** on the integration entry at any time to adjust the polling interval (`30`–`600` seconds).

---

## Entities Created

### Plant Device (`PV <Plant Name>`)

| Entity / Key | Device Class / State Class | Unit | Notes |
|---|---|---|---|
| `pv_power` | `power` / `measurement` | `kW` | Current solar generation |
| `load_power` | `power` / `measurement` | `kW` | Current house/load consumption |
| `grid_power` | `power` / `measurement` | `kW` | Signed net grid exchange (`+` import, `-` export) |
| `grid_import_power` | `power` / `measurement` | `kW` | Non-negative grid import power |
| `grid_export_power` | `power` / `measurement` | `kW` | Non-negative grid export power |
| `battery_power` | `power` / `measurement` | `kW` | Signed net battery power (`+` charge, `-` discharge) |
| `battery_charge_power` | `power` / `measurement` | `kW` | Non-negative battery charging power |
| `battery_discharge_power` | `power` / `measurement` | `kW` | Non-negative battery discharging power |
| `battery_soc` | `battery` / `measurement` | `%` | Plant battery state of charge |
| `daily_pv_energy` / `total_pv_energy` | `energy` / `total_increasing` | `kWh` | Daily & cumulative PV generation |
| `month_pv_energy` | `energy` / `total_increasing` | `kWh` | Current month PV generation |
| `daily_self_consumption_energy` | `energy` / `total_increasing` | `kWh` | Daily direct solar self-consumption |
| `daily_grid_import` / `total_grid_import`* | `energy` / `total_increasing` | `kWh` | Grid energy imported |
| `daily_grid_export` / `total_grid_export`* | `energy` / `total_increasing` | `kWh` | Grid energy exported |
| `daily_battery_charge` / `total_battery_charge`* | `energy` / `total_increasing` | `kWh` | Battery energy charged |
| `daily_battery_discharge` / `total_battery_discharge`* | `energy` / `total_increasing` | `kWh` | Battery energy discharged |
| `daily_load_energy` / `total_load_energy`* | `energy` / `total_increasing` | `kWh` | House load consumption |
| `today_income` / `total_income`* | `monetary` / `total` | Currency | Plant revenue in configured currency |
| `co2_reduced_total`* | Diagnostic / `total_increasing` | `t` | Cumulative CO2 emissions avoided |
| `installed_capacity` | Diagnostic | `kWp` | Plant peak capacity |
| `plant_status` | Diagnostic | — | `Normal`, `Offline`, or `Fault` |
| `plant_temperature`* | Diagnostic / `temperature` | `°C` | Local plant weather (`high`, `low`, `sunrise` in attributes) |
| `last_update` | Diagnostic / `timestamp` | — | Last API or coordinator sync timestamp |
| `online` (`binary_sensor`) | `connectivity` | — | Plant online state |
| `fault` (`binary_sensor`) | `problem` | — | Plant fault state (includes `fault_count` & `faults` attributes when active) |
| `refresh_data` (`button`) | Diagnostic | — | Trigger an immediate poll |

*\*Optional metrics are only created when the plant's API response provides them, avoiding permanently `unknown` entities.*

### Child Devices (Inverter / Hybrid ESS / Battery / Meter / Comms)

Every device attached to the plant is linked via `via_device_id` (with `via_device` fallback on older HA Core releases) and exposes:

- **Dynamic Telemetry (`sensor`):** All points returned for that device's `device_type`, with automatic `device_class` / `state_class` mapping and `EntityCategory.DIAGNOSTIC` classification for technical/metadata points.
- **Status & Health:** `device_status_code` (`sensor`), `online` (`binary_sensor`, `connectivity`), and `fault` (`binary_sensor`, `problem` with matching active fault attributes when triggered).

---

## Home Assistant Energy Dashboard Setup

Go to **Settings → Dashboards → Energy** and map:

- **Solar production:** `sensor.pv_<plant>_daily_pv_energy` (or `total_pv_energy`)
- **Grid consumption:** `sensor.pv_<plant>_daily_grid_import`
- **Return to grid:** `sensor.pv_<plant>_daily_grid_export`
- **Battery systems:**
  - Energy going into the battery: `sensor.pv_<plant>_daily_battery_charge`
  - Energy coming out of the battery: `sensor.pv_<plant>_daily_battery_discharge`

---

## Preconfigured Power Flow Card Plus

If you use [Power Flow Card Plus](https://github.com/flixlix/power-flow-card-plus) from HACS, see [examples/power-flow-card-plus.yaml](examples/power-flow-card-plus.yaml) for a complete, ready-to-paste Lovelace card configuration using the split import/export and charge/discharge sensors.

---

## Architecture & Development

The standalone async client inside [`custom_components/py_sungrow_isolarcloud/api/`](custom_components/py_sungrow_isolarcloud/api/) has **zero `homeassistant` imports** (only `aiohttp` and `cryptography`), making it fast to test independently and ready to extract into a standalone PyPI package once public.

See [CONTRIBUTING.md](CONTRIBUTING.md) for local venv setup, `ruff` checks, and running the unit + Home Assistant Core test suite.
