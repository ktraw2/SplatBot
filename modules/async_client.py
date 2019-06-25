import aiohttp
import asyncio
import json


class AsyncClient:
    def __init__(self, user_agent: str = "", request_prefix: str = "", request_suffix: str = "", session=None):
        self.user_agent = user_agent
        self.request_prefix = request_prefix
        self.request_suffix = request_suffix

        if session is None:
            self.connection = aiohttp.ClientSession()
        else:
            self.connection = session

    async def send_request(self, request: str):
        header = {"User:Agent": self.user_agent}
        async with self.connection.get(self.request_prefix + request + self.request_suffix, headers=header) as response:
            if response.status == 200:
                return await response.text()
            elif response.status == 429:
                # bot is sending too many requests, try again after a couple seconds
                print("Bot is being rate limited, resending request...")
                await asyncio.sleep(5)
                return await self.send_request(request)
            else:
                return '{"error":' + str(response.status) + '}'

    async def send_image_request(self, image_url: str, file_path: str):
        header = {"User:Agent": self.user_agent}
        async with self.connection.get(image_url, headers=header) as response:
            image = await response.read()
            if response.status == 200:
                with open(file_path, "wb") as f:
                    f.write(image)
                    return
            elif response.status == 429:
                # bot is sending too many requests, try again after a couple seconds
                print("Bot is being rate limited, resending request...")
                await asyncio.sleep(5)
                return await self.send_image_request(image_url, file_path)
            else:
                raise Exception("Error with getting image: " + str(response.status))

    async def send_json_request(self, request: str, return_raw_and_json: bool = False):
        raw_data = await self.send_request(request)
        json_data = json.loads(raw_data)
        if return_raw_and_json:
            return json_data, raw_data
        else:
            return json_data
