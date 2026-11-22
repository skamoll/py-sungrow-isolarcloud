# Sungrow iSolarCloud for Home Assistant

[![CI](https://github.com/skamoll/py-sungrow-isolarcloud/actions/workflows/ci.yml/badge.svg)](https://github.com/skamoll/py-sungrow-isolarcloud/actions/workflows/ci.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Native Home Assistant integration (`py_sungrow_isolarcloud`) for monitoring **Sungrow iSolarCloud** solar plants, batteries, and inverters.

## Features

- **Native UI Setup (`ConfigFlow` & `OptionsFlow`):** Configure credentials, regional gateway (`auto` or `eu`, `com`, `au`, `hk`, `cn`, `in`), and polling interval (`30s`–`600s`, default `120s`) directly in Home Assistant.
- **Clean Device & Entity Hierarchy:** One Plant device (`Power Station`) with child Inverter / Battery / Meter devices linked via `via_device`, using `has_entity_name` and stable `unique_id`s.
- **Energy Dashboard Ready:** Daily and total `kWh` sensors (`TOTAL_INCREASING`, `device_class: energy`) for PV generation, grid import/export, battery charge/discharge, and home consumption.
- **Canonical Units:** Normalizes units (`°C`, `°F`, `var`, `W/m²`, `kW`, `kWh`) for long-term statistics.
- **Bilingual UI:** English and Spanish translations included.

## Installation

### HACS (Custom Repository)

1. Open **HACS** in Home Assistant → **Integrations** → **⋮** → **Custom repositories**.
2. Add `https://github.com/skamoll/py-sungrow-isolarcloud` with category **Integration**.
3. Search for **Sungrow iSolarCloud** and install it.
4. Restart Home Assistant.

### Manual Installation

1. Copy `custom_components/py_sungrow_isolarcloud` into your Home Assistant `<config>/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Sungrow iSolarCloud**.
3. Select your regional gateway (or leave **Auto**) and enter your iSolarCloud email and password.

## Entities Created

### Plant Device
- **Power (W/kW):** PV power, Load power, Grid power, Battery power
- **Battery:** State of Charge (`%`)
- **Energy (kWh, `TOTAL_INCREASING`):** Daily & Total PV energy, Grid import/export, Battery charge/discharge, Home consumption
- **Diagnostics & Connectivity:** Installed capacity (`kWp`), Last update timestamp, Online (`binary_sensor`)

### Child Devices (Inverter / Battery / Meter)
- **Connectivity:** Online (`binary_sensor`)
- **Diagnostics:** Status code

## Development & Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, linting, and testing instructions.
