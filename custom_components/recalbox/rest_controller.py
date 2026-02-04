from homeassistant.components.http import HomeAssistantView
from aiohttp import web
import logging
from .const import DOMAIN
from .switch import RecalboxEntity

_LOGGER = logging.getLogger(__name__)

class RecalboxRestController(HomeAssistantView):
    """Endpoint pour recevoir les notifications de la Recalbox."""
    url = "/api/recalbox/notification/{hostname}"
    name = "api:recalbox:notification"
    requires_auth = False # Permet à la Recalbox d'envoyer sans token complexe

    def __init__(self, hass):
        self.hass = hass
        _LOGGER.debug(f"Create an API endpoint to {self.url}, to received the Recalbox messages")


    async def post(self, request, hostname):
        """Reçoit le JSON et l'aiguille vers la bonne instance."""
        try:
            data = await request.json()
            _LOGGER.debug(f"Notification reçue pour le host {hostname}: {data}")

            # On cherche l'instance correspondante
            instances = self.hass.data.get(DOMAIN, {}).get("instances", {})
            target_entity:RecalboxEntity = None

            for entry_id, instance in instances.items():
                api = instance.get("api")
                # On compare le hostname de l'URL avec celui configuré dans l'API
                if api and api.host.lower() == hostname.lower():
                    target_entity = instance.get("sensor_entity")
                    break

            if target_entity:
                # On met à jour l'entité directement
                await target_entity.update_from_recalbox_json_message(data)
                return web.Response(status=200, text="OK")

            _LOGGER.warning(f"Aucune instance Recalbox trouvée pour le host : {hostname}")
            return web.Response(status=404, text="Host not found in Recalbox entities")

        except Exception as e:
            _LOGGER.error(f"Erreur lors de la réception notification Recalbox: {e}")
            return web.Response(status=400, text=str(e))