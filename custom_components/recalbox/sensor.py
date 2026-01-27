from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

# Pour afficher l'IP dans les diagnostics de la recalbox

async def async_setup_entry(hass, config_entry, async_add_entities):
    host = config_entry.data.get("host")
    async_add_entities([RecalboxDiagnosticIP(config_entry, host)])

class RecalboxDiagnosticIP(SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:ip-network"
    _attr_has_entity_name = True

    def __init__(self, config_entry, host):
        self._config_entry = config_entry
        self._attr_name = "Host"
        self._attr_unique_id = f"{config_entry.entry_id}_ip_address"
        self._attr_native_value = host

    @property
    def device_info(self):
        # Rattachement au même appareil que le switch
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
        }