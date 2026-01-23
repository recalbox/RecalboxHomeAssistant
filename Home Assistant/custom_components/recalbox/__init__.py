from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .api import RecalboxAPI
from homeassistant.components.http import StaticPathConfig
from .intent import async_setup_intents # Pour charger les phrases Assist

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data.get("host")

    # On stocke l'API pour que button.py puisse la récupérer
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": RecalboxAPI(host)
    }

    # On ajoute "button" à la liste des plateformes
    await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor", "button"])

    # On enregistre les phrases Assist (S'assurer que ce n'est fait qu'une fois)
    if "intents_registered" not in hass.data[DOMAIN]:
        await async_setup_intents(hass)
        hass.data[DOMAIN]["intents_registered"] = True

    # enregistrement du chemin statique
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/recalbox",
            hass.config.path("custom_components/recalbox/www"),
            False
        )
    ])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Suppression de l'intégration."""
    return await hass.config_entries.async_unload_platforms(entry, ["binary_sensor"])


