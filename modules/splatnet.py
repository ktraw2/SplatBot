from modules.async_client import AsyncClient


class Splatnet(AsyncClient):

    """
    Constructor for Splatnet

    If no session is given, make a new one via aiohttp
    """
    def __init__(self, session=None):
        super(Splatnet, self).__init__(user_agent="SplatBot/1.0 Github: github.com/ktraw2/SplatBot",
                                       request_prefix="https://splatoon2.ink/data/", request_suffix=".json",
                                       session=session)

    """
    Gets the JSON data for turf wars
    
    Returns the JSON data about turf wars' stages and when the rotation will occur
    """
    async def get_turf(self):
        return (await self.send_json_request("schedules"))['regular']

    """
    Gets the JSON data for ranked battles
    
    Returns the JSON data about ranked battles' mode, stages, and when the rotation will occur
    """
    async def get_ranked(self):
        return (await self.send_json_request("schedules"))['gachi']

    """
    Gets the JSON data for league battles

    Returns the JSON data about league battles' mode, stages, and when the rotation will occur
    """
    async def get_league(self):
        return (await self.send_json_request("schedules"))['league']

    """
    Gets the JSON data for salmon run's weapons and stages

    Returns the JSON data about salmon run's weapons and stages for the next 2 rotations
    """
    async def get_salmon_detail(self):
        return (await self.send_json_request("coop-schedules"))['details']

    """
    Gets the JSON data for salmon run's stages
    
    Returns the JSON data about salmon run's stages
    """
    async def get_salmon_schedule(self):
        return (await self.send_json_request("coop-schedules"))['schedules']

    """
    Gets the JSON data for splatfest in North America
    
    Returns the JSON data for splatfests in NA: returns info about the festival and the results
    """
    async def get_na_splatfest(self):
        return (await self.send_json_request("festivals"))['na']
