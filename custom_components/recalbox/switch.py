from homeassistant.components.mqtt import async_subscribe
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, CoordinatorEntity
from homeassistant.helpers import device_registry as dr
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN
from .translations_service import RecalboxTranslator
from .api import RecalboxAPI
import unicodedata
import ipaddress
import re
import homeassistant.helpers.config_validation as cv
import json
import asyncio
import logging
from collections import deque
from .recalbox_offline_watcher import prepare_ping_coordinator

_LOGGER = logging.getLogger(__name__)






async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configuration des entités Recalbox à partir de la config entry."""
    api = hass.data[DOMAIN]["instances"][config_entry.entry_id]["api"]
    coordinator = await prepare_ping_coordinator(hass, api)
    # On crée l'entité en lui passant l'objet config_entry (qui contient l'IP)
    new_entity = RecalboxEntityMQTT(hass, config_entry, api, coordinator)
    hass.data[DOMAIN]["instances"][config_entry.entry_id]["sensor_entity"] = new_entity # pour la retrouver ailleurs plus facilement
    async_add_entities([new_entity])




class RecalboxEntityMQTT(CoordinatorEntity, SwitchEntity):
    def __init__(self, hass, config_entry, api:RecalboxAPI, coordinator):
        super().__init__(coordinator)
        self.hass = hass # On récupère l'IP stockée dans la config
        self._config_entry = config_entry
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_status"
        self._attr_name = f"Recalbox {self._api.host}"
        self._attr_icon = "mdi:gamepad-variant-outline"
        self._attr_is_on = False
        self._attr_extra_state_attributes = {}
        # Attribut volatile (non persisté dans l'objet d'état standard)
        self.game = None
        self.console = None
        self.rom = None
        self.genre = None
        self.genreId = None
        self.imageUrl = None

    #@property
    #def icon(self):
    #    return "mdi:controller" if self.is_on else "mdi:controller-off"

    @property
    def is_on(self) -> bool:
        """L'entité est ON si MQTT dit ON ET que le dernier ping a réussi."""
        if not self.coordinator.data.get("is_alive_smoothed"):
            return False
        return self._attr_is_on

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"Recalbox ({self._api.host})",
            "manufacturer": "Recalbox",
            "model": f"Recalbox OS, at {self._api.host}",
            "configuration_url": f"http://{self._api.host}",
            "sw_version": self._attr_extra_state_attributes.get("recalboxVersion"),
            "hw_version": self._attr_extra_state_attributes.get("hardware")
        }

    @property
    def extra_state_attributes(self):
        """Retourne les attributs de l'état."""
        global_data = self.hass.data.get(DOMAIN, {}).get("global", {})
        return {
            **self._attr_extra_state_attributes, # Les persistants (version, hw)
            "host": self._api.host,
            "mdns_ip_address": self.coordinator.data.get("mdns_ip_address") if self.coordinator.data else None,
            "game": self.game,
            "console": self.console,
            "genre": self.genre,
            "genreId": self.genreId,
            "rom": self.rom,
            "imageUrl": self.imageUrl,
            "needs_restart": global_data.get("needs_restart", False),
            "entity_name": self._attr_name,
        }

    async def async_turn_off(self, **kwargs):
        """Action déclenchée par l'intent d'extinction ou le bouton de l'UI."""
        _LOGGER.info("Extinction de la Recalbox via le Switch")
        await self.request_shutdown()
        self.async_write_ha_state()


    async def async_turn_on(self, **kwargs):
        _LOGGER.info("Allumage de la Recalbox via le Switch -> impossible")
        translator:RecalboxTranslator = self.hass.data[DOMAIN]["translator"]
        power_off_not_implemented_message = translator.translate("errors.power_off_not_implemented_message")
        raise HomeAssistantError(power_off_not_implemented_message)


    #################################
    #             ACTIONS           #
    #################################

    async def _force_status_off(self):
        _LOGGER.debug("Forcing Recalbox status OFF (sans attendre MQTT)")
        self._attr_is_on = False
        self.reset_game_attributes()
        self.async_write_ha_state()


    async def request_shutdown(self) -> bool:
        _LOGGER.debug("Shut down Recalbox via API")
        port_api = self._api.api_port_os
        if await self._api.post_api("/api/system/shutdown", port=port_api) :
            await asyncio.sleep(5)
            await self._force_status_off()
            return True
        else:
            return False


    async def request_reboot(self) -> bool :
        _LOGGER.debug("Reboot Recalbox via API")
        port_api = self._api.api_port_os
        if await self._api.post_api("/api/system/reboot", port=port_api) :
            await asyncio.sleep(5)
            await self._force_status_off()
            return True
        else:
            return False


    async def request_screenshot(self) -> bool :
        _LOGGER.debug("Screenshot UDP, puis API si échec")
        port_api = self._api.api_port_gamesmanager
        port_udp = self._api.udp_retroarch
        # 1. Test UDP
        success = await self._api.send_udp_command(port_udp, "SCREENSHOT")
        # 2. Fallback API
        if not success:
            _LOGGER.warning(f"Screenshot UDP command not sent on port {port_udp}. Please check your Recalbox is has this port running. Will now try a screenshot via API...")
            return await self._api.post_api("/api/media/takescreenshot", port=port_api)
        else:
            _LOGGER.debug("Screenshot UDP command sent successfully to Recalbox")
            return True


    async def request_quit_current_game(self) -> bool :
        _LOGGER.debug("Quit current game via UDP")
        port_udp = self._api.udp_retroarch
        return await self._api.send_udp_command(port_udp, "QUIT")


    async def request_pause_game(self) -> bool :
        _LOGGER.debug("(Un)Pause current game via UDP")
        port_udp = self._api.udp_retroarch
        return await self._api.send_udp_command(port_udp, "PAUSE_TOGGLE")


    async def request_save_state(self) -> bool :
        _LOGGER.debug("Saving state game via UDP")
        port_udp = self._api.udp_retroarch
        return await self._api.send_udp_command(port_udp, "SAVE_STATE")


    async def request_load_state(self) -> bool :
        _LOGGER.debug("Loading state game via UDP")
        port_udp = self._api.udp_retroarch
        return await self._api.send_udp_command(port_udp, "LOAD_STATE")


    # Renvoie le texte pour Assist
    async def search_and_launch_game_by_name(self, console, game_query, lang=None) -> str :
        _LOGGER.debug(f"Try to launch game {game_query} on system {console}")
        translator:RecalboxTranslator = self.hass.data[DOMAIN]["translator"]
        port_api = self._api.api_port_gamesmanager
        port_udp = self._api.udp_recalbox
        # Récupérer la liste des roms via l'API (HTTP GET)
        try:
            roms = await self._api.get_roms(console, port_api)
            if not roms:
                return translator.translate(
                    "intent_response.no_game_on_system",
                    {"console": console},
                    lang = lang
                )
        except:
            return translator.translate("intent_response.list_roms_failed", lang=lang)


        # enlève les accents, et passe en minuscles
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
            _LOGGER.debug(f"Game found, with name {target['name']}, on system {console}. Try to launch via UDP command...")
            try:
                await self._api.send_udp_command(port_udp, f"START|{console}|{target['path']}")
                _LOGGER.debug(f"Game launched !")
                return translator.translate(
                    "intent_response.game_launched_success",
                    {"console": console, "game": target['name']},
                    lang=lang
                )
            except Exception as err:
                _LOGGER.error(f"Failed to launch game {target['name']} on {console} : {err}")
                return translator.translate(
                    "intent_response.game_launched_error",
                    {"console": console, "game": target['name']},
                    lang=lang
                )
        else:
            _LOGGER.info(f"No game matching {game_query} on {console} !")
            return translator.translate(
                "intent_response.game_not_found_on_console",
                {"console": console, "game":game_query},
                lang=lang
            )


    def reset_game_attributes(self):
        self.game = None
        self.console = None
        self.genre = None
        self.genreId = None
        self.rom = None
        self.imageUrl = None
        _LOGGER.debug("Recalbox game attributes cleaned")



    #########
    # UTILS #
    #########

    async def getRecalboxCurrentIPAddress(self) -> str :
        # si le host est déjà une adresse IP
        try:
            ipaddress.ip_address(self._api.host)
            return self._api.host # on était déjà sur une adresse IP
        except ValueError as err:
            # Ce n'est pas une IP (probablement un nom d'hôte)
            # Si on ne connait pas encore l'IP, on essaye de la récupérer
            if not self.coordinator.data.get("mdns_ip_address"):
                await self.coordinator.async_refresh()
            # on renvoie l'adresse IP si on la connait
            return self.coordinator.data.get("mdns_ip_address")

    ##########################
    #       Ecoute MQTT      #
    ##########################



    def generateImageUrlFromPath(self, path:str) -> str:
        if path and path != "-":
            imageUrl = f"http://{self._api.host}:{self._api.api_port_gamesmanager}/{path}"
            _LOGGER.debug(f"Generate image URL to {imageUrl}")
            return imageUrl
        else:
            return path


    # Callback, une fois ajouté à HASS
    # on souscrit aux files MQTT
    # pour mettre à jour la Recalbox selon
    # les messages reçus
    async def async_added_to_hass(self):
        """Appelé quand l'entité est ajoutée à HA."""
        await super().async_added_to_hass()

        # Initialisation du 1er status pour savoir si on est ON ou OFF
        await self.coordinator.async_config_entry_first_refresh()
        if self.coordinator.data.get("is_ping_success") is True:
            _LOGGER.debug("Premier ping réussi au démarrage : on met la recalbox sur ON")
            self._attr_is_on = True
            self.reset_game_attributes()
            self.async_write_ha_state()
            _LOGGER.info("Recalbox marquée comme en ligne, sans info de jeux")
        else:
            _LOGGER.debug("Premier ping échoué au démarrage : on laisse la recalbox sur OFF")

        async def message_received(msg):
            """Logique lors de la réception d'un message MQTT."""
            topic = msg.topic
            payload = msg.payload

            if topic == "recalbox/notifications/game":
                _LOGGER.debug(f"MQTT game message received ! Updating data with JSON : {payload}")
                try:
                    data = json.loads(payload)

                    # Vérification si le message est destiné à cette recalbox ou non
                    if await self.getRecalboxCurrentIPAddress() == data.get("recalboxIpAddress") :
                        _LOGGER.debug(f"This game message was sent from {self._api.host} !")
                    else :
                        _LOGGER.debug(f"Ignore : this game message was sent from {data.get("recalboxIpAddress")}, but {self._api.host} has IP {self.coordinator.data.get("mdns_ip_address")} !")
                        return

                    # 0. Mise à jour du status
                    self._attr_is_on = (data.get("status") == "ON")

                    # 1. Mise à jour des attributs internes
                    v_sw = data.get("recalboxVersion")
                    v_hw = data.get("hardware")
                    scriptVersion = data.get("scriptVersion")

                    self._attr_extra_state_attributes.update({
                        "hardware": v_hw,
                        "recalboxVersion": v_sw,
                        "scriptVersion": scriptVersion,
                    })

                    _LOGGER.debug('Updating game attributes...')

                    self.game = data.get("game")
                    self.console = data.get("console")
                    self.genre = data.get("genre")
                    self.genreId = data.get("genreId")
                    self.rom = data.get("rom")
                    self.imageUrl = data.get("imageUrl", self.generateImageUrlFromPath(data.get("imagePath")))


                    _LOGGER.debug('Updating device version/hardware...')
                    # On signale à HA que les infos du device ont pu changer
                    device_registry = dr.async_get(self.hass)
                    device = device_registry.async_get_device(
                        identifiers={(DOMAIN, self._config_entry.entry_id)}
                    )
                    if device:
                        device_registry.async_update_device(
                            device.id,
                            sw_version=v_sw,
                            hw_version=v_hw
                        )

                except json.JSONDecodeError:
                    _LOGGER.error('Cannot parse JSON')
                    pass

            # Notifier HA du changement
            self.async_write_ha_state()

        # Abonnement au topic
        await async_subscribe(self.hass, "recalbox/notifications/status", message_received)
        await async_subscribe(self.hass, "recalbox/notifications/game", message_received)
        _LOGGER.info("Subscribed to MQTT topics recalbox/notifications/status and recalbox/notifications/game")

