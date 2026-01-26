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
from .translations import RecalboxTranslator
import os
import shutil
import logging
import hashlib

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {"instances": {}, "global": {}})
    host = entry.data.get("host")

    # Traducteur : accessible partout
    translator = RecalboxTranslator(hass, DOMAIN)
    hass.data[DOMAIN]["translator"] = translator

    # On stocke l'API pour que button.py puisse la récupérer
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["instances"][entry.entry_id] = {
        "api": RecalboxAPI(host)
    }

    # On enregistre les phrases Assist
    if "intents_registered" not in hass.data[DOMAIN]:
        await async_setup_intents(hass)
        hass.data[DOMAIN]["intents_registered"] = True

    # On ajoute "button" à la liste des plateformes
    await hass.config_entries.async_forward_entry_setups(entry, ["switch"])



    # services appelés par le JS

    async def handle_shutdown(call):
        recalbox_entity = findRecalboxEntity(hass, call.data.get("entity_id"))
        if recalbox_entity: await recalbox_entity.request_shutdown()
    async def handle_reboot(call):
        recalbox_entity = findRecalboxEntity(hass, call.data.get("entity_id"))
        if recalbox_entity: await recalbox_entity.request_reboot()
    async def handle_screenshot(call):
        recalbox_entity = findRecalboxEntity(hass, call.data.get("entity_id"))
        if recalbox_entity: await recalbox_entity.request_screenshot()
    async def handle_quit_game(call):
        recalbox_entity = findRecalboxEntity(hass, call.data.get("entity_id"))
        if recalbox_entity: await recalbox_entity.request_quit_current_game()
    async def handle_launch_game(call):
        recalbox_entity = findRecalboxEntity(hass, call.data.get("entity_id"))
        game = call.data.get("game")
        console = call.data.get("console")
        if recalbox_entity:
            await recalbox_entity.search_and_launch_game_by_name(console, game)

    # Enregistrement du service recalbox.screen
    hass.services.async_register(DOMAIN, "shutdown", handle_shutdown)
    hass.services.async_register(DOMAIN, "reboot", handle_reboot)
    hass.services.async_register(DOMAIN, "screenshot", handle_screenshot)
    hass.services.async_register(DOMAIN, "quit_game", handle_quit_game)
    hass.services.async_register(DOMAIN, "launch_game", handle_launch_game)

    return True


def findRecalboxEntity(hass: HomeAssistant, entity_id: str):
    for instance in hass.data[DOMAIN]["instances"].values():
        entity = instance.get("sensor_entity")
        if entity and entity.entity_id == entity_id:
            return entity
    return None


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Register frontend modules after HA startup."""
    module_register = JSModuleRegistration(hass)
    await module_register.async_register()


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    # 1. INITIALISER le dictionnaire pour éviter le KeyError
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



def get_file_hash(filename):
    """Calcule le hash MD5 d'un fichier."""
    hash_md5 = hashlib.md5()
    try:
        with open(filename, "r", encoding="utf-8", newline=None) as f:
            for line in f:
                # On encode chaque ligne en utf-8 pour le hash
                hash_md5.update(line.encode("utf-8"))
        hashValue = hash_md5.hexdigest()
        _LOGGER.debug("The file %s hash is %s", filename, hashValue)
        return hashValue
    except FileNotFoundError:
        _LOGGER.debug("The file %s doesnt exist", filename)
        return None


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
                _LOGGER.debug("Comparing folders %s and %s ...", source_lang_path, dest_lang_path)

                # On copie chaque fichier YAML
                for file_name in os.listdir(source_lang_path):
                    if file_name.endswith(".yaml"):
                        source_file = os.path.join(source_lang_path, file_name)
                        dest_file = os.path.join(dest_lang_path, file_name)
                        _LOGGER.debug("Check if should copy %s to %s ...", source_file, dest_file)

                        # LOGIQUE PAR HASH
                        source_hash = get_file_hash(source_file)
                        dest_hash = get_file_hash(dest_file)

                        # Si le fichier destination n'existe pas ou si le contenu diffère
                        if source_hash != dest_hash:
                            _LOGGER.debug("Hashes are different")
                            try:
                                shutil.copy2(source_file, dest_file)
                                _LOGGER.info("Mise à jour phrase Assist : %s", dest_file)
                                changes_made = True
                            except Exception as e:
                                _LOGGER.error("Failed to copy file to %s: %s", dest_file, e)
                        else:
                            _LOGGER.debug("Hashes are equals, no need to copy again this file.")
        return changes_made
    except Exception as e:
        _LOGGER.error("Erreur lors de l'installation des phrases Assist : %s", e)
        return False


