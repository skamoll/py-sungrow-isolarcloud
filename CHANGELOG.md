# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-23

### Added
- Standalone async Python client package (`src/py_sungrow_isolarcloud/`) with zero Home Assistant dependencies.
- RSA PKCS#1 v1.5 + AES-128-ECB encrypted transport with automatic clock-skew and session-expiry recovery.
- Regional gateway auto-discovery (`eu`, `com`, `au`, `hk`, `cn`, `in`) and multi-language API support (`_en_US`, `_es_ES`, `_de_DE`, `_fr_FR`, etc.).
- Typed models (`PlantSummary`, `PlantFlow`, `DeviceSummary`, `DevicePoint`, `ActiveFault`, `PlantWeather`, `ChargingPileSummary`) with canonical `kW`/`kWh` normalization and directional power helpers.
- Unit tests (`tests/test_client.py`, `tests/test_crypto.py`, `tests/test_models.py`) and GitHub Actions CI (`ruff`, `pytest`).
