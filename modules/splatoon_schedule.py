from enum import Enum, auto
from modules.splatnet import Splatnet
from datetime import datetime
from modules.linked_list import LinkedList

IMAGE_BASE = "https://splatoon2.ink/assets/splatnet"


class ScheduleTypes(Enum):
    REGULAR = auto()
    RANKED = auto()
    LEAGUE = auto()
    SALMON = auto()


class SplatoonSchedule:
    def __init__(self, target_time: datetime, schedule_type: ScheduleTypes, session=None):
        self.mode = None
        self.stage_a = None
        self.stage_a_image = None
        self.stage_b = None
        self.stage_b_image = None
        self.start_time = None
        self.end_time = None
        self.weapons_array = None           # for salmon run
        self.weapon_image_array = None      # for salmon run

        self.target_time = target_time
        self.schedule_type = schedule_type
        self.session = session

    async def populate_data(self):
        sn = Splatnet(self.session)
        timestamp = self.target_time.timestamp()
        data = None
        if self.schedule_type == ScheduleTypes.REGULAR:
            data = await sn.get_turf()
        elif self.schedule_type == ScheduleTypes.RANKED:
            data = await sn.get_ranked()
        elif self.schedule_type == ScheduleTypes.LEAGUE:
            data = await sn.get_league()
        elif self.schedule_type == ScheduleTypes.SALMON:
            data = await sn.get_salmon_schedule()

        # find a league session given the target time
        if self.schedule_type != ScheduleTypes.SALMON:
            for schedule in data:
                if schedule["start_time"] <= timestamp < schedule["end_time"]:
                    self.mode = schedule["rule"]["name"]
                    self.stage_a = schedule["stage_a"]["name"]
                    self.stage_a_image = IMAGE_BASE + schedule["stage_a"]["image"]
                    self.stage_b = schedule["stage_b"]["name"]
                    self.stage_b_image = IMAGE_BASE + schedule["stage_b"]["image"]
                    self.start_time = datetime.fromtimestamp(schedule["start_time"], self.target_time.tzname())
                    self.end_time = datetime.fromtimestamp(schedule["end_time"], self.target_time.tzname())
                    return True
            return False
        # salmon run is a special exception, requires special processing
        else:
            for schedule in data:
                if schedule["start_time"] <= timestamp < schedule["end_time"]:
                    self.mode = "Salmon Run"
                    self.stage_a = schedule["stage"]["name"]
                    self.stage_a_image = schedule["stage"]["image"]
                    self.stage_b = None
                    self.stage_b_image = None
                    self.start_time = datetime.fromtimestamp(schedule["start_time"], self.target_time.tzname())
                    self.end_time = datetime.fromtimestamp(schedule["end_time"], self.target_time.tzname())
                    self.weapons_array = LinkedList()
                    self.weapon_image_array = LinkedList()

                    # getting weapons
                    for weapon in schedule["weapons"]:
                        self.weapons_array.add(weapon["weapon"["name"]])
                        self.weapon_image_array.add(weapon["weapon"]["image"])
                    return True
            return False

    @staticmethod
    def format_time(time: datetime):
        return time.strftime("%I:%M %p")
