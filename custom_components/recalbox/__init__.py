from homeassistant.core import (
    HomeAssistant,
    CoreState,
    EVENT_HOMEASSISTANT_STARTED,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.http import StaticPathConfig
from .const import DOMAIN
from .api import RecalboxAPI
from .intent import async_setup_intents
from .frontend import JSModuleRegistration
from .translations_service import RecalboxTranslator
from .custom_sentences_installer import install_sentences
from .services_installer import install_services
import os
import shutil
import logging
import hashlib

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["switch", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {"instances": {}, "global": {}})
    # Fusionner data et options pour avoir les valeurs à jour
    config = {**entry.data, **entry.options}
    host = config.get("host")

    # Ajout du service de traductions : accessible partout (genre de singleton)
    hass.data[DOMAIN]["translator"] = RecalboxTranslator(hass, DOMAIN)

    # On stocke l'API pour que button.py puisse la récupérer
    hass.data[DOMAIN]["instances"][entry.entry_id] = {
        "api": RecalboxAPI(
            host,
            api_port_os=config.get("api_port_os"),
            api_port_emulstation=config.get("api_port_emulstation"),
            udp_recalbox=config.get("udp_recalbox"),
            udp_emulstation=config.get("udp_emulstation")
        )
    }

    await async_setup_intents(hass)

    # On ajoute le switch à la liste des plateformes
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # rengistrement des services Recalbox, utilisés par la partie JS notamment
    # mais dispo aussi dans HA au global
    install_services(hass)

    # Pour raffraichir les entoités si ma config change
    entry.async_on_unload(entry.add_update_listener(update_listener))

    _LOGGER.debug(f"Entry {entry.entry_id} setup complete")
    return True



async def async_register_frontend(hass: HomeAssistant) -> None:
    """Register frontend modules after HA startup."""
    module_register = JSModuleRegistration(hass)
    await module_register.async_register()
    _LOGGER.debug(f"Front end registration complete")


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    # 1. INITIALISER le dictionnaire pour éviter le KeyError
    hass.data.setdefault(DOMAIN, {
        "instances": {}, # Contiendra les entry_id (dictionnaires)
        "global": {}     # Contiendra les flags (booléens)
    })

    # Etape préliminaire :
    # Installer les phrases Assist automatiquement
    hass.data[DOMAIN]["global"]["needs_restart"]= await hass.async_add_executor_job(
        install_sentences, hass
    )

    # enregistrement du chemin statique pour la custom card
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/recalbox",
            hass.config.path("custom_components/recalbox/frontend"),
            False
        )
    ])


    async def _setup_frontend(_event=None) -> None:
        await async_register_frontend(hass)

    # If HA is already running, register immediately
    if hass.state == CoreState.running:
        await _setup_frontend()
    else:
        # Otherwise, wait for STARTED event
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _setup_frontend)

    _LOGGER.debug(f"{DOMAIN} setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Suppression de l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN]["instances"].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Met à jour l'entrée si les options changent."""
    await hass.config_entries.async_reload(entry.entry_id)




