import aiohttp
import asyncio
import json
# TODO: Fix weird syntax error w/ import statement


class Splatnet:

    """
    Constructor for Splatnet

    If no session is given, make a new one via aiohttp
    """
    def __init__(self, session=None):
        if session is None:
            self.connection = aiohttp.ClientSession()
        else:
            self.connection = session

    """
    Sends a request to splatoon2.ink's API.
    
    Request param should match splatoon2.ink's API.
    return_raw_and_json denotes if you want both the raw file and the API returned
    Otherwise will return just the JSON
    
    Will return the JSON or the JSON and the raw file or an error code from splatoon2.ink.
    """
    async def __send_request__(self, request, return_raw_and_json=False):
        # Recommended header for splatoon2.ink's API
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

    """
    Gets the JSON data for turf wars
    
    Returns the JSON data about turf wars' stages and when the rotation will occur
    """
    async def get_turf(self):
        return await self.send_request("schedules")['regular']

    """
    Gets the JSON data for ranked battles
    
    Returns the JSON data about ranked battles' mode, stages, and when the rotation will occur
    """
    async def get_ranked(self):
        return await self.send_request("schedules")['gachi']

    """
    Gets the JSON data for league battles

    Returns the JSON data about league battles' mode, stages, and when the rotation will occur
    """
    async def get_league(self):
        return await self.send_request("schedules")['league']

    """
    Gets the JSON data for salmon run's weapons and stages

    Returns the JSON data about salmon run's weapons and stages for the next 2 rotations
    """
    async def get_salmon_detail(self):
        return await self.send_request("coop-schedules")['details']

    """
    Gets the JSON data for salmon run's stages
    
    Returns the JSON data about salmon run's stages
    """
    async def get_salmon_schedule(self):
        return await self.send_request("coop-schedules")['schedules']

    """
    Gets the JSON data for splatfest in North America
    
    Returns the JSON data for splatfests in NA: returns info about the festival and the results
    """
    async def get_na_splatfest(self):
        return await self.send_request("festivals.json")['na']

    # TODO: fix [] error found in above functions

