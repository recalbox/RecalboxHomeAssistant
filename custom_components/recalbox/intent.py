from homeassistant.helpers import intent
from homeassistant.core import HomeAssistant, State
import unicodedata
import re
from .const import DOMAIN
from .translations_service import RecalboxTranslator
from .switch import RecalboxEntityMQTT
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_intents(hass):
    """Enregistre les handlers d'intentions seulement s'ils n'existent pas."""

    if "intents_registered" in hass.data[DOMAIN]:
        _LOGGER.debug("The intents are already registered. Skip re-register.")
        return

    # Liste des intentions de votre intégration
    intents_to_register = [
        RecalboxLaunchHandler(),
        RecalboxStatusHandler(),
        RecalboxQuitGameHandler(),
        RecalboxPauseGameHandler(),
        RecalboxScreenshotHandler(),
        RecalboxLoadStateHandler(),
        RecalboxSaveStateHandler(),
    ]

    for handler in intents_to_register:
        # On vérifie si l'intent_type est déjà enregistré
        if handler.intent_type not in intent.async_get(hass):
            intent.async_register(hass, handler)
            _LOGGER.info(f"Registered {handler.intent_type} intent handler")

    hass.data[DOMAIN]["intents_registered"] = True


# --- TOOLS ----

# Va chercher la Recalbox par défaut.
# - soit l'instance est spécifiée dans l'intent
# - soit non, et on prend la première qu'on trouve allumée
# - soit on prend la première qu'on trouve si toutes sont éteintes
def find_recalbox_entity(hass: HomeAssistant, intent_obj:intent.Intent) -> RecalboxEntityMQTT:
    instances = hass.data[DOMAIN].get("instances", {})
    if not instances:
        return None

    # Extraction des entités réelles (RecalboxEntityMQTT)
    all_entities = [instance.get("sensor_entity") for instance in instances.values() if instance.get("sensor_entity")]

    if not all_entities:
        _LOGGER.warning("No RecalboxEntityMQTT found")
        return None

    # Prio 1 :
    # Recherche par nom spécifique, si présent dans l'Intent
    slots = intent_obj.slots
    recalbox_instance_name = slots.get("instance", {}).get("value")

    if recalbox_instance_name:
        target_slug = slugify(str(recalbox_instance_name))
        for entity in all_entities:
            # On compare avec le nom de l'entité ou un attribut de nom
            if slugify(entity.name) == target_slug:
                _LOGGER.info(f"Found Recalbox target by its name {entity.name}")
                return entity

    # Prio 2 :
    # Si on n'a pas trouvé un RecalboxEntityMQTT par nom,
    # on cherche la première qui est "ON"
    for entity in all_entities:
        state = hass.states.get(entity.entity_id)
        if state and state.state == "on":
            _LOGGER.info(f"Found a Recalbox that is ON : {entity.name}")
            return entity

    # Sinon, on prend juste la première de la liste par défaut
    _LOGGER.info(f"Using the first Recalbox by default.")
    return all_entities[0]

def find_recalbox_states(hass: HomeAssistant, intent_obj:intent.Intent) -> State:
    recalboxEntity:RecalboxEntityMQTT = find_recalbox_entity(hass, intent_obj)
    return hass.states.get(recalboxEntity.entity_id)

def get_translator(hass: HomeAssistant) -> RecalboxTranslator:
    return hass.data[DOMAIN]["translator"]



# ---- Intent Handlers -----



#class RecalboxOtherUDPActionHandler(intent.IntentHandler):
#    def __init__(self, intent_type, port, command, responseKey):
#        self.intent_type = intent_type
#        self._port = port
#        self._command = command
#        self._responseKey = responseKey
#
#    async def async_handle(self, intent_obj):
#        instances = intent_obj.hass.data[DOMAIN].get("instances", {})
#        entry_id = list(instances.keys())[0]
#        api = instances[entry_id]["api"]
#        await api.send_udp_command(self._port, self._command)
#        translator = intent_obj.hass.data[DOMAIN]["translator"]
#
#        response = intent_obj.create_response()
#        response.async_set_speech(translator.translate(self._responseKey, lang=intent_obj.language))
#        return response



# ----- Handlers basiques : trouvent l'entité et appellent une fonction --------

class RecalboxScreenshotHandler(intent.IntentHandler):
    intent_type = "RecalboxCreateScreenshot"

    async def async_handle(self, intent_obj):
        hass = intent_obj.hass
        recalbox:RecalboxEntityMQTT = find_recalbox_entity(hass, intent_obj)
        translator:RecalboxTranslator = get_translator(hass)

        if await recalbox.request_screenshot():
            text = translator.translate("intent_response.screenshot_success", lang=intent_obj.language)
        else:
            text = translator.translate("intent_response.screenshot_fail", lang=intent_obj.language)

        response = intent_obj.create_response()
        response.async_set_speech(text)
        return response



