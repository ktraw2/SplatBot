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
        self.stage_b = None                 # Not populated for salmon run
        self.stage_b_image = None           # Not populated for salmon run
        self.start_time = None
        self.end_time = None
        self.weapons_array = None           # for salmon run

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
            data = await sn.get_salmon_detail()

        # find a regular/ranked/league session given the target time
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
                    self.stage_a_image = IMAGE_BASE + schedule["stage"]["image"]
                    self.start_time = datetime.fromtimestamp(schedule["start_time"], self.target_time.tzname())
                    self.end_time = datetime.fromtimestamp(schedule["end_time"], self.target_time.tzname())
                    self.weapons_array = LinkedList()

                    # getting weapons
                    for weapon in schedule["weapons"]:
                        # weapon id of -1 indicates a special weapon, parsed differently
                        if weapon["id"] != '-1':
                            self.weapons_array.add(weapon["weapon"]["name"])
                        else:
                            self.weapons_array.add(weapon["coop_special_weapon"]["name"])
                    return True

            # if we can't find a detailed schedule, search some more in the other schedule
            data = await sn.get_salmon_schedule()
            for schedule in data:
                if schedule["start_time"] <= timestamp < schedule["end_time"]:
                    self.mode = "Salmon Run"
                    self.start_time = datetime.fromtimestamp(schedule["start_time"], self.target_time.tzname())
                    self.end_time = datetime.fromtimestamp(schedule["end_time"], self.target_time.tzname())
                    return True
            return False

    @staticmethod
    def format_time(time: datetime):
        # returns <hour>:<time> <am/pm>
        return time.strftime("%I:%M %p")

    @staticmethod
    def format_time_sr(time: datetime):
        # returns <abbr. weekday> <abbr. month> <date> <hour>:<time> <am/pm>
        return time.strftime("%a %b %d %I:%M %p")
