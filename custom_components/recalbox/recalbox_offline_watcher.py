import logging
import asyncio
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, CoordinatorEntity
from collections import deque
from .api import RecalboxAPI

_LOGGER = logging.getLogger(__name__)

############################################
# Coordinateur                             #
# Pour vérifier toutes les 60 sec          #
# Si la Recalbox est encore ON par un ping #
############################################

frequency = timedelta(seconds=30)
maxHistoryLength = 4

async def prepare_ping_coordinator(hass, api:RecalboxAPI) -> DataUpdateCoordinator:
    _LOGGER.info(f"Prepare Recalbox watcher (coordinator). It will Ping the Recalbox {api.host} every {frequency}. When Pings reaches {maxHistoryLength} fails, it will automatically consider this Recalbox offline")
    # On garde un historique des 3 derniers résultats de Ping.
    # Si on a un seul ping qui échoue, ça évite de mettre la recalbox offline pour rien.
    # Avec un ping toutes les 30sec, on la passe en offline après 2 minutes comme ça.
    history = deque([], maxlen=maxHistoryLength)
    # 1. On définit le coordinateur pour le "Ping"
    async def async_update_data():
        """Vérifie si la Recalbox répond aux ping."""
        success = False
        try:
            async with async_timeout.timeout(5):
                success = await api.ping()
        except Exception as err:
            # Si échec de connexion, on considère qu'elle est OFF
            success = False
        hasAnySuccessBefore = any(history)
        history.append(success)
        _LOGGER.debug(f"Historique des pings sur la Recalbox {api.host} : {list(history)}")
        if any(history) :
            # The recalbox has Pings OK in the history
            return True
        elif hasAnySuccessBefore :
            # La recalbox n'a plus de Ping OK mais elle en avait juste avant
            _LOGGER.info("The Recalbox doesnt answer to Pings anymore... Considering it as offline from now.")
            return False
        else :
            # La recalbox ne répondait déjà plus aux pings, reste dans la continuité
            return False

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Recalbox Availability",
        update_method=async_update_data,
        update_interval=frequency, # Fréquence du check (ici: 30s)
    )

    # On lance le premier rafraîchissement
    await coordinator.async_config_entry_first_refresh()
    return coordinator