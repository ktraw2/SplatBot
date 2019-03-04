import discord
import asyncio
import config
from collections import namedtuple
from datetime import datetime, timedelta
from dateutil.parser import parse
from discord.ext import commands
from modules.linked_list import LinkedList
from modules.splatoon_schedule import SplatoonSchedule, ModeTypes
from misc_date_utilities.date_difference import DateDifference

# constants for arguments
NUM_PLAYERS = 2
TIME = 1
NAME = 0

# define lobby namedtuple
LobbyData = namedtuple("LobbyData", ["players", "metadata"])


class Lobby:
    """
    Defines commands for the lobby system of SplatBot.
    """

    def __init__(self, bot):
        """
        Initializes the reference to the bot, an empty lobbies list, and creates a notifications task
        :param bot: reference to the bot that created this cog
        """
        self.bot = bot
        self.lobbies = []

        # register notification task
        bot.loop.create_task(self.send_notifications())

    async def send_notifications(self):
        """
        Check if any lobbies need to have their notifications sent, also deletes old lobbies automatically.
        :return: Nothing
        """

        # wait for the bot to be ready, then loop while the bot is running
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # loop through all lobbies
            for lobby in self.lobbies:
                difference = DateDifference.subtract_datetimes(lobby.metadata["time"], datetime.now())
                # notify if less than zero and not notified
                if not lobby.metadata["notified"] and difference <= DateDifference():
                    # build and send the notification
                    announcement = "Hey "
                    for i, player in enumerate(lobby.players):
                        announcement += player.mention
                        if i < len(lobby.players) - 1:
                            announcement += ", "
                        if i == len(lobby.players) - 2 and len(lobby.players) > 1:
                            announcement += "and "
                    announcement += " it's time for your scheduled lobby: `" + lobby.metadata["name"] + "`!"
                    await lobby.metadata["channel"].send(announcement)
                    await lobby.metadata["channel"].send(embed=Lobby.generate_lobby_embed(lobby))
                    lobby.metadata["notified"] = True
                # code to clean up old notifications
                elif lobby.metadata["notified"]:
                    if lobby.metadata["schedule_data"] is not None:
                        end_difference = DateDifference.subtract_datetimes(lobby.metadata["schedule_data"].end_time,
                                                                           datetime.now())
                        # delete league lobby if the rotation ends
                        if lobby.metadata["schedule_data"].schedule_type == ModeTypes.LEAGUE and \
                           end_difference <= DateDifference():
                            self.lobbies.remove(lobby)
                    else:
                        # use 1 hour as default autodeletion time
                        end_difference = DateDifference.subtract_datetimes(lobby.metadata["time"],
                                                                           datetime.now() + timedelta(hours=1))
                        if end_difference <= DateDifference(hours=-1):
                            self.lobbies.remove(lobby)
            # sleep until the next minute
            sleep_time = datetime.now()
            sleep_time += timedelta(seconds=60 - sleep_time.second)
            await asyncio.sleep(sleep_time.second)

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def lobby(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is None:
            await ctx.send("Available lobby commands are: `create`, `edit`, `join`, `leave`, `end`")
        else:
            await ctx.send(embed=Lobby.generate_lobby_embed(lobby))

    @lobby.command(aliases=["start"])
    async def create(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is None:
            # default argument values
            name = "Splatoon Lobby"
            num_players = 4

            # default time is the next hour
            time = datetime.now()
            time += timedelta(minutes=60 - time.minute)

            # get arguments if they exist
            if len(args) >= NAME + 1:
                name = args[NAME]
                lobby_type = Lobby.parse_special_lobby_type(name)
                if lobby_type == ModeTypes.LEAGUE:
                    name = "League Battle"
                elif lobby_type == ModeTypes.SALMON:
                    name = "Salmon Run"
                else:
                    lobby_type = ModeTypes.PRIVATE
                    name = "Private Battle"
                    num_players = 8
                    await ctx.send(":warning: No lobby name, defaulting to " + name + ".")
            if len(args) >= NUM_PLAYERS + 1:
                try:
                    num_players = int(args[NUM_PLAYERS])
                except ValueError as e:
                    await ctx.send(":warning: You gave an invalid number of players, defaulting to " + str(num_players)
                                   + " players.")
            if len(args) >= TIME + 1:
                try:
                    time = parse(args[TIME])
                    # if the time has already happened, delay the lobby start time to the next day
                    if DateDifference.subtract_datetimes(time, datetime.now()) <= DateDifference(0):
                        time = time + timedelta(days=1)
                except ValueError as e:
                    await ctx.send(":warning: You gave an invalid lobby time, defaulting to the next hour.")

            # handle extra data for league battle
            if lobby_type == ModeTypes.LEAGUE:
                league = await Lobby.generate_league(name, time, self.bot.session)
            elif lobby_type == ModeTypes.SALMON:
                league = await Lobby.generate_salmon(name, time, self.bot.session)

            # add the lobby to the list
            lobby = LobbyData(LinkedList(),
                              {"channel": ctx.channel,
                               "name": name,
                               "schedule_data": league,
                               "num_players": num_players,
                               "time": time,
                               "notified": False})
            self.lobbies.append(lobby)
            await ctx.send(":white_check_mark: Created a lobby in " + ctx.channel.mention)
            await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
        else:
            await ctx.send(":x: A lobby already exists in " + ctx.channel.mention)

    @lobby.command(aliases=["add"])
    async def join(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is not None:
            if ctx.author not in lobby.players:
                if lobby.players.size < lobby.metadata["num_players"]:
                    lobby.players.add(ctx.author, prevent_duplicates=True)
                    await ctx.send(":white_check_mark: Successfully added " + ctx.author.mention + " to the lobby.")
                    await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
                else:
                    await ctx.send(":x: This lobby is full.")
            else:
                await ctx.send(":x: You are already in this lobby.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @lobby.command(aliases=["remove"])
    async def leave(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is not None:
            if lobby.players.remove_object(ctx.author):
                await ctx.send(":white_check_mark: Successfully removed " + ctx.author.mention + " from the lobby.")
                await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
            else:
                await ctx.send(":x: You are not currently in this lobby.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @lobby.group(case_insensitive=True, invoke_without_command=True)
    async def edit(self, ctx, *args):
        await ctx.send("Available edit commands are: name, players, time")

    @edit.command(aliases=["title", "lobbyname", "lobbytitle"])
    async def name(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is not None:
            if len(args) > 0:
                if "name" in lobby.metadata:
                    # add or remove custom battle data if necessary
                    lobby_type = Lobby.parse_special_lobby_type(args[0])
                    if lobby_type == ModeTypes.LEAGUE:
                        lobby.metadata["name"] = "League Battle"
                        lobby.metadata["schedule_data"] = await Lobby.generate_league(args[0], lobby.metadata["time"],
                                                                                self.bot.session)
                        Lobby.attempt_update_num_players(lobby, 4)
                    elif lobby_type == ModeTypes.SALMON:
                        lobby.metadata["name"] = "Salmon Run"
                        lobby.metadata["schedule_data"] = await Lobby.generate_salmon(args[0], lobby.metadata["time"],
                                                                                self.bot.session)
                        Lobby.attempt_update_num_players(lobby, 4)
                    elif lobby_type == ModeTypes.PRIVATE:
                        lobby.metadata["name"] = "Private Battle"
                        lobby.metadata["schedule_data"] = None
                        Lobby.attempt_update_num_players(lobby, 8)
                    else:
                        lobby.metadata["name"] = args[0]
                        lobby.metadata["schedule_data"] = None

                    await ctx.send(":white_check_mark: Successfully changed the lobby name.")
                    await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
            else:
                await ctx.send(":x: Please give a lobby name.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @edit.command(aliases=["num", "numplayers", "num_players"])
    async def players(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is not None:
            if len(args) > 0:
                if "num_players" in lobby.metadata:
                    old_num = lobby.metadata["num_players"]
                    try:
                        new_num = int(args[0])
                        if new_num >= lobby.players.size:
                            lobby.metadata["num_players"] = int(args[0])
                        else:
                            await ctx.send(":x: You cannot set the number of players to a number that is lower than the"
                                           " amount of players that are currently in the lobby.")
                            return
                    except ValueError as e:
                        await ctx.send(":x: You gave an invalid number of players.")
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
        lobby = self.find_lobby(ctx.channel)
        if lobby is not None:
            if len(args) > 0:
                if "time" in lobby.metadata:
                    old_time = lobby.metadata["time"]
                    try:
                        time = parse(args[0])
                        # if the time has already happened, delay the lobby start time to the next day
                        if DateDifference.subtract_datetimes(time, datetime.now()) <= DateDifference(0):
                            time = time + timedelta(days=1)
                        lobby.metadata["time"] = time
                    except ValueError as e:
                        await ctx.send(":x: You gave an invalid start time.")
                        lobby.metadata["time"] = old_time
                        return

                    await ctx.send(":white_check_mark: Successfully changed the start time.")
                    await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
            else:
                await ctx.send(":x: Please give a time.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @lobby.command(aliases=["end"])
    async def delete(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is not None:
            self.lobbies.remove(lobby)
            await ctx.send(":white_check_mark: Deleted the lobby from " + ctx.channel.mention)
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    def find_lobby(self, channel):
        for lobby in self.lobbies:
            if "channel" in lobby.metadata and lobby.metadata["channel"].id == channel.id:
                return lobby
        return None

    @staticmethod
    def generate_lobby_embed(lobby: LobbyData):
        metadata = lobby.metadata
        name = metadata["name"]

        lobby_embed = discord.Embed(title="Lobby Information - " + name, color=config.embed_color)
        lobby_embed.set_thumbnail(url=config.images["default"])

        lobby_type = Lobby.parse_special_lobby_type(name)
        # add data for league
        if lobby_type == ModeTypes.LEAGUE and "schedule_data" in metadata and metadata["schedule_data"] is not None:
            lobby_embed.set_thumbnail(url=config.images["league"])
            lobby_embed.set_image(url=metadata["schedule_data"].stage_a_image)
            lobby_embed.add_field(name="Mode", value=metadata["schedule_data"].mode)
            lobby_embed.add_field(name="Maps", value=metadata["schedule_data"].stage_a + "\n" +
                                                     metadata["schedule_data"].stage_b)
            lobby_embed.add_field(name="Rotation Time",
                                  value=SplatoonSchedule.format_time(metadata["schedule_data"].start_time) + " - "
                                  + SplatoonSchedule.format_time(metadata["schedule_data"].end_time))
        elif lobby_type == ModeTypes.SALMON and "schedule_data" in metadata and metadata["schedule_data"] is not None:
            lobby_embed.set_thumbnail(url=config.images["salmon"])
            weapons_str = "*Not released yet*"
            map_str = "Not released yet*"
            # Checking if weapons and map have been released yet
            if metadata["schedule_data"].stage_a is not None:
                weapons_str = metadata["schedule_data"].weapons_array[0] + "\n" + \
                                    metadata["schedule_data"].weapons_array[1] + "\n" + \
                                    metadata["schedule_data"].weapons_array[2] + "\n" + \
                                    metadata["schedule_data"].weapons_array[3]
                map_str = metadata["schedule_data"].stage_a

            lobby_embed.set_image(url=metadata["schedule_data"].stage_a_image)
            lobby_embed.add_field(name="Mode", value=metadata["schedule_data"].mode)
            lobby_embed.add_field(name="Maps", value=map_str)
            lobby_embed.add_field(name="Rotation Time",
                                    value=SplatoonSchedule.format_time_sr(metadata["schedule_data"].start_time) + " - "
                                    + SplatoonSchedule.format_time_sr(metadata["schedule_data"].end_time))
            lobby_embed.add_field(name="Weapons", value=weapons_str)
        elif lobby_type == ModeTypes.PRIVATE:
            lobby_embed.set_thumbnail(url=config.images["private_battle"])

        # add rest of data
        if "num_players" in metadata:
            lobby_embed.add_field(name="Number of Players", value=str(metadata["num_players"]))
        if "time" in metadata:
            lobby_embed.add_field(name="Lobby Start Time", value=SplatoonSchedule.format_time(metadata["time"]))

        # add list of players
        i = 0
        player_string = ""
        for player in lobby.players:
            player_string = player_string + str(i + 1) + ". " + player.mention + "\n"
            i += 1
        # now, add all the blank spots
        while i < metadata["num_players"]:
            player_string = player_string + str(i + 1) + ". Empty\n"
            i += 1
        lobby_embed.add_field(name="Players", value=player_string)

        return lobby_embed

    @staticmethod
    def attempt_update_num_players(lobby: LobbyData, new_num: int):
        if len(lobby.players) < new_num:
            lobby.metadata["num_players"] = new_num

    @staticmethod
    def parse_special_lobby_type(name: str):
        if "private" in name.lower():
            return ModeTypes.PRIVATE
        elif "league" in name.lower():
            return ModeTypes.LEAGUE
        elif "salmon" in name.lower():
            return ModeTypes.SALMON
        else:
            return None

    @staticmethod
    async def generate_league(name: str, time: datetime = datetime.now(), session=None):
        lobby_type = Lobby.parse_special_lobby_type(name)
        if lobby_type == ModeTypes.LEAGUE:
            league = SplatoonSchedule(time, ModeTypes.LEAGUE, session)
            success = await league.populate_data()
            if success:
                return league
        return None

    @staticmethod
    async def generate_salmon(name: str, time: datetime = datetime.now(), session=None):
        lobby_type = Lobby.parse_special_lobby_type(name)
        if lobby_type == ModeTypes.SALMON:
            salmon = SplatoonSchedule(time, ModeTypes.SALMON, session)
            success = await salmon.populate_data()
            if success:
                return salmon
        return None



def setup(bot):
    bot.add_cog(Lobby(bot))
