class LobbyData:
    def __init__(self, players, metadata):
        self.players = players
        self.metadata = metadata


class DiscordChannel:
    def __init__(self, channel):
        self.id = channel.id
        self.mention = channel.mention


class DiscordUser:
    def __init__(self, user):
        self.mention = user.mention

    def __eq__(self, other):
        return self.mention == other.mention
