from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    entities = [
        RecalboxPortNumber(hass, config_entry, "api_port_os", "Port API OS", "mdi:api", 80),
        RecalboxPortNumber(hass, config_entry, "api_port_gamesmanager", "Port API Games", "mdi:api", 81),
        RecalboxPortNumber(hass, config_entry, "udp_recalbox", "Port UDP Recalbox", "mdi:remote", 1337),
        RecalboxPortNumber(hass, config_entry, "udp_retroarch", "Port UDP RetroArch", "mdi:remote", 55355),
        RecalboxPortNumber(hass, config_entry, "api_port_kodi", "Port API Kodi", "mdi:kodi", 8081),
    ]
    async_add_entities(entities)

class RecalboxPortNumber(NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_native_min_value = 1
    _attr_native_max_value = 65535
    _attr_native_step = 1

    def __init__(self, hass, config_entry, key, name, icon, defaultValue):
        self.hass = hass
        self._config_entry = config_entry
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{config_entry.entry_id}_port_{key}"
        self._default = defaultValue

    @property
    def native_value(self):
        return self._config_entry.options.get(self._key, self._default)

    async def async_set_native_value(self, value: float):
        new_options = dict(self._config_entry.options)
        new_options[self._key] = int(value)
        self.hass.config_entries.async_update_entry(self._config_entry, options=new_options)

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._config_entry.entry_id)}}