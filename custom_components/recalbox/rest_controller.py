from homeassistant.components.http import HomeAssistantView
from aiohttp import web
import logging
import ipaddress
from .const import DOMAIN
from .switch import RecalboxEntity
from .api import RecalboxAPI

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
                api:RecalboxAPI = instance.get("api")
                # On compare le hostname de l'URL avec celui configuré dans l'API
                if api and (self.isApiForHostname(api, hostname, data)):
                    target_entity = instance.get("sensor_entity")
                    # On met à jour l'entité directement
                    await target_entity.update_from_recalbox_json_message(data)
                    break

            if target_entity:
                return web.Response(status=200, text="OK")

            _LOGGER.warning(f"Aucune instance Recalbox trouvée pour le host : {hostname}")
            return web.Response(status=404, text="Host not found in Recalbox entities")

        except Exception as e:
            _LOGGER.error(f"Erreur lors de la réception notification Recalbox: {e}")
            return web.Response(status=400, text=str(e))


    # regarde si le message est pour cette instance :
    # - soit le hostname = celui dela recalbox
    # - soit la recalbox avait son IP renseignée et on compare alors l'IP
    def isApiForHostname(self, api:RecalboxAPI, hostname:str, jsonData) -> bool:
        try:
            # si le host est renseiné sous forme d'adresse IP
            ipaddress.ip_address(api.host)
            if api.host and api.host == jsonData.get("recalboxIpAddress") :
                _LOGGER.error(f"Instance trouvée par son IP")
                return True
            else :
                return False

        except ValueError as err:
            # Ce n'est pas une IP, mais un hostname à comparer
            hostnameApi = api.host.lower()
            hostnameRequest = hostname.lower()
            # 2. Suppression du suffixe '.local' s'il existe
            if hostnameApi.endswith('.local'):
                hostnameApi = hostnameApi[:-6] # Enlève les 6 derniers caractères
            if hostnameRequest.endswith('.local'):
                hostnameRequest = hostnameRequest[:-6]
            return hostnameApi == hostnameRequest

