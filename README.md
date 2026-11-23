# py-sungrow-isolarcloud

[![CI](https://github.com/skamoll/py-sungrow-isolarcloud/actions/workflows/ci.yml/badge.svg)](https://github.com/skamoll/py-sungrow-isolarcloud/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Typed, asynchronous Python client library for the **Sungrow iSolarCloud** cloud API.

For the Home Assistant custom integration (HACS) built on top of this library, see [`skamoll/hass_sungrow_isolarcloud`](https://github.com/skamoll/hass_sungrow_isolarcloud).

## Features

- **Encrypted Wire Protocol:** RSA PKCS#1 v1.5 key exchange + AES-128-ECB payload encryption/decryption with automatic clock-skew (`Expired request`) and session-expiry recovery.
- **Regional Gateway Auto-Discovery:** Supports `auto` probing across `eu`, `com`, `au`, `hk`, `cn`, and `in`, or explicit regional selection.
- **Ecosystem-Wide Models:** Parses plant summaries (`PlantSummary`), energy flows & directional powers (`PlantFlow`), device inventories (`DeviceSummary`), dynamic per-device telemetry (`DevicePoint`), conditional active faults (`ActiveFault`), local plant weather (`PlantWeather`), and EV chargers (`ChargingPileSummary`).
- **Canonical Units & Locale Support:** Normalizes power (`W`/`kW`/`MW` -> `kW`), energy (`Wh`/`kWh`/`MWh` -> `kWh`), temperatures (`°C`/`°F`), and reactive/apparent power (`var`/`VA`), with iSolarCloud `lang` support (`_en_US`, `_es_ES`, `_de_DE`, `_fr_FR`, etc.).

## Installation

```bash
pip install py-sungrow-isolarcloud
```

## Quick Start

```python
import asyncio
import aiohttp
from py_sungrow_isolarcloud import GATEWAY_AUTO, ISolarCloudClient


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        client = ISolarCloudClient(
            session=session,
            username="user@example.com",
            password="your-password",
            gateway=GATEWAY_AUTO,
            lang="_en_US",
        )
        plants = await client.async_fetch_all_plants()
        for ps_id, plant in plants.items():
            print(ps_id, plant.summary.ps_name, plant.flow.pv_power)
            for dev in plant.devices:
                print(" ", dev.device_name, dev.device_model, len(dev.points), "points")


asyncio.run(main())
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest -v
```
