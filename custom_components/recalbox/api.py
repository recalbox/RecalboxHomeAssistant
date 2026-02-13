# api.py
import httpx
import asyncio
import logging
import socket
import urllib.parse
from homeassistant.core import (
    HomeAssistant
)

_LOGGER = logging.getLogger(__name__)

class RecalboxAPI:
    def __init__(self,
                 hass: HomeAssistant,
                 host: str = "recalbox.local",
                 api_port_os: int = 80,
                 api_port_gamesmanager: int = 81,
                 udp_recalbox: int = 1337, # https://github.com/recalbox/recalbox-api
                 udp_retroarch: int = 55355, # https://docs.libretro.com/development/retroarch/network-control-interface/
                 api_port_kodi: int = 8081, # https://kodi.wiki/view/JSON-RPC_API
                 only_ip_v4: bool = True,
                 ):
        self.host = host
        self.api_port_os = api_port_os # Arrêter, Reboot de Recalbox...
        self.api_port_gamesmanager = api_port_gamesmanager # Lister les roms, demander un screenshot...
        self.udp_recalbox = udp_recalbox # Lancer une ROM
        self.udp_retroarch = udp_retroarch
        self.api_port_kodi = api_port_kodi # Pour quitter Kodi
        self.only_ip_v4 = only_ip_v4
        # On récupère la session globale de HA
        # https://developers.home-assistant.io/docs/asyncio_blocking_operations/#load_verify_locations :
        # httpx: homeassistant.helpers.httpx_client.get_async_client to create the httpx.AsyncClient
        self._http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            ),
            transport=httpx.AsyncHTTPTransport(
                local_address="0.0.0.0" if only_ip_v4 else None,
                retries=3, # fait des retry en cas d'échec DNS
                verify=False # pas de vérification SSL : pas de certificat en .local
            ),
            verify=False # pas de vérification SSL : pas de certificat en .local
        )
        _LOGGER.debug(f"Create API with {"IPv4 only" if self.only_ip_v4 else "IPv4 and IPv6"} supported")


    # --------- Network tools -----------

    def _getSocketType(self):
        if self.only_ip_v4:
            return socket.AF_INET  # Force la résolution en IPv4
        else :
            return socket.AF_UNSPEC  # Peut avoir du IPv6 ou IPv4


    async def close(self):
        """Ferme la session proprement."""
        _LOGGER.debug(f"Closing API httpx client connexions")
        await self._http_client.aclose()


    # -------- Generic UDP / HTTP functions ----------

    async def send_udp_command(self, port, message):
        socket_type = self._getSocketType()
        _LOGGER.debug(f"Envoi UDP {port} ({socket_type}): \"{message}\"")
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            remote_addr=(self.host, port),
            family=socket_type
        )
        try:
            transport.sendto(message.encode())
            _LOGGER.debug(f"UDP message sent !")
            return True
        except Exception as e:
            _LOGGER.error(f"Fail to send UDP message to {self.host} on port {port} : {e}")
            return False
        finally:
            transport.close()


    async def post_api(self, path, port=80) -> bool:
        url = f"http://{self.host}:{port}{path}"
        _LOGGER.debug(f"API POST {url}")
        try:
            response = await self._http_client.post(url)
            response.raise_for_status()
            return response.status_code == 200
        except httpx.HTTPError as e:
            _LOGGER.error(f"Failed to call {url}")
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to call {url}")
            raise



    # ------- Specific services ----------

    async def get_recalbox_version(self) -> str | None :
        """Récupérer la version par l'API"""
        url = f"http://{self.host}:{self.api_port_gamesmanager}/api/versions"
        # Renvoie :
        # {
        #     "webapi": "2.0",
        #     "recalbox": "10.0\n",
        #     "linux": "Linux version 6.12.25-v7",
        #     "libretro": {
        #         "retroarch": "1.21.0",
        #         "cores": {
        #             "": "",
        #             "2048": "v1.0 8bf45bfa90",
        #             "AppleWin": "1.30.20.0",
        #             "Atari800": "3.1.0 8bf45bfa90",
        #             "Beetle Lynx": "v1.24.0 8bf45bfa90",
        #             "Beetle NeoPop": "v1.29.0.0 8bf45bfa90",
        #             "Beetle PCE Fast": "v1.31.0.0 8bf45bfa90",
        #             "Beetle SuperGrafx": "v1.29.0 8bf45bfa90",
        #             "Beetle VB": "v1.31.0 8bf45bfa90",
        #             "Beetle WonderSwan": "v0.9.35.1 8bf45bfa90",
        #             "Cannonball": "git",
        #             "DOSBox-pure": "1.0-preview2",
        #             "Dinothawr": "v1.0 8bf45bfa90",
        #             "EasyRPG Player": "0.8",
        #             "EightyOne": "1.0a 8bf45bf",
        #             "FCEUmm": "(SVN) 8bf45bfa90",
        #             "FinalBurn Neo": "v1.0.0.03 8bf45bfa90",
        #             "Flycast": "0.1 8bf45bfa90",
        #             "FreeChaF": "1.0 8bf45bfa90",
        #             "FreeIntv": "1.2",
        #             "Gambatte": "v0.5.0-netlink 8bf45bfa90",
        #             "Game & Watch": "1.6.3",
        #             "Gearcoleco": "1.0.1",
        #             "Geargrafx": "10.0-dirty",
        #             "Gearsystem": "baa78638",
        #             "Genesis Plus GX": "v1.7.4-83485a27",
        #             "Genesis Plus GX Wide": "v1.7.4-b7d31422",
        #             "Geolith": "0.2.1",
        #             "Handy": "0.97 8bf45bfa90",
        #             "Hatari": "1.8 8bf45bfa90",
        #             "Libretro-EmuSCV": "0.14.20221017160000",
        #             "LowRes NX": "1.2",
        #             "MAME 2000": "0.37b5 8bf45bfa90",
        #             "MAME 2003 (0.78)": "0.78 8bf45bfa90",
        #             "MAME 2003-Plus": " 8bf45bfa90",
        #             "MAME 2010": "0.139 8bf45bfa90",
        #             "MAME 2015": "0.160 8bf45bfa90",
        #             "Meteor GBA": "v1.4 8bf45bfa90",
        #             "Mini vMac": "b36",
        #             "Mr.Boom": "5.3 8bf45bfa90",
        #             "Mu": "v1.3.1 8bf45bfa90",
        #             "Mupen64Plus-Next": "2.8-GLES2-680e033f",
        #             "NXEngine": "1.0.0.6",
        #             "Neko Project II kai": "rev.1 53a4fa3d698c22bf02a7fc78c3b73ba55e4a0732",
        #             "NeoCD": "2022 8bf45bfa90",
        #             "Nestopia": "1.52.0 8bf45bfa90",
        #             "O2EM": "1.18 8bf45bfa90",
        #             "Opera": "1.0.0 8bf45bfa90",
        #             "PCSX-ReARMed": "r24l 8bf45bfa90",
        #             "PUAE": "5.0.0 8bf45bfa90",
        #             "PX68K": "0.15+ 8bf45bfa90",
        #             "ParaLLEl N64": "2.0-rc2-1da824e1",
        #             "PicoDrive": "2.05-8bf45bfa90",
        #             "PokeMini": "v0.60",
        #             "Potator": "1.0.5 8bf45bfa90",
        #             "PrBoom": "v2.5.0 8bf45bfa90",
        #             "ProSystem": "1.3e 8bf45bfa90",
        #             "QUASI88": "0.6.4 8bf45bfa90",
        #             "QuickNES": "1.0-WIP 10.0-dirty",
        #             "RACE": "v2.16 8bf45bfa90",
        #             "REminiscence": "0.3.6",
        #             "SameBoy": "0.16.6 8bf45bfa90",
        #             "SameDuck": "0.13.6 8bf45bfa90",
        #             "ScummVM": "10.0",
        #             "Snes9x": "1.63 8bf45bfa90",
        #             "Snes9x 2005 Plus": "v1.36 8bf45bfa90",
        #             "Snes9x 2010": "1.52.4 8bf45bfa90",
        #             "Stella": "7.0_pre 8bf45bfa90",
        #             "Stella 2014": "3.9.3 8bf45bfa90",
        #             "Supafaust": "1.29.0 8bf45bfa90",
        #             "SwanStation": "1.0.0",
        #             "TGB Dual": "v0.8.3 8bf45bfa90",
        #             "TIC-80": "1.2.44800-dev (8bf45bf)",
        #             "TamaLIBretro": "git-67605e42",
        #             "The Powder Toy": "92.5.336",
        #             "TyrQuake": "v0.62 8bf45bfa90",
        #             "Uzem": "v2.0",
        #             "VICE x128": "3.8 8bf45bfa90",
        #             "VICE x64": "3.8 8bf45bfa90",
        #             "VICE x64sc": "3.8 8bf45bfa90",
        #             "VICE xcbm2": "3.8 8bf45bfa90",
        #             "VICE xcbm5x0": "3.8 8bf45bfa90",
        #             "VICE xpet": "3.8 8bf45bfa90",
        #             "VICE xplus4": "3.8 8bf45bfa90",
        #             "VICE xscpu64": "3.8 8bf45bfa90",
        #             "VICE xvic": "3.8 8bf45bfa90",
        #             "VecX": "1.2 8bf45bfa90",
        #             "WASM-4": "v1 8bf45bfa90",
        #             "a5200": "2.0.2 8bf45bfa90",
        #             "arduous": "0.1.0",
        #             "bk": "v1.0 8bf45bfa90",
        #             "blueMSX": "git 8bf45bfa90",
        #             "cap32": "4.5.4 8bf45bfa90 HI",
        #             "crocods": "git 8bf45bfa90",
        #             "dice": "0.4.2",
        #             "dirksimple": "0.3",
        #             "ecwolf": "v0.01",
        #             "fMSX": "6.0 8bf45bfa90",
        #             "fake-08": "0.0.2.20",
        #             "fuse": "1.6.0 8bf45bf",
        #             "gong": "v1.0 8bf45bfa90",
        #             "gpSP": "v0.91 8bf45bfa90",
        #             "hatariB": "v0.4 unstable preview 8bf45bfa90 Feb 12 2026 13:49:00",
        #             "holani": "0.9.6-1",
        #             "image display": "v0.1",
        #             "lutro": "0.0.1 8bf45bfa90",
        #             "mGBA": "0.11-dev 8bf45bfa90",
        #             "mojozork": "0.2",
        #             "retro-8 (alpha)": "0.1b 8bf45bfa90",
        #             "theodore": "10.0-dirty",
        #             "uae4arm": "0.5",
        #             "x1": "0.60",
        #             "xrick": "021212-Dev"
        #         }
        #     }
        # }
        _LOGGER.debug(f"API GET versions from {url}")
        try:
            response = await self._http_client.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            # pour trimmer la version, ou renvoyer None si c'est None ou un texte vide
            return (data.get("recalbox") or "").strip() or None
        except httpx.HTTPError as e:
            _LOGGER.error(f"Failed to get version from {url} : {e}")
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to get version from {url} : {e}")
            raise




    async def get_roms(self, console):
        url = f"http://{self.host}:{self.api_port_gamesmanager}/api/systems/{console}/roms"
        _LOGGER.debug(f"API GET roms from {url}")
        try:
            response = await self._http_client.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("roms", [])
        except httpx.HTTPError as e:
            _LOGGER.error(f"Failed to get roms list on {url} : {e}")
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to get roms list on {url} : {e}")
            raise


    async def quit_kodi(self) -> bool:
        kodi_url = f"http://{self.host}:{self.api_port_kodi}/jsonrpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "Application.Quit",
            "id": 1
        }
        _LOGGER.debug(f"API to quit Kodi : {kodi_url}")
        try:
            response = await self._http_client.post(kodi_url, json=payload, timeout=5)
            response.raise_for_status()
            await asyncio.sleep(5)
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to quit Kodi via JSON RPC on {kodi_url} : {e}")
            return False


    async def is_kodi_running(self) -> bool:
        kodi_url = f"http://{self.host}:{self.api_port_kodi}/jsonrpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "JSONRPC.Ping",
            "id": 1
        }
        _LOGGER.debug(f"Ping Kodi : {kodi_url}")
        try:
            response = await self._http_client.post(kodi_url, json=payload, timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            _LOGGER.info(f"Failed to ping Kodi via JSON RPC on {kodi_url} : {e}")
            return False


    # On va interroger Recalbox pour connaitre le status.
    # S'il répond pas, on va quand même regarder si Kodi est lancé au démarrage
    async def get_current_status(self):
        url = f"http://{self.host}:{self.api_port_gamesmanager}/api/status"
        _LOGGER.debug(f"API GET current Recalbox status {url}")
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
        try:
            response = await self._http_client.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            is_game_running = (data.get("Action")=="rungame")
            imagePath = None
            # Generate image path
            if (is_game_running
                    and data.get("Game", {}).get("GamePath") is not None
                    and data.get("System", {}).get("SystemId") is not None
                    and data.get("Game", {}).get("ImagePath") is not None) :
                romPathUrlEncoded = urllib.parse.quote(data.get("Game", {}).get("GamePath"), safe='')
                imagePath = f"api/systems/{data.get("System", {}).get("SystemId")}/roms/metadata/image/{romPathUrlEncoded}"
                _LOGGER.debug(f"Auto created image path : {imagePath}")

            recalboxVersion = None
            try :
                recalboxVersion = await self.get_recalbox_version()
                _LOGGER.debug(f"Got recalbox version via API : {recalboxVersion}")
            except Exception as e:
                _LOGGER.warning(f"Cannot get recalbox version via API : {e}")

            return {
                "game": self.clean_game_name(data.get("Game", {}).get("Game") if is_game_running else None),
                "console": data.get("System", {}).get("System"),
                "rom": data.get("Game", {}).get("GamePath") if is_game_running else None,
                "genre": data.get("Game", {}).get("Genre") if is_game_running else None,
                "genreId": data.get("Game", {}).get("GenreId") if is_game_running else None,
                "imagePath": imagePath,
                "recalboxIpAddress": None,
                "recalboxVersion": recalboxVersion,
                "hardware": None,
                "scriptVersion": None,
                "status": "ON"
            }
        except Exception as e:
            _LOGGER.error(f"Failed to get recalbox status on API {url} ({e})")
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


    # ----------- test ping and ports ---------

    async def ping(self) -> bool:
        """Exécute un ping système vers l'hôte."""
        _LOGGER.debug(f"PING recalbox on {self.host}")
        command = f"ping {'-4 ' if self.only_ip_v4 else ''}-c 1 -W 1 {self.host} > /dev/null 2>&1"
        try:
            # On exécute la commande système de façon asynchrone
            process = await asyncio.create_subprocess_shell(command)
            await process.wait()

            _LOGGER.debug(f"Command \"{command}\" returned {process.returncode}")
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
                    conn = asyncio.open_connection(self.host, port, family=self._getSocketType())
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
        except Exception as ex:
            _LOGGER.debug(f"Failed to PING ports of {self.host} : {ex}")
            return False


# ------ utils


    def clean_game_name(self, raw_game_name):
        if raw_game_name is None:
            return None
        elif len(raw_game_name) > 4 and raw_game_name[:3].isdigit() and raw_game_name[3] == " ":
            return raw_game_name[4:]
        else:
            return raw_game_name