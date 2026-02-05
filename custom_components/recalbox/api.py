# api.py
import aiohttp
import asyncio
import logging
import socket

_LOGGER = logging.getLogger(__name__)

class RecalboxAPI:
    def __init__(self,
                 host: str = "recalbox.local",
                 api_port_os: int = 80,
                 api_port_gamesmanager: int = 81,
                 udp_recalbox: int = 1337, # https://github.com/recalbox/recalbox-api
                 udp_retroarch: int = 55355, # https://docs.libretro.com/development/retroarch/network-control-interface/
                 api_port_kodi: int = 8081, # https://kodi.wiki/view/JSON-RPC_API
                 ):
        self.host = host
        self.api_port_os = api_port_os # Arrêter, Reboot de Recalbox...
        self.api_port_gamesmanager = api_port_gamesmanager # Lister les roms, demander un screenshot...
        self.udp_recalbox = udp_recalbox # Lancer une ROM
        self.udp_retroarch = udp_retroarch
        self.api_port_kodi = api_port_kodi # Pour quitter Kodi


    async def send_udp_command(self, port, message):
        _LOGGER.debug(f"Envoi UDP {port}: \"{message}\"")
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            remote_addr=(self.host, port),
            family=socket.AF_INET  # Force la résolution en IPv4
        )
        try:
            transport.sendto(message.encode())
            return True
        except:
            _LOGGER.error(f"Fail to send UDP message to {self.host} on port {port}")
            return False
        finally:
            transport.close()


    async def post_api(self, path, port=80):
        url = f"http://{self.host}:{port}{path}"
        _LOGGER.debug(f"API POST {url}")
        connector = aiohttp.TCPConnector(family=socket.AF_INET) # Force la résolution en IPv4
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.post(url) as response:
                    return response.status == 200
            except:
                _LOGGER.error(f"Failed to call {url}")
                raise


    async def get_roms(self, console):
        url = f"http://{self.host}:{self.api_port_gamesmanager}/api/systems/{console}/roms"
        _LOGGER.debug(f"API GET roms from {url}")
        connector = aiohttp.TCPConnector(family=socket.AF_INET) # Force la résolution en IPv4
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("roms", [])
            except:
                _LOGGER.error(f"Failed to get roms list on {url}")
                raise


    async def quit_kodi(self) -> bool:
        kodi_url = f"http://{self.host}:{self.api_port_kodi}/jsonrpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "Application.Quit",
            "id": 1
        }
        _LOGGER.debug(f"API to quit Kodi : {kodi_url}")
        connector = aiohttp.TCPConnector(family=socket.AF_INET) # Force la résolution en IPv4
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.post(kodi_url, json=payload, timeout=5) as response:
                    if response.status == 200:
                        await asyncio.sleep(5)
                        return True
            except:
                _LOGGER.error(f"Failed to quit Kodi via JSON RPC on {kodi_url}")
                return False


    async def is_kodi_running(self) -> bool:
        kodi_url = f"http://{self.host}:{self.api_port_kodi}/jsonrpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "JSONRPC.Ping",
            "id": 1
        }
        _LOGGER.debug(f"Ping Kodi : {kodi_url}")
        connector = aiohttp.TCPConnector(family=socket.AF_INET) # Force la résolution en IPv4
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.post(kodi_url, json=payload, timeout=5) as response:
                    if response.status == 200:
                        return True
            except:
                _LOGGER.info(f"Failed to ping Kodi via JSON RPC on {kodi_url}")
                return False


    # On va interroger Recalbox pour connaitre le status.
    # S'il répond pas, on va quand même regarder si Kodi est lancé au démarrage
    async def get_current_status(self):
        url = f"http://{self.host}:{self.api_port_gamesmanager}/api/status"
        _LOGGER.debug(f"API GET current Recalbox status {url}")
        connector = aiohttp.TCPConnector(family=socket.AF_INET) # Force la résolution en IPv4
        # {
        #   "Action": "rungame",
        #   "Parameter": "/recalbox/share/roms/megadrive/001 Sonic 1.bin",
        #   "Version": "2.0",
        #   "System": {
        #     "System": "Sega Megadrive",
        #     "SystemId": "megadrive",
        #     "DefaultEmulator": {
        #       "Emulator": "libretro",
        #       "Core": "picodrive"
        #     }
        #   },
        #   "Game": {
        #     "Game": "001 Sonic 1",
        #     "GamePath": "/recalbox/share/roms/megadrive/001 Sonic 1.bin",
        #     "IsFolder": false,
        #     "ImagePath": "/recalbox/share/roms/megadrive/media/images/Sonic The Hedgehog c28514e75f5cdcce646d3f568f089ce0.png",
        #     "ThumbnailPath": "",
        #     "VideoPath": "",
        #     "Developer": "SEGA",
        #     "Publisher": "SEGA",
        #     "Players": "1",
        #     "Region": "us,jp,eu",
        #     "Genre": "Plateforme",
        #     "GenreId": "257",
        #     "Favorite": true,
        #     "Hidden": false,
        #     "Adult": false,
        #     "SelectedEmulator": {
        #       "Emulator": "libretro",
        #       "Core": "picodrive"
        #     }
        #   }
        # }
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "game": data.get("Game", {}).get("Game"),
                            "console": data.get("System", {}).get("System"),
                            "rom": data.get("Game", {}).get("GamePath"),
                            "genre": data.get("Game", {}).get("Genre"),
                            "genreId": data.get("Game", {}).get("GenreId"),
                            "imagePath": None,
                            "recalboxIpAddress": None,
                            "recalboxVersion": None,
                            "hardware": None,
                            "scriptVersion": None,
                            "status": "ON"
                        }
            except:
                _LOGGER.error(f"Failed to get recalbox status on API {url}")
                if (await self.is_kodi_running()) :
                    _LOGGER.debug(f"Kodi seems to be running ! Simulating JSON data for Recalbox HA status")
                    return {
                        "game": None,
                        "console": "Kodi",
                        "rom": None,
                        "genre": None,
                        "genreId": None,
                        "imagePath": None,
                        "recalboxIpAddress": None,
                        "recalboxVersion": None,
                        "hardware": None,
                        "scriptVersion": None,
                        "status": "ON"
                    }
                else:
                    _LOGGER.error(f"Kodi is not reachable neither")
                    raise

    async def ping(self) -> bool:
        """Exécute un ping système vers l'hôte."""
        _LOGGER.debug(f"PING recalbox on {self.host}")
        command = f"ping -4 -c 1 -W 1 {self.host} > /dev/null 2>&1"
        try:
            # On exécute la commande système de façon asynchrone
            process = await asyncio.create_subprocess_shell(command)
            await process.wait()

            _LOGGER.debug(f"PING {self.host} returned {process.returncode}")
            # Si le code de retour est 0, l'hôte a répondu
            return process.returncode == 0
        except:
            _LOGGER.debug(f"Failed to PING {self.host}")
            return False


    async def testPorts(self) -> bool:
        try:
            _LOGGER.info(f"Testing TCP+UDP ports on {self.host}...")
            TCP_PORTS = [self.api_port_os, self.api_port_gamesmanager] # On teste pas Kodi car le port est ouvert que s'il est lancé
            UDP_PORTS = [self.udp_recalbox, self.udp_retroarch]
            for port in TCP_PORTS:
                try:
                    _LOGGER.debug(f"Testing TCP port {port} on {self.host}")
                    conn = asyncio.open_connection(self.host, port, family=socket.AF_INET)
                    _reader, writer = await asyncio.wait_for(conn, timeout=1.0)
                    writer.close()
                    await writer.wait_closed()
                except Exception as e:
                    _LOGGER.error(f"TCP Port {port} is closed or unreachable: {e}")
                    return False

            # En UDP, on ne peut pas vraiment savoir si le port est "ouvert"
            # sans réponse du serveur, mais on peut vérifier si l'interface réseau accepte l'envoi.
            for port in UDP_PORTS:
                success = await self.send_udp_command(port, "PING") # Envoi d'un message neutre
                if not success:
                    _LOGGER.error(f"UDP Port {port} is unreachable")
                    return False

            return True
        except:
            _LOGGER.debug(f"Failed to PING ports of {self.host}")
            return False
