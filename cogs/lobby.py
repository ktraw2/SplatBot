import discord
import asyncio
import pickle
import config
from modules.lobby_data import LobbyData, DiscordChannel, DiscordUser
from datetime import datetime, timedelta
from dateutil.parser import parse
from discord.ext import commands
from modules import checks
from modules.linked_list import LinkedList
from modules.splatoon_rotation import SplatoonRotation, ModeTypes
from modules.gif_generator import generate_gif
from misc_date_utilities.date_difference import DateDifference

# constants for arguments
NUM_PLAYERS = 2
TIME = 1
NAME = 0





# define lobbydata
# LobbyData = namedtuple("LobbyData", ["players", "metadata"])
# add it to globals
# globals()[LobbyData.__name__] = LobbyData


class Lobby(commands.Cog):
    """
    Defines commands for the lobby system of SplatBot.
    """

    def __init__(self, bot):
        """
        Initializes the reference to the bot, an empty lobbies list, and creates a notifications task
        :param bot: reference to the bot that created this cog
        """
        self.bot = bot

        # initialize lobbies from serialized data
        checks.make_sure_file_exists("lobbies.pickle", pickle.dumps([]))

        with open("lobbies.pickle", "rb") as lobbypickle:
            self.lobbies = pickle.load(lobbypickle)

        # register notification task
        bot.loop.create_task(self.send_notifications())

    def __del__(self):
        """
        Cleans up by writing out lobbies to disk.
        """
        with open("lobbies.pickle", "wb") as lobbypickle:
            try:
                pickle.dump(self.lobbies, lobbypickle)
            except pickle.PicklingError:
                print("An error occurred! Writing empty list.")
                lobbypickle.write(pickle.dumps([]))

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
                    announcement = "Hey"
                    if len(lobby.players) > 0:  # if there's no players, don't add a space for formatting
                        announcement = announcement + " "
                    for i, player in enumerate(lobby.players):
                        announcement += player.mention
                        if i < len(lobby.players) - 1:
                            announcement += ", "
                        if i == len(lobby.players) - 2 and len(lobby.players) > 1:
                            announcement += "and "
                    announcement += " it's time for your scheduled lobby: `" + lobby.metadata["name"] + "`!"
                    await self.bot.get_channel(lobby.metadata["channel"].id).send(announcement)

                    # making and sending if applicable
                    embed, file = await Lobby.attach_gif(embed=Lobby.generate_lobby_embed(lobby), lobby=lobby,
                                                         channel_id=str(lobby.metadata["channel"].id))
                    if file is not None:
                        await self.bot.get_channel(lobby.metadata["channel"].id).send(
                            embed=embed,file=file)
                    else:
                        await self.bot.get_channel(lobby.metadata["channel"].id).send(
                            embed=Lobby.generate_lobby_embed(lobby))
                    lobby.metadata["notified"] = True
                # code to clean up old notifications
                elif lobby.metadata["notified"]:

                    if lobby.metadata["rotation_data"] is not None and \
                            lobby.metadata["rotation_data"].mode_type == ModeTypes.LEAGUE:
                        # delete league lobby when rotation ends
                        delete_delay_hours = 0
                        end_difference = DateDifference.subtract_datetimes(lobby.metadata["rotation_data"].end_time,
                                                                           datetime.now() +
                                                                           timedelta(hours=delete_delay_hours))
                    else:
                        delete_delay_hours = 1  # use 1 hour as the default autodeletion time
                        end_difference = DateDifference.subtract_datetimes(lobby.metadata["time"],
                                                                           datetime.now())
                    # delete lobby if it is time
                    if end_difference <= DateDifference(hours=(-1 * delete_delay_hours)):
                        self.lobbies.remove(lobby)
            # sleep until the next minute
            sleep_time = datetime.now()
            sleep_time += timedelta(seconds=60 - sleep_time.second)
            await asyncio.sleep(sleep_time.second)

    @commands.group(case_insensitive=True, invoke_without_command=True, aliases=["l"])
    async def lobby(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is None:
            await ctx.send("Available lobby commands are: `create`, `edit`, `join`, `leave`, `end`")
        else:
            if lobby.metadata["rotation_data"] is None and Lobby.parse_special_lobby_type(lobby.metadata["name"]) is ModeTypes.SALMON:
                await Lobby.send_sal_err(ctx, lobby.metadata["time"], session=self.bot.session)
            elif lobby.metadata["rotation_data"].stage_a is None:
                await ctx.send(":warning: Detailed Salmon Run information not avaliable!")
            await ctx.send(embed=Lobby.generate_lobby_embed(lobby))

    @lobby.command(aliases=["start", "c"])
    async def create(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is None:
            # default argument values
            name = "Splatoon Lobby"
            num_players = 4
            lobby_type = None

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
                elif lobby_type == ModeTypes.REGULAR:
                    name = "Turf War"
                elif lobby_type == ModeTypes.PRIVATE:
                    name = "Private Battle"
                    num_players = 8

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

            # attach extra data if applicable
            if lobby_type is ModeTypes.LEAGUE:
                rotation = await Lobby.generate_league(name, time, self.bot.session)
            elif lobby_type is ModeTypes.SALMON:
                rotation = await Lobby.generate_salmon(name, time, self.bot.session)
                # checking if there is a salmon run rotation happening right now
                if rotation is None:
                    await Lobby.send_sal_err(ctx, time, session=self.bot.session)
            elif lobby_type is ModeTypes.REGULAR:
                rotation = await Lobby.generate_regular(name, time, self.bot.session)
            else:
                rotation = None

            # add the lobby to the list
            lobby = LobbyData(LinkedList(),
                              {"channel": DiscordChannel(ctx.channel),
                               "name": name,
                               "rotation_data": rotation,
                               "num_players": num_players,
                               "time": time,
                               "notified": False})
            self.lobbies.append(lobby)

            # generate and send off the embed
            await ctx.send(":white_check_mark: Created a lobby in " + ctx.channel.mention)
            await Lobby.attach_send_gif(embed=Lobby.generate_lobby_embed(lobby), lobby=lobby, ctx=ctx)
        else:
            await ctx.send(":x: A lobby already exists in " + ctx.channel.mention)

    @lobby.command(aliases=["add", "j"])
    async def join(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is not None:
            user = DiscordUser(ctx.author)
            if user not in lobby.players:
                if lobby.players.size < lobby.metadata["num_players"]:
                    lobby.players.add(user, prevent_duplicates=True)
                    await ctx.send(":white_check_mark: Successfully added " + user.mention + " to the lobby.")
                    await Lobby.attach_send_gif(embed=Lobby.generate_lobby_embed(lobby), lobby=lobby, ctx=ctx)
                else:
                    await ctx.send(":x: This lobby is full.")
            else:
                await ctx.send(":x: You are already in this lobby.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @lobby.command(aliases=["remove", "l", "r"])
    async def leave(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is not None:
            if lobby.players.remove_object(DiscordUser(ctx.author)):
                await ctx.send(":white_check_mark: Successfully removed " + ctx.author.mention + " from the lobby.")
                await Lobby.attach_send_gif(embed=Lobby.generate_lobby_embed(lobby), lobby=lobby, ctx=ctx)
            else:
                await ctx.send(":x: You are not currently in this lobby.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @lobby.group(case_insensitive=True, invoke_without_command=True, aliases=["e"])
    async def edit(self, ctx, *args):
        await ctx.send("Available edit commands are: name, players, time")

    @edit.command(aliases=["title", "lobbyname", "lobbytitle", "n"])
    async def name(self, ctx, *args):
        lobby = self.find_lobby(ctx.channel)
        if lobby is not None:
            if len(args) > 0:
                if "name" in lobby.metadata:
                    # add or remove custom battle data if necessary
                    lobby_type = Lobby.parse_special_lobby_type(args[0])
                    if lobby_type == ModeTypes.LEAGUE:
                        lobby.metadata["name"] = "League Battle"
                        lobby.metadata["rotation_data"] = await Lobby.generate_league(args[0], lobby.metadata["time"],
                                                                                self.bot.session)
                        Lobby.attempt_update_num_players(lobby, 4)
                    elif lobby_type == ModeTypes.SALMON:
                        lobby.metadata["name"] = "Salmon Run"
                        lobby.metadata["rotation_data"] = await Lobby.generate_salmon(args[0], lobby.metadata["time"],
                                                                                self.bot.session)
                        if lobby.metadata["rotation_data"] is None:
                            await Lobby.send_sal_err(ctx, lobby.metadata["time"], session=self.bot.session)
                        Lobby.attempt_update_num_players(lobby, 4)
                    elif lobby_type == ModeTypes.REGULAR:
                        lobby.metadata["name"] = "Turf War"
                        lobby.metadata["rotation_data"] = await Lobby.generate_regular(args[0], lobby.metadata["time"],
                                                                                self.bot.session)
                        Lobby.attempt_update_num_players(lobby, 4)
                    elif lobby_type == ModeTypes.PRIVATE:
                        lobby.metadata["name"] = "Private Battle"
                        lobby.metadata["rotation_data"] = None
                        Lobby.attempt_update_num_players(lobby, 8)

                    else:
                        lobby.metadata["name"] = args[0]
                        lobby.metadata["rotation_data"] = None

                    await ctx.send(":white_check_mark: Successfully changed the lobby name.")
                    await Lobby.attach_send_gif(embed=Lobby.generate_lobby_embed(lobby), lobby=lobby, ctx=ctx)
            else:
                await ctx.send(":x: Please give a lobby name.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @edit.command(aliases=["num", "numplayers", "num_players", "np"])
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
                    await Lobby.attach_send_gif(embed=Lobby.generate_lobby_embed(lobby), lobby=lobby, ctx=ctx)
            else:
                await ctx.send(":x: Please give a number.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @edit.command(aliases=["start", "starttime", "s"])
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
                        lobby.metadata["notified"] = False
                    except ValueError as e:
                        await ctx.send(":x: You gave an invalid start time.")
                        lobby.metadata["time"] = old_time
                        return
                    # update battle data dude to time change
                    lobby_type = Lobby.parse_special_lobby_type(lobby.metadata["name"])
                    if lobby_type == ModeTypes.LEAGUE:
                        lobby.metadata["rotation_data"] = await Lobby.generate_league(lobby.metadata["name"],
                                                                        lobby.metadata["time"], self.bot.session)
                    elif lobby_type == ModeTypes.SALMON:
                        lobby.metadata["rotation_data"] = await Lobby.generate_salmon(lobby.metadata["name"],
                                                                        lobby.metadata["time"], self.bot.session)
                        if lobby.metadata["rotation_data"] is None:
                            await Lobby.send_sal_err(ctx, lobby.metadata["time"], session=self.bot.session)
                        Lobby.attempt_update_num_players(lobby, 4)  # salmon can have a max of four players
                    elif lobby_type == ModeTypes.REGULAR:
                        lobby.metadata["rotation_data"] = await Lobby.generate_regular(lobby.metadata["name"],
                                                                        lobby.metadata["time"], self.bot.session)
                    else:
                        lobby.metadata["rotation_data"] = None
                    await ctx.send(":white_check_mark: Successfully changed the start time.")
                    await Lobby.attach_send_gif(embed=Lobby.generate_lobby_embed(lobby), lobby=lobby, ctx=ctx)
            else:
                await ctx.send(":x: Please give a time.")
        else:
            await ctx.send(":x: There is currently no active lobby in " + ctx.channel.mention)

    @lobby.command(aliases=["end", "d"])
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
        if lobby_type == ModeTypes.LEAGUE and "rotation_data" in metadata and metadata["rotation_data"] is not None:
            lobby_embed.set_thumbnail(url=config.images["league"])
            lobby_embed.set_image(url=metadata["rotation_data"].stage_a_image)
            lobby_embed.add_field(name="Mode", value=metadata["rotation_data"].mode)
            lobby_embed.add_field(name="Maps", value=metadata["rotation_data"].stage_a + "\n" +
                                                     metadata["rotation_data"].stage_b)
            lobby_embed.add_field(name="Rotation Time",
                                  value=SplatoonRotation.format_time(metadata["rotation_data"].start_time) + " - "
                                        + SplatoonRotation.format_time(metadata["rotation_data"].end_time))
        # add data for regular
        elif lobby_type == ModeTypes.REGULAR and "rotation_data" in metadata and metadata["rotation_data"] is not None:
            lobby_embed.set_thumbnail(url=config.images["default"])
            lobby_embed.set_image(url=metadata["rotation_data"].stage_a_image)
            lobby_embed.add_field(name="Mode", value=metadata["rotation_data"].mode)
            lobby_embed.add_field(name="Maps", value=metadata["rotation_data"].stage_a + "\n" +
                                                     metadata["rotation_data"].stage_b)
            lobby_embed.add_field(name="Rotation Time",
                                  value=SplatoonRotation.format_time(metadata["rotation_data"].start_time) + " - "
                                        + SplatoonRotation.format_time(metadata["rotation_data"].end_time))
        # add data for salmon
        elif lobby_type == ModeTypes.SALMON and "rotation_data" in metadata and metadata["rotation_data"] is not None:
            lobby_embed.set_thumbnail(url=config.images["salmon"])
            weapons_str = "*Not released yet*"
            map_str = "*Not released yet*"
            # Checking if weapons and map have been released yet
            if metadata["rotation_data"].stage_a is not None:
                weapons_str = SplatoonRotation.print_sr_weapons(metadata["rotation_data"].weapons_array)
                map_str = metadata["rotation_data"].stage_a
                lobby_embed.set_image(url=metadata["rotation_data"].stage_a_image)
            lobby_embed.add_field(name="Mode", value=metadata["rotation_data"].mode)
            lobby_embed.add_field(name="Map", value=map_str)
            lobby_embed.add_field(name="Rotation Time",
                                  value=SplatoonRotation.format_time_sr(metadata["rotation_data"].start_time) + " - "
                                        + SplatoonRotation.format_time_sr(metadata["rotation_data"].end_time))
            lobby_embed.add_field(name="Weapons", value=weapons_str)
        elif lobby_type == ModeTypes.PRIVATE:
            lobby_embed.set_thumbnail(url=config.images["private_battle"])
        # add rest of data
        if "num_players" in metadata:
            lobby_embed.add_field(name="Number of Players", value=str(metadata["num_players"]))
        if "time" in metadata:
            lobby_embed.add_field(name="Lobby Start Time", value=SplatoonRotation.format_time(metadata["time"]))

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
        if "private" in name.lower() or "pb" in name.lower():
            return ModeTypes.PRIVATE
        elif "league" in name.lower() or "leg" in name.lower():
            return ModeTypes.LEAGUE
        elif "salmon" in name.lower() or "sr" in name.lower() or "sal" in name.lower():
            return ModeTypes.SALMON
        elif "regular" in name.lower() or "turf" in name.lower():
            return ModeTypes.REGULAR
        else:
            return None

    @staticmethod
    async def generate_league(name: str, time: datetime = datetime.now(), session=None):
        lobby_type = Lobby.parse_special_lobby_type(name)
        if lobby_type == ModeTypes.LEAGUE:
            league = SplatoonRotation(time, ModeTypes.LEAGUE, session)
            success = await league.populate_data()
            if success:
                return league
        return None

    @staticmethod
    async def generate_salmon(name: str, time: datetime = datetime.now(), session=None):
        lobby_type = Lobby.parse_special_lobby_type(name)
        if lobby_type == ModeTypes.SALMON:
            salmon = SplatoonRotation(time, ModeTypes.SALMON, session)
            success = await salmon.populate_data()
            if success:
                return salmon
        return None

    @staticmethod
    async def generate_regular(name: str, time: datetime = datetime.now(), session=None):
        lobby_type = Lobby.parse_special_lobby_type(name)
        if lobby_type == ModeTypes.REGULAR:
            regular = SplatoonRotation(time, ModeTypes.REGULAR, session)
            success = await regular.populate_data()
            if success:
                return regular
        return None

    @staticmethod
    async def send_sal_err(ctx, time: datetime = datetime.now(), session=None):
        # Get all rotations
        all_rotations = await SplatoonRotation.get_all_rotations(time=time,
                                                                 mode_type=ModeTypes.SALMON, session=session)
        start_time = None
        # Loop through all rotations until we find the 1st one that's after the given time
        for rotation in all_rotations:
            if rotation.start_time >= time:
                start_time = rotation.start_time
                break
        # If we can't find given rotation use an error str
        if start_time is None:
            format_str = "an unknown time."
        else:
            format_str = SplatoonRotation.format_time_sr(start_time)
        # Form error string and send it
        err_str = ":warning: There isn't a Salmon Run rotation happening at the given time! The next rotation is at {}."
        err_str = err_str.format(format_str)
        await ctx.send(err_str)

    @staticmethod
    async def attach_send_gif(embed, lobby: LobbyData, ctx):
        schedule_type = Lobby.parse_special_lobby_type(lobby.metadata["name"])
        channel_id = str(DiscordChannel(ctx.channel).id)
        # we check if there are multiple stages in the rotation
        if schedule_type is ModeTypes.REGULAR or schedule_type is ModeTypes.LEAGUE:
            # if so attach the gif to the embed and send it off via the files argument
            embed, file = await Lobby.attach_gif(embed, lobby, channel_id)
            if file is not None:
                await ctx.send(embed=embed, file=file)
                return
        await ctx.send(embed=embed)

    @staticmethod
    async def attach_gif(embed, lobby: LobbyData, channel_id: str):
        schedule_type = Lobby.parse_special_lobby_type(lobby.metadata["name"])
        # we check if there are multiple stages in the rotation
        if schedule_type is ModeTypes.REGULAR or schedule_type is ModeTypes.LEAGUE:
            #  generate the gif, make it a discord file, attach gif to the embed, and return the result
            rotation_data = lobby.metadata["rotation_data"]
            generated_gif = await generate_gif(rotation_data, channel_id)
            file = discord.File(generated_gif)
            embed.set_image(url="attachment://" + generated_gif)
            return embed, file
        else:
            return embed, None


def setup(bot):
    bot.add_cog(Lobby(bot))
