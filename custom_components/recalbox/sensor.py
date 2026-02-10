from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

# Pour afficher l'IP dans les diagnostics de la recalbox

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configuration des capteurs de diagnostic."""
    instance_data = hass.data[DOMAIN]["instances"].get(config_entry.entry_id)
    switch_entity = instance_data.get("sensor_entity") if instance_data else None
    if not switch_entity:
        return False

    game_name_entity = RecalboxCurrentGameName(switch_entity, config_entry)
    instance_data["game_name_entity"] = game_name_entity

    # On crée une liste d'entités à ajouter
    entities = [
        RecalboxDiagnosticSensor(switch_entity, config_entry, "host", "Host", "mdi:ip-network"),
        RecalboxDiagnosticSensor(switch_entity, config_entry, "only_ip_v4", "Force mDNS IP v4 only", "mdi:dns", True),
        game_name_entity,
    ]
    async_add_entities(entities)


class RecalboxDiagnosticSensor(SensorEntity):
    """Classe générique pour les diagnostics de la Recalbox."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(self, switch_entity, config_entry, key, name, icon, default=None):
        self._config_entry = config_entry
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._default = default
        self._attr_device_info = switch_entity.device_info
        # L'ID unique doit être différent pour chaque port
        self._attr_unique_id = f"{config_entry.entry_id}_config_{key}"

    @property
    def native_value(self):
        """Récupère la valeur en temps réel depuis la config ou les options."""
        # On cherche d'abord dans options (si modifié), puis data, puis valeur par défaut
        return self._config_entry.options.get(
            self._key,
            self._config_entry.data.get(self._key, self._default)
        )



# Infos du jeu

class RecalboxCurrentGameName(SensorEntity):
    """Nom du jeu."""

    def __init__(self, switch_entity, config_entry):
        self._switch = switch_entity
        self._attr_unique_id = f"{config_entry.entry_id}_current_game_name"
        self._attr_name = f"Game"
        self._attr_icon = "mdi:controller-classic"
        self._attr_device_info = switch_entity.device_info

    @property
    def native_value(self) -> str | None:
        """Retourne le nom du jeu stocké dans l'attribut du switch."""
        if self._switch.is_on and self._switch.game:
            return self._switch.game
        return None

    @property
    def available(self) -> bool:
        return self._switch.available and self._switch.is_on
