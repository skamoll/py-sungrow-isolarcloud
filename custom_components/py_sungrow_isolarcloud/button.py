"""Button platform for Sungrow iSolarCloud."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ISolarCloudCoordinator
from .entity import ISolarCloudPlantEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sungrow iSolarCloud buttons from a config entry."""
    coordinator: ISolarCloudCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [ISolarCloudRefreshButton(coordinator, ps_id) for ps_id in (coordinator.data or {})]
    async_add_entities(entities)


class ISolarCloudRefreshButton(ISolarCloudPlantEntity, ButtonEntity):
    """Button to trigger an immediate iSolarCloud data refresh."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "refresh"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: ISolarCloudCoordinator, ps_id: str) -> None:
        super().__init__(coordinator, ps_id, "refresh")

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_request_refresh()
