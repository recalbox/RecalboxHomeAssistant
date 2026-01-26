import logging
from homeassistant.core import HomeAssistant
from .const import DOMAIN

# by Aurélien Tomassini - ooree23
# Tools : installer les services


_LOGGER = logging.getLogger(__name__)


def findRecalboxEntity(hass: HomeAssistant, entity_id: str):
    for instance in hass.data[DOMAIN]["instances"].values():
        entity = instance.get("sensor_entity")
        if entity and entity.entity_id == entity_id:
            return entity
    return None

def install_services(hass: HomeAssistant):
    _LOGGER.debug("Install Recalbox services...")

    # handlers
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

    # Mapping des noms de services vers leurs fonctions de rappel
    RECALBOX_SERVICES = {
        "shutdown": handle_shutdown,
        "reboot": handle_reboot,
        "screenshot": handle_screenshot,
        "quit_game": handle_quit_game,
        "launch_game": handle_launch_game,
    }

    for service_name, handler in RECALBOX_SERVICES.items():
        hass.services.async_register(DOMAIN, service_name, handler)
        _LOGGER.info(f"Registered {service_name} Recalbox service")