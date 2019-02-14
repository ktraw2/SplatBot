import discord
import config
from datetime import datetime, timedelta
from dateutil.parser import parse
from discord.ext import commands
from modules.queue_data import Queue_Data
from modules.league import League

# constants for arguments
NUM_PLAYERS = 0
TIME = 1
TITLE = 2


class Lobby:
    def __init__(self, bot):
        self.bot = bot
        self.lobbies = []

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def lobby(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel.id)
        if lobby is None:
            await ctx.send("Available lobby commands are: start, add, remove, end")
        else:
            await ctx.send(embed=Lobby.generate_lobby_embed(lobby))

    @lobby.command(aliases=["create"])
    async def start(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel.id)
        if lobby is None:
            # default argument values
            title = "Splatoon Lobby"
            num_players = 4

            # default time is the next hour
            time = datetime.now()
            time += timedelta(minutes=60 - time.minute)

            # get arguments if they exist
            if len(args) >= TITLE + 1:
                title = args[TITLE]
            if len(args) >= NUM_PLAYERS + 1:
                try:
                    num_players = int(args[NUM_PLAYERS])
                except ValueError as e:
                    await ctx.send(":warning: You gave an invalid number of players, defaulting to 4 players.")
            if len(args) >= TIME + 1:
                try:
                    time = parse(args[TIME])
                except ValueError as e:
                    await ctx.send(":warning: You gave an invalid lobby time, defaulting to the next hour.")

            # handle extra data for league battle
            league = Lobby.generate_league(title, time)

            # add the lobby to the list
            lobby = Queue_Data(**{"channel": ctx.channel.id,
                                  "title": title,
                                  "league": league,
                                  "num_players": num_players,
                                  "time": time})
            self.lobbies.append(lobby)
            await ctx.send(":white_check_mark: Created a lobby in " + ctx.channel.mention)
            await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
        else:
            await ctx.send(":x: A lobby already exists in " + ctx.channel.mention)

    @lobby.command(aliases=["join"])
    async def add(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel.id)
        if lobby is not None:
            await ctx.send("DEBUG: queue size: " + str(lobby.queue.size) + "; max players: " + str(lobby.metadata["num_players"]))
            if lobby.queue.size < lobby.metadata["num_players"]:
                if lobby.queue.add(ctx.author, prevent_duplicates=True):
                    await ctx.send(":white_check_mark: Successfully added " + ctx.author.mention + " to the lobby.")
                    await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
                else:
                    await ctx.send(":x: You are already in this lobby.")
            else:
                await ctx.send(":x: This lobby is full.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @lobby.command()
    async def remove(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel.id)
        if lobby is not None:
            if lobby.queue.remove_by_key(ctx.author):
                await ctx.send(":white_check_mark: Successfully removed " + ctx.author.mention + " from the lobby.")
                await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
            else:
                await ctx.send(":x: You are not currently in this lobby.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @lobby.group(case_insensitive=True, invoke_without_command=True)
    async def edit(self, ctx, *args):
        pass

    @edit.command(aliases=["name", "lobbytitle"])
    async def title(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel.id)
        if lobby is not None:
            if len(args) > 0:
                if "title" in lobby.metadata:
                    lobby.metadata["title"] = args[0]
                    # add or remove league battle data if necessary
                    if "league" in lobby.metadata:
                        lobby.metadata["league"] = Lobby.generate_league(args[0])

                    await ctx.send(":white_check_mark: Successfully changed the lobby title.")
                    await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
            else:
                await ctx.send(":x: Please give a lobby title.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @edit.command(aliases=["num", "numplayers", "num_players"])
    async def players(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel.id)
        if lobby is not None:
            if len(args) > 0:
                if "num_players" in lobby.metadata:
                    old_num = lobby.metadata["num_players"]
                    try:
                        lobby.metadata["num_players"] = int(args[0])
                    except ValueError as e:
                        await ctx.send(":warning: You gave an invalid number of players.")
                        lobby.metadata["num_players"] = old_num
                        return

                    await ctx.send(":white_check_mark: Successfully changed the number of players.")
                    await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
            else:
                await ctx.send(":x: Please give a number.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @edit.command(aliases=["start", "starttime"])
    async def time(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel.id)
        if lobby is not None:
            if len(args) > 0:
                if "time" in lobby.metadata:
                    old_time = lobby.metadata["time"]
                    try:
                        lobby.metadata["time"] = parse(args[0])
                    except ValueError as e:
                        await ctx.send(":warning: You gave an invalid start time.")
                        lobby.metadata["time"] = old_time
                        return

                    await ctx.send(":white_check_mark: Successfully changed the start time.")
                    await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
            else:
                await ctx.send(":x: Please give a time.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @lobby.command(aliases=["delete"])
    async def end(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel.id)
        if lobby is not None:
            self.lobbies.remove(lobby)
            await ctx.send(":white_check_mark: Deleted the lobby from " + ctx.channel.mention)
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    def find_lobby(self, channel):
        for lobby in self.lobbies:
            if "channel" in lobby.metadata and lobby.metadata["channel"] == channel:
                return lobby
        return None

    @staticmethod
    def generate_lobby_embed(lobby: Queue_Data):
        title = "Splatoon Lobby"
        metadata = lobby.metadata
        if "title" in metadata:
            if Lobby.is_league(metadata["title"]):
                title = "League Battle"
            else:
                title = metadata["title"]

        lobby_embed = discord.Embed(title="Lobby Information - " + title, color=config.embed_color)

        # add data for league
        if "league" in metadata and metadata["league"] is not None:
            lobby_embed.add_field(name="Mode", value=metadata["league"].mode)
            lobby_embed.add_field(name="Maps", value=metadata["league"].map1 + "\n" + metadata["league"].map2)
            lobby_embed.add_field(name="Rotation Time", value=Lobby.format_time(metadata["league"].start_time) + " - "
                                  + Lobby.format_time(metadata["league"].end_time))
        # add rest of data
        if "num_players" in metadata:
            lobby_embed.add_field(name="Number of Players", value=str(metadata["num_players"]))
        if "time" in metadata:
            lobby_embed.add_field(name="Start Time", value=Lobby.format_time(metadata["time"]))

        # add list of players
        i = 0
        player_string = ""
        for player in lobby.queue:
            player_string = player_string + str(i + 1) + ". " + player.mention + "\n"
            i += 1
        # now, add all the blank spots
        while i < metadata["num_players"]:
            player_string = player_string + str(i + 1) + ". Empty\n"
            i += 1
        lobby_embed.add_field(name="Players", value=player_string)

        return lobby_embed

    @staticmethod
    def is_league(title: str):
        if title.lower() == "league" or title.lower == "league battle":
            return True
        else:
            return False

    @staticmethod
    def generate_league(title: str, time: datetime = datetime.now()):
        if Lobby.is_league(title):
            return League("Test Mode", "Test Map 1", "Test Map 2", time)
        else:
            return None

    @staticmethod
    def format_time(time: datetime):
        return time.strftime("%I:%M %p")


def setup(bot):
    bot.add_cog(Lobby(bot))
