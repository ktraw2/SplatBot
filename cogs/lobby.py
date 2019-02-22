import discord
import asyncio
import config
from datetime import datetime, timedelta
from dateutil.parser import parse
from discord.ext import commands
from modules.queue_data import QueueData
from modules.splatoon_schedule import SplatoonSchedule, ScheduleTypes
from misc_date_utilities.date_difference import DateDifference

# constants for arguments
NUM_PLAYERS = 2
TIME = 1
NAME = 0


class Lobby:
    def __init__(self, bot):
        self.bot = bot
        self.lobbies = []

        # register notification task
        bot.loop.create_task(self.send_notifications())

    async def send_notifications(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for lobby in self.lobbies:
                difference = DateDifference.subtract_datetimes(lobby.metadata["time"], datetime.now())
                # notify if less than zero and not notified
                if not lobby.metadata["notified"] and difference <= DateDifference():
                    announcement = "Hey "
                    for i, player in enumerate(lobby.queue):
                        announcement += player.mention
                        if i < len(lobby.queue) - 1:
                            announcement += ", "
                        if i == len(lobby.queue) - 2 and len(lobby.queue) > 1:
                            announcement += "and "
                    announcement += " it's time for your scheduled lobby: `" + lobby.metadata["name"] + "`!"
                    await lobby.metadata["channel"].send(announcement)
                    await lobby.metadata["channel"].send(embed=Lobby.generate_lobby_embed(lobby))
                    lobby.metadata["notified"] = True
            await asyncio.sleep(60)

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def lobby(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is None:
            await ctx.send("Available lobby commands are: create, edit, join, leave, end")
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
                if Lobby.is_league(name):
                    name = "League Battle"
                elif Lobby.is_private_battle(name):
                    name = "Private Battle"
                    num_players = 8
                elif Lobby.is_salmon_run(name):
                    name = "Salmon Run"
                    num_players = 4
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

            if Lobby.is_league(name):
                # handle extra data for league battle
                battle_lobby = await Lobby.generate_league(name, time, self.bot.session)
                # add the lobby to the list
                lobby = QueueData({"channel": ctx.channel,
                                  "name": name,
                                  "league": battle_lobby,
                                  "num_players": num_players,
                                  "time": time,
                                  "notified": False})
            elif Lobby.is_salmon_run(name):
                battle_lobby = await Lobby.generate_salmon(name, time, self.bot.session)
                # add the lobby to the list
                lobby = QueueData({"channel": ctx.channel,
                                  "name": name,
                                  "league": battle_lobby,
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
            if ctx.author not in lobby.queue:
                if lobby.queue.size < lobby.metadata["num_players"]:
                    lobby.queue.add(ctx.author, prevent_duplicates=True)
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
            if lobby.queue.remove_object(ctx.author):
                await ctx.send(":white_check_mark: Successfully removed " + ctx.author.mention + " from the lobby.")
                await ctx.send(embed=Lobby.generate_lobby_embed(lobby))
            else:
                await ctx.send(":x: You are not currently in this lobby.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @lobby.group(case_insensitive=True, invoke_without_command=True)
    async def edit(self, ctx, *args):
        pass

    @edit.command(aliases=["title", "lobbyname", "lobbytitle"])
    async def name(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is not None:
            if len(args) > 0:
                if "name" in lobby.metadata:
                    lobby.metadata["name"] = args[0]
                    # add or remove league battle data if necessary
                    if Lobby.is_league(args[0]):
                        lobby.metadata["league"] = await Lobby.generate_league(args[0], lobby.metadata["time"],
                                                                               self.bot.session)
                        lobby.metadata["name"] = "League Battle"
                    elif Lobby.is_salmon_run(args[0]):
                        lobby.metadata["league"] = await Lobby.generate_league(args[0], lobby.metadata["time"],
                                                                               self.bot.session)
                    else:
                        lobby.metadata["league"] = None

                    # set private battle title if necessary
                    if Lobby.is_private_battle(args[0]):
                        lobby.metadata["name"] = "Private Battle"
                    elif Lobby.is_salmon_run(args[0]):
                        lobby.metedata["name"] = "Salmon Run"

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
                        if new_num >= lobby.queue.size:
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

                    # update league battle rotation time
                    if lobby.metadata["league"] is not None:
                        lobby.metadata["league"] = await Lobby.generate_league(lobby.metadata["name"],
                                                                               lobby.metadata["time"], self.bot.session)
                    elif lobby.metadata["salmon"] is not None:
                        lobby.metadata["salmon"] = await Lobby.generate_salmon(lobby.metadata["name"],
                                                                               lobby.metadata["time"], self.bot.session)

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
    def generate_lobby_embed(lobby: QueueData):
        metadata = lobby.metadata
        name = metadata["name"]

        lobby_embed = discord.Embed(title="Lobby Information - " + name, color=config.embed_color)
        lobby_embed.set_thumbnail(url=config.images["default"])

        # add data for league
        if "league" in metadata and metadata["league"] is not None:
            lobby_embed.set_thumbnail(url=config.images["league"])
            lobby_embed.set_image(url=metadata["league"].stage_a_image)
            lobby_embed.add_field(name="Mode", value=metadata["league"].mode)
            lobby_embed.add_field(name="Maps", value=metadata["league"].stage_a + "\n" + metadata["league"].stage_b)
            lobby_embed.add_field(name="Rotation Time",
                                  value=SplatoonSchedule.format_time(metadata["league"].start_time) + " - "
                                  + SplatoonSchedule.format_time(metadata["league"].end_time))
        elif "salmon" in metadata and metadata["league"] is not None:
            lobby_embed.set_thumbnail(url=config.images["salmon"])
            lobby_embed.set_image(url=metadata["league"].stage_a_image)
            lobby_embed.add_field(name="Mode", value=metadata["league"].mode)
            lobby_embed.add_field(name="Maps", value=metadata["league"].stage_a)
            lobby_embed.add_field(name="Rotation Time",
                                  value=SplatoonSchedule.format_time_sr(metadata["league"].start_time) + " - "
                                  + SplatoonSchedule.format_time_sr(metadata["league"].end_time))

        # add rest of data
        if Lobby.is_private_battle(name):
            lobby_embed.set_thumbnail(url=config.images["private_battle"])
        elif Lobby.is_salmon_run(name):
            lobby_embed.set_thumbnail(url=config.images["salmon_run"])

        if "num_players" in metadata:
            lobby_embed.add_field(name="Number of Players", value=str(metadata["num_players"]))
        if "time" in metadata:
            lobby_embed.add_field(name="Lobby Start Time", value=SplatoonSchedule.format_time(metadata["time"]))

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
    def is_league(name: str):
        if "league" in name.lower():
            return True
        else:
            return False

    @staticmethod
    def is_private_battle(name: str):
        if "private" in name.lower():
            return True
        else:
            return False

    @staticmethod
    def is_salmon_run(name: str):
        if "salmon" in name.lower():
            return True
        else:
            return False

    @staticmethod
    async def generate_league(name: str, time: datetime = datetime.now(), session=None):
        if Lobby.is_league(name):
            league = SplatoonSchedule(time, ScheduleTypes.LEAGUE, session)
            success = await league.populate_data()
            if success:
                return league
        return None

    @staticmethod
    async def generate_salmon(name: str, time: datetime = datetime.now(), session=None):
        if Lobby.is_salmon_run(name):
            league = SplatoonSchedule(time, ScheduleTypes.SALMON, session)
            success = await league.populate_data()
            if success:
                return league
        return None


def setup(bot):
    bot.add_cog(Lobby(bot))
