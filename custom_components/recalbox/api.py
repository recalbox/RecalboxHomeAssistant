# api.py
import aiohttp
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class RecalboxAPI:
    def __init__(self,
                 host: str = "recalbox.local",
                 api_port_os: int = 80,
                 api_port_webmanager: int = 81,
                 udp_recalbox: int = 1337,
                 udp_emulstation: int = 55355
                 ):
        self.host = host
        self.api_port_os = api_port_os
        self.api_port_webmanager = api_port_webmanager
        self.udp_recalbox = udp_recalbox
        self.udp_emulstation = udp_emulstation

    async def send_udp_command(self, port, message):
        _LOGGER.debug(f"Envoi UDP {port}: {message}")
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            remote_addr=(self.host, port)
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
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url) as response:
                    return response.status == 200
            except:
                _LOGGER.error(f"Failed to call {url}")
                raise


    async def get_roms(self, console, port=81):
        url = f"http://{self.host}:{port}/api/systems/{console}/roms"
        _LOGGER.debug(f"API GET roms from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("roms", [])
            except:
                _LOGGER.error(f"Failed to get roms list on {url}")
                raise


    async def ping(self) -> bool:
        """Exécute un ping système vers l'hôte."""
        _LOGGER.debug(f"PING recalbox on {self.host}")
        command = f"ping -c 1 -W 1 {self.host} > /dev/null 2>&1"
        try:
            # On exécute la commande système de façon asynchrone
            process = await asyncio.create_subprocess_shell(command)
            await process.wait()

            _LOGGER.debug(f"PING {self.host} returned {process.returncode}")
            # Si le code de retour est 0, l'hôte a répondu
            return process.returncode == 0
        except:
            _LOGGER.debug(f"Failed to PING {self.host}")
            return False;
