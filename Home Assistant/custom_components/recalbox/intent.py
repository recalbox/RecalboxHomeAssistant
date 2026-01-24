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
        entry_id = list(intent_obj.hass.data[DOMAIN].keys())[0]
        api = intent_obj.hass.data[DOMAIN][entry_id]["api"]
        await api.send_udp_command(self._port, self._command)

        response = intent_obj.create_response()
        response.async_set_speech(self._reply)
        return response

class RecalboxScreenshotHandler(intent.IntentHandler):
    intent_type = "RecalboxCreateScreenshot"

    async def async_handle(self, intent_obj):
        hass = intent_obj.hass
        entry_id = list(hass.data[DOMAIN].keys())[0]
        api = hass.data[DOMAIN][entry_id]["api"]

        if await api.screenshot():
            text = "La capture d'écran n'a pas pu être effectuée."
        else:
            text = "La capture d'écran a été demandée à Recalbox !"

        response = intent_obj.create_response()
        response.async_set_speech(text)
        return response

class RecalboxStatusHandler(intent.IntentHandler):
    intent_type = "RecalboxGameStatus"

    async def async_handle(self, intent_obj):
        # On va lire l'état de l'entité binary_sensor pour répondre
        hass = intent_obj.hass
        entry_id = list(hass.data[DOMAIN].keys())[0]
        recalbox = hass.states.get(entry_id)

        if not recalbox:
            text = "La Recalbox n'a pas été trouvée."
        elif recalbox.state == "off":
            text = "La Recalbox est éteinte."
        else:
            game = recalbox.attributes.get("game", "-")
            if game != "-":
                console = recalbox.attributes.get("console", "")
                text = f"Tu joues à {game}, sur {console}."
            else:
                text = "La Recalbox est allumée mais aucun jeu n'est lancé."

        response = intent_obj.create_response()
        response.async_set_speech(text)
        return response


class RecalboxLaunchHandler(intent.IntentHandler):
    """Handler pour lancer un jeu."""
    intent_type = "RecalboxLaunchGame" # Doit correspondre au nom dans ton YAML

    async def async_handle(self, intent_obj):
        hass = intent_obj.hass
        # 1. Récupérer les slots (variables) de la phrase
        slots = intent_obj.slots
        game = slots.get("game", {}).get("value")
        console = slots.get("console", {}).get("value")

        # On récupère la première Recalbox configurée (ou on filtre par nom)
        entry_id = list(hass.data[DOMAIN].keys())[0]
        api = hass.data[DOMAIN][entry_id]["api"]

        # Appeler ta fonction de recherche
        result_text = await self.search_and_launch(api, console, game)

        response = intent_obj.create_response()
        response.async_set_speech(result_text)
        return response


    async def search_and_launch(self, api, console, game_query):
        # Récupérer la liste des roms via l'API (HTTP GET)
        roms = await api.get_roms(console)
        if not roms:
            return f"Aucun jeu trouvé sur la console {console}."

        def normalize_str(s):
            if not s: return ""
            # Supprime les accents et met en minuscule
            s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8')
            return s.lower().strip()

        query_simplified = normalize_str(game_query)
        pattern = query_simplified.replace(" ", ".*")

        target = None
        for r in roms:
            # On simplifie le nom du fichier/jeu pour la comparaison
            name_simplified = normalize_str(r.get('name', ''))
            # Recherche RegEx (l'ordre est respecté grâce au .*)
            if re.search(pattern, name_simplified):
                target = r
                break

        if target:
            await api.send_udp_command(1337, f"START|{console}|{target['path']}")
            return f"Le jeu {target['name']} a bien été trouvé. Lancement sur {console} !"
        else:
            return f"Le jeu {game_query} n'a pas été trouvé sur {console}."