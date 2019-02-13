from datetime import datetime, timedelta


class League:
    def __init__(self, mode, map1, map2, start_time: datetime):
        self.mode = mode
        self.map1 = map1
        self.map2 = map2
        self.start_time = start_time
        self.end_time = start_time + timedelta(hours=2)
