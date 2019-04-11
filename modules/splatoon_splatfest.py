from enum import Enum, auto
from modules.splatnet import Splatnet
from datetime import datetime
from modules.linked_list import LinkedList

IMAGE_BASE = "https://splatoon2.ink/assets/splatnet"


class SplatfestWinner(Enum):
    ALPHA = auto()
    BRAVO = auto()


class SplatoonSplatfest:
    def __init__(self, target_time: datetime, session=None):
        self.cover_image = None
        self.alpha_name = None
        self.bravo_name = None
        self.start_time = None
        self.end_time = None
        self.votes = None
        self.normal = None
        self.pro = None

        self.target_time = target_time
        self.session = session

    """
    Populates the class variables in the SplatoonSplatfest object. 
    Will populate the variables via a requested time from the constructor.
    
    Return Value: False if the requested time was not able to be found.
                  True if the requested time was able to be found.
                  
    Parameters: None
    """
    async def populate_data_time(self):
        sn = Splatnet(self.session)
        timestamp = self.target_time.timestamp()
        data = await sn.get_na_splatfest()
        splatfest_counter = 0

        if data is None:
            raise Exception("Splatnet call failed.")

        for splatfest in data["festivals"]:
            if splatfest["times"]["start"] <= timestamp < splatfest["times"]["end"]:
                self.cover_image = IMAGE_BASE + splatfest["images"]["panel"]
                self.alpha_name = splatfest["names"]["alpha_short"]
                self.bravo_name = splatfest["names"]["bravo_short"]
                self.start_time = datetime.fromtimestamp(splatfest["times"]["start"], self.target_time.tzname())
                self.end_time = datetime.fromtimestamp(splatfest["times"]["end"], self.target_time.tzname())
            else:
                splatfest_counter = splatfest_counter + 1

        # Checking to see if splatfest has ended to populate votes info
        if self.target_time.timestamp() > splatfest["times"]["end"] and \
                len(data["festivals"]) == len(data["results"]):
            results = data["results"][splatfest_counter]

            if results["rates"]["vote"]["alpha"] > results["rates"]["vote"]["bravo"]:
                self.votes = SplatfestWinner.ALPHA
            else:
                self.votes = SplatfestWinner.BRAVO

            if results["rates"]["challenge"]["alpha"] > results["rates"]["challenge"]["bravo"]:
                self.pro = SplatfestWinner.ALPHA
            else:
                self.pro = SplatfestWinner.BRAVO

            if results["rates"]["regular"]["alpha"] > results["rates"]["regular"]["bravo"]:
                self.normal = SplatfestWinner.ALPHA
            else:
                self.normal = SplatfestWinner.BRAVO
            return True  # Return true, we populated it all

        # If the object was populated, return true
        if self.cover_image is not None:
            return True

        # Otherwise return false
        return False

    """
    Populates the class variables in the SplatoonSplatfest object. 
    Will populate the variables via a given Splatfest name from the constructor.
    
    Return Value: False if the requested time was not able to be found.
                  True if the requested time was able to be found.
    """
    async def populate_data_name(self, target_str: str):
        sn = Splatnet(self.session)
        data = await sn.get_na_splatfest()
        splatfest_counter = 0

        if data is None:
            raise Exception("Splatnet call failed.")

        for splatfest in data["festivals"]:
            alpha_name = splatfest["names"]["alpha_short"]
            bravo_name = splatfest["names"]["bravo_short"]

            if alpha_name == target_str or bravo_name == target_str:
                self.cover_image = IMAGE_BASE + splatfest["images"]["panel"]
                self.alpha_name = alpha_name
                self.bravo_name = bravo_name
                self.start_time = datetime.fromtimestamp(splatfest["times"]["start"], self.target_time.tzname())
                self.end_time = datetime.fromtimestamp(splatfest["times"]["end"], self.target_time.tzname())
            else:
                splatfest_counter = splatfest_counter + 1

        if self.cover_image is None:
            return False

        # Checking to see if splatfest has ended to populate votes info
        if self.target_time.timestamp() > splatfest["times"]["end"] and \
                len(data["festivals"]) == len(data["results"]):
            results = data["results"][splatfest_counter]

            if results["rates"]["vote"]["alpha"] > results["rates"]["vote"]["bravo"]:
                self.votes = SplatfestWinner.ALPHA
            else:
                self.votes = SplatfestWinner.BRAVO

            if results["rates"]["challenge"]["alpha"] > results["rates"]["challenge"]["bravo"]:
                self.pro = SplatfestWinner.ALPHA
            else:
                self.pro = SplatfestWinner.BRAVO

            if results["rates"]["regular"]["alpha"] > results["rates"]["regular"]["bravo"]:
                self.normal = SplatfestWinner.ALPHA
            else:
                self.normal = SplatfestWinner.BRAVO
            return True  # Return true, we populated it all

        # If the object was populated, return true
        if self.cover_image is not None:
            return True

        # Otherwise return false
        return False


    @staticmethod
    async def get_all_rotations(time: datetime, session=None):
        sn = Splatnet(session)
        data = await sn.get_na_splatfest()

        splatfest_list = []
        splatfest_counter = 0

        if data is None:
            raise Exception("Splatnet call failed.")

        for schedule in data["festivals"]:
            start_time = datetime.fromtimestamp(schedule["times"]["start"], time.tzname())
            element = SplatoonSplatfest(start_time, session)
            element.cover_image = IMAGE_BASE + schedule["images"]["panel"]
            element.alpha_name = schedule["names"]["alpha_short"]
            element.bravo_name = schedule["names"]["bravo_short"]
            element.start_time = start_time
            element.end_time = datetime.fromtimestamp(schedule["times"]["end"], time.tzname())

            if time.timestamp() < schedule["times"]["end"]:
                results = data["results"][splatfest_counter]

                if results["rates"]["vote"]["alpha"] > results["rates"]["vote"]["bravo"]:
                    element.votes = SplatfestWinner.ALPHA
                else:
                    element.votes = SplatfestWinner.BRAVO

                if results["rates"]["challenge"]["alpha"] > results["rates"]["challenge"]["bravo"]:
                    element.pro = SplatfestWinner.ALPHA
                else:
                    element.pro = SplatfestWinner.BRAVO

                if results["rates"]["regular"]["alpha"] > results["rates"]["regular"]["bravo"]:
                    element.normal = SplatfestWinner.ALPHA
                else:
                    element.normal = SplatfestWinner.BRAVO

            splatfest_list.append(element)
            splatfest_counter = splatfest_counter + 1

        return splatfest_list
