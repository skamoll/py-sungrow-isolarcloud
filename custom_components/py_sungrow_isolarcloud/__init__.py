"""The Sungrow iSolarCloud integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GATEWAY_AUTO, ISolarCloudClient
from .const import CONF_GATEWAY, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import ISolarCloudCoordinator
from .entity import format_plant_device_name

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

_ISOLARCLOUD_LANG_MAP: dict[str, str] = {
    "cs": "_cs_CZ",
    "de": "_de_DE",
    "en": "_en_US",
    "es": "_es_ES",
    "fr": "_fr_FR",
    "id": "_id_ID",
    "it": "_it_IT",
    "ja": "_ja_JP",
    "ko": "_ko_KR",
    "nl": "_nl_NL",
}


def _resolve_isolarcloud_lang(language: str | None) -> str:
    """Map Home Assistant UI language to supported iSolarCloud API lang code."""
    if not language:
        return "_en_US"
    prefix = language.split("-")[0].split("_")[0].lower()
    return _ISOLARCLOUD_LANG_MAP.get(prefix, "_en_US")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sungrow iSolarCloud from a config entry."""
    session = async_get_clientsession(hass)
    client = ISolarCloudClient(
        session=session,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        gateway=entry.data.get(CONF_GATEWAY, GATEWAY_AUTO),
        lang=_resolve_isolarcloud_lang(hass.config.language),
    )
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = ISolarCloudCoordinator(
        hass=hass,
        client=client,
        scan_interval_seconds=scan_interval,
    )
    await coordinator.async_config_entry_first_refresh()

    device_reg = dr.async_get(hass)
    for ps_id, plant in (coordinator.data or {}).items():
        device_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"plant_{ps_id}")},
            manufacturer="Sungrow",
            model="Power Station",
            name=format_plant_device_name(plant.summary.ps_name, ps_id),
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
