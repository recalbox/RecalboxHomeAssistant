from homeassistant.components.image import ImageEntity
from .const import DOMAIN
import logging


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configuration de l'entité Image."""
    api = hass.data[DOMAIN]["instances"][config_entry.entry_id]["api"]
    # On récupère l'entité switch déjà créée pour accéder à ses attributs
    instance_data = hass.data[DOMAIN]["instances"].get(config_entry.entry_id)
    switch_entity = instance_data.get("sensor_entity") if instance_data else None
    if not switch_entity:
        _LOGGER.error("Le switch Recalbox n'est pas prêt. Impossible de charger l'image.")
        return False

    image_entity = RecalboxCurrentGameImage(hass, switch_entity, config_entry, api)
    hass.data[DOMAIN]["instances"][config_entry.entry_id]["image_entity"] = image_entity
    async_add_entities([image_entity])

class RecalboxCurrentGameImage(ImageEntity):
    """Représentation de l'image de la jaquette Recalbox."""

    def __init__(self, hass, switch_entity, config_entry, api):
        super().__init__(hass)
        self._switch = switch_entity
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_game_image"
        self._attr_name = f"Gamepic"
        self._attr_device_info = switch_entity.device_info

    @property
    def image_url(self) -> str | None:
        """Retourne l'URL de l'image stockée dans le switch."""
        # On vérifie si le switch est ON et si une URL est disponible
        if self._switch.is_on and self._switch.imageUrl:
            return self._switch.imageUrl
        return None

    @property
    def available(self) -> bool:
        """L'entité image est disponible si le switch est ON."""
        return self._switch.available and self._switch.is_on