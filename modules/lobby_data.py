import pickle
from datetime import datetime
from modules.linked_list import LinkedList
from modules.splatoon_rotation import SplatoonRotation


class LobbyData:
    def __init__(self, players: LinkedList, channel: int, name: str, rotation_data: SplatoonRotation, num_players: int, time: datetime, notified: bool, database):
        self._players = players
        self._channel = channel
        self._channel_mention = "<#" + str(self.channel) + ">"
        self._name = name
        self._rotation_data = rotation_data
        self._num_players = num_players
        self._time = time
        self._notified = notified
        self.database = database

    def commit_players(self):
        if self.database is not None:
            self.database.update_lobby_row(self.channel, "players", pickle.dumps(self.players))

    @property
    def players(self):
        return self._players

    @players.setter
    def players(self, value):
        self._players = value
        self.commit_players()

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        self._channel = value
        if self.database is not None:
            self.database.update_lobby_row(self.channel, "channelID", self.channel)

    @property
    def channel_mention(self):
        return self._channel_mention

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        if self.database is not None:
            self.database.update_lobby_row(self.channel, "lobbyName", self.name)

    @property
    def rotation_data(self):
        return self._rotation_data

    @rotation_data.setter
    def rotation_data(self, value):
        self._rotation_data = value
        if self.database is not None:
            self.database.update_lobby_row(self.channel, "rotationData", pickle.dumps(self.rotation_data))

    @property
    def num_players(self):
        return self._num_players

    @num_players.setter
    def num_players(self, value):
        self._num_players = value
        if self.database is not None:
            self.database.update_lobby_row(self.channel, "numPlayers", self.num_players)

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._time = value
        if self.database is not None:
            self.database.update_lobby_row(self.channel, "lobbyTime", self.time.timestamp())

    @property
    def notified(self):
        return self._notified

    @notified.setter
    def notified(self, value):
        self._notified = value
        if self.database is not None:
            self.database.update_lobby_row(self.channel, "notified", self.notified)


class DiscordUser:
    def __init__(self, user):
        self.mention = user.mention

    def __eq__(self, other):
        return self.mention == other.mention
