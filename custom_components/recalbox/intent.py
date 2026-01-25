from homeassistant.helpers import intent
import unicodedata
import re
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_intents(hass):
    """Enregistre les handlers d'intentions seulement s'ils n'existent pas."""

    # Liste des intentions de votre intégration
    intents_to_register = [
        RecalboxLaunchHandler(),
        RecalboxStatusHandler(),
        RecalboxActionHandler("RecalboxStopGame", 55355, "QUIT", "intent_response.quit_game_requested"),
        RecalboxActionHandler("RecalboxPauseGame", 55355, "PAUSE_TOGGLE", "intent_response.pause_game_requested"),
        RecalboxScreenshotHandler()
    ]

    for handler in intents_to_register:
        # On vérifie si l'intent_type est déjà enregistré
        if handler.intent_type not in intent.async_get(hass):
            intent.async_register(hass, handler)


class RecalboxActionHandler(intent.IntentHandler):
    def __init__(self, intent_type, port, command, responseKey):
        self.intent_type = intent_type
        self._port = port
        self._command = command
        self._responseKey = responseKey

    async def async_handle(self, intent_obj):
        instances = intent_obj.hass.data[DOMAIN].get("instances", {})
        entry_id = list(instances.keys())[0]
        api = instances[entry_id]["api"]
        await api.send_udp_command(self._port, self._command)
        translator = intent_obj.hass.data[DOMAIN]["translator"]

        response = intent_obj.create_response()
        response.async_set_speech(translator.translate(self._responseKey, lang=intent_obj.language))
        return response

class RecalboxScreenshotHandler(intent.IntentHandler):
    intent_type = "RecalboxCreateScreenshot"

    async def async_handle(self, intent_obj):
        hass = intent_obj.hass
        instances = hass.data[DOMAIN].get("instances", {})
        entry_id = list(instances.keys())[0]
        recalbox = instances[entry_id].get("sensor_entity")
        translator = hass.data[DOMAIN]["translator"]

        if await recalbox.request_screenshot():
            text = translator.translate("intent_response.screenshot_success", lang=intent_obj.language)
        else:
            text = translator.translate("intent_response.screenshot_fail", lang=intent_obj.language)

        response = intent_obj.create_response()
        response.async_set_speech(text)
        return response

class RecalboxStatusHandler(intent.IntentHandler):
    intent_type = "RecalboxGameStatus"

    async def async_handle(self, intent_obj):
        # On va lire l'état de l'entité binary_sensor pour répondre
        hass = intent_obj.hass
        instances = hass.data[DOMAIN].get("instances", {})
        entry_id = list(instances.keys())[0]
        recalboxEntity = instances[entry_id].get("sensor_entity")
        recalbox = hass.states.get(recalboxEntity.entity_id)
        translator = hass.data[DOMAIN]["translator"]

        if not recalbox:
            text = translator.translate("intent_response.recalbox_not_found", lang=intent_obj.language)
        elif recalbox.state == "off":
            text = translator.translate("intent_response.recalbox_offline", lang=intent_obj.language)
        else:
            game = recalbox.attributes.get("game", "-")
            if game is not None and game != "None" and game != "-" :
                console = recalbox.attributes.get("console", "")
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


class RecalboxLaunchHandler(intent.IntentHandler):
    """Handler pour lancer un jeu."""
    intent_type = "RecalboxLaunchGame" # Doit correspondre au nom dans ton YAML

    async def async_handle(self, intent_obj):
        hass = intent_obj.hass
        instances = hass.data[DOMAIN].get("instances", {})
        entry_id = list(instances.keys())[0]
        recalbox = instances[entry_id].get("sensor_entity")

        # 1. Récupérer les slots (variables) de la phrase
        slots = intent_obj.slots
        game = slots.get("game", {}).get("value")
        console = slots.get("console", {}).get("value")

        # Appeler la fonction de recherche
        result_text = await recalbox.search_and_launch_game_by_name(console, game, lang=intent_obj.language)

        response = intent_obj.create_response()
        response.async_set_speech(result_text)
        return response
