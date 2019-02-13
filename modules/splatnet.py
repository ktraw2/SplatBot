import aiohttp
import asyncio
import json
# TODO: Fix weird syntax error w/ import statement


class Splatnet:

    def __init__(self, session=None):
        if session is None:
            self.connection = aiohttp.ClientSession()
        else:
            self.connection = session

    async def send_request(self, request, return_raw_and_json=False):
        """
        Returns the JSON of a request to a Splatoon2.ink endpoint, or returns the error code as JSON if unsuccessful
        """
        header = {"User:Agent": "SplatBot/1.0 Github: github.com/ktraw2/SplatBot"}
        async with self.connection.get("https://splatoon2.ink/data/" + request + ".json", header=header) as response:
            if response.status == 200:
                if return_raw_and_json:
                    text = await response.text()
                    return json.loads(text), text
                else:
                    return json.loads(await response.text())
            elif response.status == 429:
                # bot is sending too many requests, try again after a couple seconds
                print("Bot is being rate limited by Splatoon2.ink, resending request...")
                await asyncio.sleep(5)
                return await self.send_request(request, return_raw_and_json=return_raw_and_json)
            else:
                error_string = '{"error":' + str(response.status) + '}'
                if return_raw_and_json:
                    return json.loads(error_string), error_string
                else:
                    return json.loads(error_string)

    async def get_turf(self):
        return await self.send_request("schedules")['regular']

    async def get_ranked(self):
        return await self.send_request("schedules")['gachi']

    async def get_league(self):
        return await self.send_request("schedules")['league']

    async def get_salmon_detail(self):
        return await self.send_request("coop-schedules")['details']

    async def get_salmon_schedule(self):
        return await self.send_request("coop-schedules")['schedules']

    async def get_na_splatfest(self):
        return await self.send_request("festivals.json")['na']

    # TODO: fix [] error found in above functions

