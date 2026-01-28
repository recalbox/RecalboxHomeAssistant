from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

# Pour afficher l'IP dans les diagnostics de la recalbox

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configuration des capteurs de diagnostic."""
    # On crée une liste d'entités à ajouter
    entities = [
        RecalboxDiagnosticSensor(config_entry, "host", "Host", "mdi:ip-network"),
        RecalboxDiagnosticSensor(config_entry, "api_port_os", "Port API OS", "mdi:api", 80),
        RecalboxDiagnosticSensor(config_entry, "api_port_webmanager", "Port API WebManager", "mdi:api", 81),
        RecalboxDiagnosticSensor(config_entry, "udp_recalbox", "Port UDP Recalbox", "mdi:remote", 1337),
        RecalboxDiagnosticSensor(config_entry, "udp_emulstation", "Port UDP EmulationStation", "mdi:remote", 55355),
    ]
    async_add_entities(entities)


class RecalboxDiagnosticSensor(SensorEntity):
    """Classe générique pour les diagnostics de la Recalbox."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(self, config_entry, key, name, icon, default=None):
        self._config_entry = config_entry
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._default = default
        # L'ID unique doit être différent pour chaque port
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"

    @property
    def native_value(self):
        """Récupère la valeur en temps réel depuis la config ou les options."""
        # On cherche d'abord dans options (si modifié), puis data, puis valeur par défaut
        return self._config_entry.options.get(
            self._key,
            self._config_entry.data.get(self._key, self._default)
        )

    @property
    def device_info(self):
        """Rattachement à l'appareil central Recalbox."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
        }