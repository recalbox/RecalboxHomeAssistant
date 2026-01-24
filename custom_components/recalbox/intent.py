from homeassistant.helpers import intent
import unicodedata
import re
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN

async def async_setup_intents(hass):
    """Enregistre les handlers d'intentions seulement s'ils n'existent pas."""

    # Liste des intentions de votre intégration
    intents_to_register = [
        RecalboxLaunchHandler(),
        RecalboxStatusHandler(),
        RecalboxActionHandler("RecalboxStopGame", 55355, "QUIT", "Retour au menu"),
        RecalboxActionHandler("RecalboxPauseGame", 55355, "PAUSE_TOGGLE", "Pause demandée"),
        RecalboxScreenshotHandler()
    ]

    for handler in intents_to_register:
        # On vérifie si l'intent_type est déjà enregistré
        if handler.intent_type not in intent.async_get(hass):
            intent.async_register(hass, handler)


class RecalboxActionHandler(intent.IntentHandler):
    def __init__(self, intent_type, port, command, reply):
        self.intent_type = intent_type
        self._port = port
        self._command = command
        self._reply = reply

    async def async_handle(self, intent_obj):
        instances = intent_obj.hass.data[DOMAIN].get("instances", {})
        entry_id = list(instances.keys())[0]
        api = instances[entry_id]["api"]
        await api.send_udp_command(self._port, self._command)

        response = intent_obj.create_response()
        response.async_set_speech(self._reply)
        return response

class RecalboxScreenshotHandler(intent.IntentHandler):
    intent_type = "RecalboxCreateScreenshot"

    async def async_handle(self, intent_obj):
        hass = intent_obj.hass
        instances = hass.data[DOMAIN].get("instances", {})
        entry_id = list(instances.keys())[0]
        recalbox = instances[entry_id].get("sensor_entity")

        if await recalbox.request_screenshot():
            text = "La capture d'écran a été faite, et stockée dans le dossier screenshots de Recalbox !"
        else:
            text = "La capture d'écran n'a pas pu être effectuée."

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

        if not recalbox:
            text = "La Recalbox n'a pas été trouvée."
        elif recalbox.state == "off":
            text = "La Recalbox est éteinte."
        else:
            game = recalbox.attributes.get("game", "-")
            if game is not None and game != "None" and game != "-" :
                console = recalbox.attributes.get("console", "")
                text = f"Tu joues à {game}, sur {console}."
            else:
                text = "La Recalbox est allumée, mais aucun jeu n'est lancé."

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
        result_text = await recalbox.search_and_launch_game_by_name(console, game)

        response = intent_obj.create_response()
        response.async_set_speech(result_text)
        return response
