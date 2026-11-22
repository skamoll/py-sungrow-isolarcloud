# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial `py_sungrow_isolarcloud` Home Assistant custom integration (`ConfigFlow`, `OptionsFlow`, `DataUpdateCoordinator`).
- Async iSolarCloud API client with regional gateway discovery (`auto` + `eu`, `com`, `au`, `hk`, `cn`, `in`).
- Curated plant-level power flow, Energy Dashboard (`kWh`, `TOTAL_INCREASING`), battery SoC, and child-device connectivity entities.
- English and Spanish translations.
- CI workflows (`ruff`, `pytest`, `hassfest`, `hacs`).
