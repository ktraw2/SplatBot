from modules.linked_list import LinkedList


class LobbyData:
    def __init__(self, players: LinkedList, channel, name: str, rotation_data, num_players: int, time, notified: bool):
        self.players = players
        self.channel = channel.id
        self.channel_mention = channel.mention
        self.name = name
        self.rotation_data = rotation_data
        self.num_players = num_players
        self.time = time
        self.notified = notified


class DiscordUser:
    def __init__(self, user):
        self.mention = user.mention

    def __eq__(self, other):
        return self.mention == other.mention
