from modules.splatnet import Splatnet
from datetime import datetime, timedelta

IMAGE_BASE = "https://splatoon2.ink/assets/splatnet"


class League:
    def __init__(self, target_time: datetime, session = None):
        self.mode = None
        self.stage_a = None
        self.stage_a_image = None
        self.stage_b = None
        self.stage_b_image = None
        self.start_time = None
        self.end_time = None

        self.target_time = target_time
        self.session = session

    async def populate_data(self):
        sn = Splatnet(self.session)
        timestamp = self.target_time.timestamp()
        league_data = await sn.get_league()

        # find a league session given the target time
        for league_schedule in league_data:
            if league_schedule["start_time"] <= timestamp < league_schedule["end_time"]:
                self.mode = league_schedule["rule"]["name"]
                self.stage_a = league_schedule["stage_a"]["name"]
                self.stage_a_image = IMAGE_BASE + league_schedule["stage_a"]["image"]
                self.stage_b = league_schedule["stage_b"]["name"]
                self.stage_b_image = IMAGE_BASE + league_schedule["stage_b"]["image"]
                self.start_time = datetime.fromtimestamp(league_schedule["start_time"], self.target_time.tzname())
                self.end_time = datetime.fromtimestamp(league_schedule["end_time"], self.target_time.tzname())
                return True
        return False
