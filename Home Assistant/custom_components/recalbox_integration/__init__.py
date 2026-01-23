from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .api import RecalboxAPI
from .intent import async_setup_intents # Pour charger tes phrases Assist

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data.get("host")

    # On stocke l'API pour que button.py puisse la récupérer
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": RecalboxAPI(host)
    }

    # On ajoute "button" à la liste des plateformes
    await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor", "button"])

    # On enregistre les phrases Assist
    await async_setup_intents(hass)

    # Enregistre le dossier www pour qu'il soit accessible via /recalbox/
    hass.http.register_static_path(
        "/recalbox",
        hass.config.path("custom_components/recalbox/www"),
        cache_headers=False
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Suppression de l'intégration."""
    return await hass.config_entries.async_unload_platforms(entry, ["binary_sensor"])


