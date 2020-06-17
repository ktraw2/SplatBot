from enum import Enum, auto
from modules.splatnet import Splatnet
from datetime import datetime
from modules.linked_list import LinkedList
from modules.salmon_emotes import gen_emote_id, SR_TERM_CHAR

IMAGE_BASE = "https://splatoon2.ink/assets/splatnet"


class ModeTypes(Enum):
    REGULAR = auto()
    RANKED = auto()
    LEAGUE = auto()
    SALMON = auto()
    PRIVATE = auto()


class SplatoonRotation:
    def __init__(self, target_time: datetime, mode_type: ModeTypes, session=None, restore_from_pickle: dict = None):
        self.target_time = target_time
        self.mode_type = mode_type
        self.session = session

        # when is object being created?
        if restore_from_pickle is None:
            # at runtime, the data will need to be populated by the program after construction
            self.mode = None
            self.stage_a = None
            self.stage_a_image = None
            if mode_type is not ModeTypes.SALMON:
                self.stage_b = None                 # Not populated for salmon run
                self.stage_b_image = None           # Not populated for salmon run
            self.start_time = None
            self.end_time = None
            if mode_type is ModeTypes.SALMON:
                self.weapons_array = None           # for salmon run only
        else:
            # we are restoring from the pickle, bring in all the data
            if "mode" in restore_from_pickle:
                self.mode = restore_from_pickle["mode"]
            else:
                self.mode = None

            if "stage_a" in restore_from_pickle:
                self.stage_a = restore_from_pickle["stage_a"]
            else:
                self.stage_a = None

            if "stage_a_image" in restore_from_pickle:
                self.stage_a_image = restore_from_pickle["stage_a_image"]
            else:
                self.stage_a_image = None

            if "stage_b" in restore_from_pickle:
                self.stage_b = restore_from_pickle["stage_b"]
            else:
                self.stage_b = None

            if "stage_b_image" in restore_from_pickle:
                self.stage_b_image = restore_from_pickle["stage_b_image"]
            else:
                self.stage_b_image = None

            if "start_time" in restore_from_pickle:
                self.start_time = restore_from_pickle["start_time"]
            else:
                self.start_time = None

            if "end_time" in restore_from_pickle:
                self.end_time = restore_from_pickle["end_time"]
            else:
                self.end_time = None

            if "weapons_array" in restore_from_pickle:
                self.weapons_array = restore_from_pickle["weapons_array"]
            else:
                self.weapons_array = None

            if "target_time" in restore_from_pickle:
                self.target_time = restore_from_pickle["target_time"]
            else:
                self.target_time = None

            if "mode_type" in restore_from_pickle:
                self.mode_type = restore_from_pickle["mode_type"]
            else:
                self.mode_type = None

            # NOTE: can't restore the session object

    def __reduce__(self):
        """
        For pickling this object, we need to keep all data but the session
        :return: a tuple with class information as well as all needed data fields
        """
        restore_from_pickle = {
            "mode": self.mode,
            "stage_a": self.stage_a,
            "stage_a_image": self.stage_a_image,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

        if self.mode_type is ModeTypes.SALMON:
            restore_from_pickle["weapons_array"] = self.weapons_array
        else:
            restore_from_pickle["stage_b"] = self.stage_b
            restore_from_pickle["stage_b_image"] = self.stage_b_image

        return (self.__class__, (self.target_time, self.mode_type, None, restore_from_pickle))

    async def populate_data(self):
        sn = Splatnet(self.session)
        timestamp = self.target_time.timestamp()
        data = None
        if self.mode_type is ModeTypes.REGULAR:
            data = await sn.get_turf()
        elif self.mode_type is ModeTypes.RANKED:
            data = await sn.get_ranked()
        elif self.mode_type is ModeTypes.LEAGUE:
            data = await sn.get_league()
        elif self.mode_type is ModeTypes.SALMON:
            data = await sn.get_salmon_detail()

        # find a regular/ranked/league session given the target time
        if self.mode_type is not ModeTypes.SALMON:
            for rotation in data:
                if rotation["start_time"] <= timestamp < rotation["end_time"]:
                    self.mode = rotation["rule"]["name"]
                    self.stage_a = rotation["stage_a"]["name"]
                    self.stage_a_image = IMAGE_BASE + rotation["stage_a"]["image"]
                    self.stage_b = rotation["stage_b"]["name"]
                    self.stage_b_image = IMAGE_BASE + rotation["stage_b"]["image"]
                    self.start_time = datetime.fromtimestamp(rotation["start_time"], self.target_time.tzname())
                    self.end_time = datetime.fromtimestamp(rotation["end_time"], self.target_time.tzname())
                    return True
            return False
        # salmon run is a special exception, requires special processing
        else:
            for rotation in data:
                if rotation["start_time"] <= timestamp < rotation["end_time"]:
                    self.mode = "Salmon Run"
                    self.stage_a = rotation["stage"]["name"]
                    self.stage_a_image = IMAGE_BASE + rotation["stage"]["image"]
                    self.start_time = datetime.fromtimestamp(rotation["start_time"], self.target_time.tzname())
                    self.end_time = datetime.fromtimestamp(rotation["end_time"], self.target_time.tzname())
                    self.weapons_array = LinkedList()

                    # getting weapons, using SR_TERM_CHAR to separate b/t weapon name and weapon id
                    for weapon in rotation["weapons"]:
                        # weapon id of -1 indicates a random weapon (non shiny question mark)
                        if weapon["id"] == '-1':
                            self.weapons_array.add(weapon["coop_special_weapon"]["name"] + " Weapon" + SR_TERM_CHAR +
                                                   "r1")  # using r1 for -1 as discord doesn't support "-" char
                        # weapon id of -2 indicates a grizzco weapon
                        elif weapon["id"] == '-2':
                            self.weapons_array.add(weapon["coop_special_weapon"]["name"] + " Grizzco Weapon" +
                                                   SR_TERM_CHAR + "r2")  # using r2 for -2
                        else:
                            self.weapons_array.add(weapon["weapon"]["name"] + SR_TERM_CHAR + weapon["id"])
                    return True

            # if we can't find a detailed rotation, search some more in the other rotations
            data = await sn.get_salmon_schedule()
            for rotation in data:
                if rotation["start_time"] <= timestamp < rotation["end_time"]:
                    self.mode = "Salmon Run"
                    self.start_time = datetime.fromtimestamp(rotation["start_time"], self.target_time.tzname())
                    self.end_time = datetime.fromtimestamp(rotation["end_time"], self.target_time.tzname())
                    return True
            return False

    @staticmethod
    async def get_all_rotations(time: datetime, mode_type: ModeTypes, session=None):
        sn = Splatnet(session)
        data = None

        schedule_list = []

        if mode_type is ModeTypes.REGULAR:
            data = await sn.get_turf()
        elif mode_type is ModeTypes.RANKED:
            data = await sn.get_ranked()
        elif mode_type is ModeTypes.LEAGUE:
            data = await sn.get_league()
        elif mode_type is ModeTypes.SALMON:
            data = await sn.get_salmon_detail()

        if data is None:
            raise Exception("Splatnet call failed.")

        if mode_type is not ModeTypes.SALMON:
            for schedule in data:
                start_time = datetime.fromtimestamp(schedule["start_time"], time.tzname())
                element = SplatoonRotation(start_time, mode_type, session)
                element.mode = schedule["rule"]["name"]
                element.stage_a = schedule["stage_a"]["name"]
                element.stage_a_image = IMAGE_BASE + schedule["stage_a"]["image"]
                element.stage_b = schedule["stage_b"]["name"]
                element.stage_b_image = IMAGE_BASE + schedule["stage_b"]["image"]
                element.start_time = start_time
                element.end_time = datetime.fromtimestamp(schedule["end_time"], time.tzname())
                schedule_list.append(element)
        # salmon run is a special exception, requires special processing
        else:
            # Adding detailed info to the list
            for sr_schedule in data:
                start_time = datetime.fromtimestamp(sr_schedule["start_time"], time.tzname())
                element = SplatoonRotation(start_time, mode_type, session)
                element.mode = "Salmon Run"
                element.start_time = start_time
                element.end_time = datetime.fromtimestamp(sr_schedule["end_time"], time.tzname())

                element.stage_a = sr_schedule["stage"]["name"]
                element.stage_a_image = IMAGE_BASE + sr_schedule["stage"]["image"]
                element.weapons_array = LinkedList()

                # getting weapons
                for weapon in sr_schedule["weapons"]:
                    # weapon id of -1 indicates a random weapon (non shiny question mark)
                    if weapon["id"] == '-1':
                        element.weapons_array.add(weapon["coop_special_weapon"]["name"] + " Weapon" + SR_TERM_CHAR +
                                                  "r1")
                    # weapon id of -2 indicates grizzco weapon
                    elif weapon["id"] == '-2':
                        element.weapons_array.add(weapon["coop_special_weapon"]["name"] + " Grizzco Weapon" +
                                                  SR_TERM_CHAR + "r2")
                    else:
                        element.weapons_array.add(weapon["weapon"]["name"] + SR_TERM_CHAR + weapon["id"])

                schedule_list.append(element)

            # Adding salmon schedules that we don't know anything about
            data = await sn.get_salmon_schedule()
            for sr_schedule in data:
                # Skipping the first 2 in the list as we already parsed that info above
                if schedule_list[0].start_time != start_time or schedule_list[1].start_time != start_time:
                    start_time = datetime.fromtimestamp(sr_schedule["start_time"], time.tzname())
                    element = SplatoonRotation(start_time, mode_type, session)
                    element.mode = "Salmon Run"
                    element.start_time = start_time
                    element.end_time = datetime.fromtimestamp(sr_schedule["end_time"], time.tzname())
                    schedule_list.append(element)
        return schedule_list

    @staticmethod
    def format_time(time: datetime):
        # returns <hour>:<time> <am/pm>
        return time.strftime("%I:%M %p")

    @staticmethod
    def format_time_sr(time: datetime):
        # returns <abbr. weekday> <abbr. month> <date> <hour>:<time> <am/pm>
        return time.strftime("%a %b %d %I:%M %p")

    @staticmethod
    def format_time_sch(time: datetime):
        # returns <hour> <am/pm>
        return time.strftime("%-I %p")

    @staticmethod
    def print_sr_weapons(weapons_array: LinkedList):
        # Used to print out salmon run weapons
        weapon_list_str = ""
        for weapon in weapons_array:
            # we split based off SR_TERM_CHAR: <weapon name>SR_TERM_CHAR<weapon id>
            weapon_name = weapon.split(SR_TERM_CHAR)[0]
            weapon_id = weapon.split(SR_TERM_CHAR)[1]
            weapon_list_str += gen_emote_id(weapon_id) + " " + weapon_name + "\n"
        return weapon_list_str