class RecalboxQuitGameHandler(intent.IntentHandler):
    intent_type = "RecalboxStopGame"

    async def async_handle(self, intent_obj):
        hass = intent_obj.hass
        recalbox:RecalboxEntityMQTT = find_recalbox_entity(hass, intent_obj)
        translator:RecalboxTranslator = get_translator(hass)

        if await recalbox.request_quit_current_game():
            text = translator.translate("intent_response.quit_game_requested", lang=intent_obj.language)
        else:
            text = translator.translate("intent_response.quit_game_failed", lang=intent_obj.language)

        response = intent_obj.create_response()
        response.async_set_speech(text)
        return response



class RecalboxPauseGameHandler(intent.IntentHandler):
    intent_type = "RecalboxPauseGame"

    async def async_handle(self, intent_obj):
        hass = intent_obj.hass
        recalbox:RecalboxEntityMQTT = find_recalbox_entity(hass, intent_obj)
        translator:RecalboxTranslator = get_translator(hass)

        if await recalbox.request_pause_game():
            text = translator.translate("intent_response.pause_game_requested", lang=intent_obj.language)
        else:
            text = translator.translate("intent_response.pause_game_failed", lang=intent_obj.language)

        response = intent_obj.create_response()
        response.async_set_speech(text)
        return response


class RecalboxSaveStateHandler(intent.IntentHandler):
    intent_type = "RecalboxSaveState"

    async def async_handle(self, intent_obj):
        hass = intent_obj.hass
        recalbox:RecalboxEntityMQTT = find_recalbox_entity(hass, intent_obj)
        translator:RecalboxTranslator = get_translator(hass)

        if await recalbox.request_save_state():
            text = translator.translate("intent_response.save_state_requested", lang=intent_obj.language)
        else:
            text = translator.translate("intent_response.save_state_failed", lang=intent_obj.language)

        response = intent_obj.create_response()
        response.async_set_speech(text)
        return response


class RecalboxLoadStateHandler(intent.IntentHandler):
    intent_type = "RecalboxLoadState"

    async def async_handle(self, intent_obj):
        hass = intent_obj.hass
        recalbox:RecalboxEntityMQTT = find_recalbox_entity(hass, intent_obj)
        translator:RecalboxTranslator = get_translator(hass)

        if await recalbox.request_load_state():
            text = translator.translate("intent_response.load_state_requested", lang=intent_obj.language)
        else:
            text = translator.translate("intent_response.load_state_failed", lang=intent_obj.language)

        response = intent_obj.create_response()
        response.async_set_speech(text)
        return response


# ---- handler qui lit plus de paramètres ------

class RecalboxLaunchHandler(intent.IntentHandler):
    """Handler pour lancer un jeu."""
    intent_type = "RecalboxLaunchGame" # Doit correspondre au nom dans ton YAML

    async def async_handle(self, intent_obj:intent.Intent):
        hass = intent_obj.hass
        # 1. Récupérer les slots (variables) de la phrase
        slots = intent_obj.slots
        game = slots.get("game", {}).get("value")
        console = slots.get("console", {}).get("value")
        # recalboxEntityId = slots.get("recalboxEntityId", {}).get("value")

        recalbox = find_recalbox_entity(hass, intent_obj)

        # Appeler la fonction de recherche
        result_text = await recalbox.search_and_launch_game_by_name(console, game, lang=intent_obj.language)

        response = intent_obj.create_response()
        response.async_set_speech(result_text)
        return response



# -------- Handler qui a se base sur le state, contrairement aux autres -------------

class RecalboxStatusHandler(intent.IntentHandler):
    intent_type = "RecalboxGameStatus"

    async def async_handle(self, intent_obj):
        # On va lire l'état de l'entité binary_sensor pour répondre
        hass = intent_obj.hass
        recalboxState:State = find_recalbox_states(hass, intent_obj)
        translator:RecalboxTranslator = get_translator(hass)

        if not recalboxState:
            text = translator.translate("intent_response.recalbox_not_found", lang=intent_obj.language)
        elif recalboxState.state == "off":
            text = translator.translate("intent_response.recalbox_offline", lang=intent_obj.language)
        else:
            game = recalboxState.attributes.get("game", "-")
            if game is not None and game != "None" and game != "-" :
                console = recalboxState.attributes.get("console", "")
                text = translator.translate(
                    "intent_response.game_status_playing",
                    {"game": game, "console": console},
                    lang=intent_obj.language
                )
            else:
                text = translator.translate("intent_response.game_status_none", lang=intent_obj.language)

        response = intent_obj.create_response()
        response.async_set_speech(text)
        return response
