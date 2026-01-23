from homeassistant.helpers import intent
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
        RecalboxActionHandler("RecalboxCreateScreenshot", 55355, "SCREENSHOT", "Deamnde de capture d'écran effectuée")
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

class RecalboxStatusHandler(intent.IntentHandler):
    intent_type = "RecalboxGameStatus"

    async def async_handle(self, intent_obj):
        # On va lire l'état de l'entité binary_sensor pour répondre
        states = intent_obj.hass.states.async_all(DOMAIN)
        recalbox = states[0] if states else None

        if not recalbox or recalbox.state == "off":
            text = "La Recalbox est éteinte."
        else:
            game = recalbox.attributes.get("game", "inconnu")
            text = f"Tu joues à {game}." if game != "-" else "La Recalbox est allumée mais aucun jeu n'est lancé."

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
        # 1. Récupérer la liste des roms via l'API (HTTP GET)
        roms = await api.get_roms(console)

        # 2. Ta logique de filtrage (plus simple qu'en Jinja2 !)
        pattern = game_query.replace(" ", ".*")
        target = next((r for r in roms if re.search(pattern, r['name'], re.I)), None)

        if target:
            # 3. Lancement UDP
            await api.send_udp_command(1337, f"START|{console}|{target['path']}")
            return f"Je lance {target['name']} sur {console} !"
        return f"Jeu {game_query} non trouvé sur {console}."