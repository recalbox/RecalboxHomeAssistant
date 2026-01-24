# api.py
import aiohttp
import asyncio

class RecalboxAPI:
    def __init__(self, host):
        self.host = host

    async def send_udp_command(self, port, message):
        print(f"Envoi UDP {port}: {message}")
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            remote_addr=(self.host, port)
        )
        try:
            transport.sendto(message.encode())
            return True
        except:
            return False
        finally:
            transport.close()


    async def post_api(self, path, port=80):
        url = f"http://{self.host}:{port}{path}"
        print(f"API POST {url}")
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as response:
                return response.status == 200


    async def get_roms(self, console):
        url = f"http://{self.host}:81/api/systems/{console}/roms"
        print(f"API GET roms from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("roms", [])
            except: return []

