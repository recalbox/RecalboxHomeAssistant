from homeassistant.components.image import ImageEntity
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configuration de l'entité Image."""
    api = hass.data[DOMAIN]["instances"][config_entry.entry_id]["api"]
    # On récupère l'entité switch déjà créée pour accéder à ses attributs
    switch_entity = hass.data[DOMAIN]["instances"][config_entry.entry_id]["sensor_entity"]
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
        self._attr_name = f"Recalbox Game {api.host}"
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