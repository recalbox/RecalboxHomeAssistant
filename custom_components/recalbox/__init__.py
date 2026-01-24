from homeassistant.core import (
    HomeAssistant,
    CoreState,
    EVENT_HOMEASSISTANT_STARTED,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.http import StaticPathConfig
from .const import DOMAIN
from .api import RecalboxAPI
from .intent import async_setup_intents # Pour charger les phrases Assist
from .frontend import JSModuleRegistration
import os
import shutil
import logging







async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {"instances": {}, "global": {}})
    host = entry.data.get("host")

    # On stocke l'API pour que button.py puisse la récupérer
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["instances"][entry.entry_id] = {
        "api": RecalboxAPI(host)
    }

    # On enregistre les phrases Assist (S'assurer que ce n'est fait qu'une fois)
    if "intents_registered" not in hass.data[DOMAIN]:
        await async_setup_intents(hass)
        hass.data[DOMAIN]["intents_registered"] = True

    # On ajoute "button" à la liste des plateformes
    await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor", "button"])

    return True






async def async_register_frontend(hass: HomeAssistant) -> None:
    """Register frontend modules after HA startup."""
    module_register = JSModuleRegistration(hass)
    await module_register.async_register()


async def async_setup(hass: HomeAssistant, config: dict) -> bool:# 1. INITIALISER le dictionnaire pour éviter le KeyError
    hass.data.setdefault(DOMAIN, {
        "instances": {}, # Contiendra les entry_id (dictionnaires)
        "global": {}     # Contiendra les flags (booléens)
    })

    # Etape préliminaire :
    # Installer les phrases Assist automatiquement
    hass.data[DOMAIN]["global"]["needs_restart"] = await async_install_sentences(hass)

    # enregistrement du chemin statique
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

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Suppression de l'intégration."""
    return await hass.config_entries.async_unload_platforms(entry, ["binary_sensor"])






# Tools : installer les custom_sentences

_LOGGER = logging.getLogger(__name__)

async def async_install_sentences(hass: HomeAssistant) -> bool :
    """Copie récursivement les sentences du composant vers le dossier système de HA."""
    # Chemin source : /config/custom_components/recalbox/sentences
    source_root = hass.config.path("custom_components", DOMAIN, "custom_sentences")
    # Chemin destination : /config/custom_sentences
    dest_root = hass.config.path("custom_sentences")
    changes_made = False

    if not os.path.exists(source_root):
        _LOGGER.warning("Dossier source des sentences introuvable : %s", source_root)
        return False

    try:
        # On parcourt les dossiers de langues (fr, en, es...)
        for lang_dir in os.listdir(source_root):
            source_lang_path = os.path.join(source_root, lang_dir)

            if os.path.isdir(source_lang_path):
                dest_lang_path = os.path.join(dest_root, lang_dir)
                os.makedirs(dest_lang_path, exist_ok=True)

                # On copie chaque fichier YAML
                for file_name in os.listdir(source_lang_path):
                    if file_name.endswith(".yaml"):
                        source_file = os.path.join(source_lang_path, file_name)
                        dest_file = os.path.join(dest_lang_path, file_name)

                        # STRATÉGIE DE COPIE :
                        # On copie si le fichier n'existe pas
                        # OU si la date de modification est différente (mise à jour du code)
                        if not os.path.exists(dest_file) or (os.path.getmtime(source_file) != os.path.getmtime(dest_file)):
                            try:
                                shutil.copy2(source_file, dest_file)
                                _LOGGER.info("Mise à jour phrase Assist : %s/%s", lang_dir, file_name)
                                changes_made = True
                            except Exception as e:
                                _LOGGER.error("Erreur copie sentence %s: %s", file_name, e)
        return changes_made
    except Exception as e:
        _LOGGER.error("Erreur lors de l'installation des phrases Assist : %s", e)
        return False


