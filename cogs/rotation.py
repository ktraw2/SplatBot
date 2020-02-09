import config
import discord
from modules.splatoon_rotation import SplatoonRotation, ModeTypes
from modules.gif_generator import generate_gif
from datetime import datetime, timedelta
from dateutil.parser import parse
from discord.ext import commands
from misc_date_utilities.date_difference import DateDifference


class Rotation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(case_insensitive=True, invoke_without_command=True, aliases=["schedule", "schedules", "rotations",
                                                                                 "info"])
    async def rotation(self, ctx, *args):
        await ctx.send("Available subcommands are: `regular`, `ranked`, `league`, `salmon`\n"
                       "Available subcommands for `ranked`, `league`, and `salmon` are: `upcoming` and `next`")

    @rotation.group(case_insensitive=True, invoke_without_command=True, aliases=["turf", "t", "reg"])
    async def regular(self, ctx, *args):
        await self.make_single_rotation(ModeTypes.REGULAR, ctx, *args)

    @rotation.group(case_insensitive=True, invoke_without_command=True, aliases=["rank", "rk", "rked"])
    async def ranked(self, ctx, *args):
        await self.make_single_rotation(ModeTypes.RANKED, ctx, *args)

    @rotation.group(case_insensitive=True, invoke_without_command=True, aliases=["l", "double", "quad"])
    async def league(self, ctx, *args):
        await self.make_single_rotation(ModeTypes.LEAGUE, ctx, *args)

    @rotation.group(case_insensitive=True, invoke_without_command=True, aliases=["sr", "s", "sal"])
    async def salmon(self, ctx, *args):
        await self.make_single_rotation(ModeTypes.SALMON, ctx, *args)

    @salmon.command(name="upcoming", aliases=["list", "full", "rotations"])
    async def salmon_upcoming(self, ctx, *args):
        await self.make_upcoming_rotations(ModeTypes.SALMON, ctx)

    @ranked.command(name="upcoming", aliases=["list", "full", "rotations"])
    async def ranked_upcoming(self, ctx, *args):
        await self.make_upcoming_rotations(ModeTypes.RANKED, ctx)

    @league.command(name="upcoming", aliases=["u", "list", "full", "rotations"])
    async def league_upcoming(self, ctx, *args):
        await self.make_upcoming_rotations(ModeTypes.LEAGUE, ctx)

    @regular.command(name="upcoming", aliases=["list", "full", "rotations"])
    async def turf_upcoming(self, ctx, *args):
        await self.make_upcoming_rotations(ModeTypes.REGULAR, ctx)

    @salmon.command(name="next", aliases=["n"])
    async def salmon_next(self, ctx, *args):
        await self.make_next_rotation(ModeTypes.SALMON, ctx)

    @ranked.command(name="next", aliases=["n"])
    async def ranked_next(self, ctx, *args):
        await self.make_next_rotation(ModeTypes.RANKED, ctx)

    @league.command(name="next", aliases=["n"])
    async def league_next(self, ctx, *args):
        await self.make_next_rotation(ModeTypes.LEAGUE, ctx)

    @regular.command(name="next", aliases=["n"])
    async def turf_next(self, ctx, *args):
        await self.make_next_rotation(ModeTypes.REGULAR, ctx)

    async def make_single_rotation(self, schedule_type: ModeTypes, ctx, *args):
        time = datetime.now()

        if len(args) > 0:
            try:
                time = parse(args[0])
                # if the time has already happened, delay the lobby start time to the next day
                if DateDifference.subtract_datetimes(time, datetime.now()) <= DateDifference(0):
                    time = time + timedelta(days=1)
            except ValueError as e:
                await ctx.send(":x: You gave an invalid time.")
                return

        rotation = SplatoonRotation(time, schedule_type, self.bot.session)
        success = await rotation.populate_data()

        if success:
            title = "Rotation Information - "
            thumbnail = ""
            if schedule_type is ModeTypes.REGULAR:
                title += "Regular Battle"
                thumbnail = config.images["regular"]
            elif schedule_type is ModeTypes.RANKED:
                title += "Ranked Battle"
                thumbnail = config.images["ranked"]
            elif schedule_type is ModeTypes.LEAGUE:
                title += "League Battle"
                thumbnail = config.images["league"]
            elif schedule_type is ModeTypes.SALMON:
                title += "Salmon Run"
                thumbnail = config.images["salmon"]

            embed = discord.Embed(title=title, color=config.embed_color)
            embed.set_thumbnail(url=thumbnail)
            embed.add_field(name="Mode", value=rotation.mode)

            # custom stuff for salmon run
            if schedule_type is ModeTypes.SALMON:
                embed = await Rotation.generate_salmon_embed(embed, rotation)
                if rotation.stage_a_image is None:
                    await ctx.send(":warning: Detailed Salmon Run information is not available!")

            else:
                embed.add_field(name="Stages", value=rotation.stage_a + "\n" + rotation.stage_b)
                embed.add_field(name="Rotation Time", value=SplatoonRotation.format_time(rotation.start_time) + " - " +
                                                            SplatoonRotation.format_time(rotation.end_time))

            await Rotation.generate_send_gif(embed, rotation, schedule_type, ctx)

        else:
            # if there's no rotation, only print the next rotation for salmon run
            if schedule_type is ModeTypes.SALMON:
                await ctx.send(":x: No rotation information was found for the given time: showing next rotation...")

                # Make the embed, add required fields
                embed = discord.Embed(title="Rotation Information - Salmon Run", color=config.embed_color)
                embed.set_thumbnail(url=config.images["salmon"])
                embed.add_field(name="Mode", value=rotation.mode)
                # Get next rotation (which is the 0th one) and send it out
                next_rotation_array = await rotation.get_all_rotations(time=datetime.now(), mode_type=schedule_type)
                next_rotation = next_rotation_array[0]
                for rotation in next_rotation_array:
                    if time <= rotation.start_time:
                        next_rotation = rotation
                        break
                embed = await Rotation.generate_salmon_embed(embed, next_rotation)

                await Rotation.generate_send_gif(embed, rotation, schedule_type, ctx)
            else:
                await ctx.send(":x: No rotation information was found for the given time.")

    async def make_upcoming_rotations(self, schedule_type: ModeTypes, ctx):
        schedule_array = await SplatoonRotation.get_all_rotations(time=datetime.now(), mode_type=schedule_type,
                                                                  session=self.bot.session)

        next_rot_val = 0  # Array val to access the next rotation
        title = "Upcoming Rotation Information - "
        thumbnail = ""
        if schedule_type is ModeTypes.REGULAR:
            title += "Regular Battle"
            thumbnail = config.images["regular"]
        elif schedule_type is ModeTypes.RANKED:
            title += "Ranked Battle"
            thumbnail = config.images["ranked"]
        elif schedule_type is ModeTypes.LEAGUE:
            title += "League Battle"
            thumbnail = config.images["league"]
        elif schedule_type is ModeTypes.SALMON:
            title += "Salmon Run"
            thumbnail = config.images["salmon"]

        embed = discord.Embed(title=title, color=config.embed_color)
        embed.set_thumbnail(url=thumbnail)

        # custom stuff for salmon run
        if schedule_type is ModeTypes.SALMON:
            embed.add_field(name="Mode", value=schedule_array[0].mode)
            value = ""
            for element in schedule_array:
                value = value + SplatoonRotation.format_time_sr(element.start_time) + " - " + \
                        SplatoonRotation.format_time_sr(element.end_time) + "\n"
            embed.add_field(name="Rotation Times", value=value)
        else:
            next_rot_val = 1
            for element in schedule_array:
                fmt_time = SplatoonRotation.format_time_sch(element.start_time) + " - " \
                           + SplatoonRotation.format_time_sch(element.end_time)
                embed.add_field(name="Rotation Time", value=fmt_time, inline=True)
                embed.add_field(name="Mode", value=element.mode, inline=True)

        # Calculates the amount of time until the next rotation
        time = schedule_array[next_rot_val].start_time
        time_diff = DateDifference.subtract_datetimes(time, datetime.now())
        time_str = str(time_diff)
        # For Salmon Run only: print if the rotation is happening right now
        if schedule_type is ModeTypes.SALMON and time_diff <= DateDifference(0):
            time_str = "Rotation is happening now!"

        embed.add_field(name="Time Until Next Rotation", value=time_str)

        await ctx.send(embed=embed)

    async def make_next_rotation(self, schedule_type: ModeTypes, ctx):
        schedule_array = await SplatoonRotation.get_all_rotations(time=datetime.now(), mode_type=schedule_type,
                                                                  session=self.bot.session)

        next_rotation = schedule_array[1]

        title = "Next Rotation Information - "
        thumbnail = ""
        if schedule_type is ModeTypes.REGULAR:
            title += "Regular Battle"
            thumbnail = config.images["regular"]
        elif schedule_type is ModeTypes.RANKED:
            title += "Ranked Battle"
            thumbnail = config.images["ranked"]
        elif schedule_type is ModeTypes.LEAGUE:
            title += "League Battle"
            thumbnail = config.images["league"]
        elif schedule_type is ModeTypes.SALMON:
            title += "Salmon Run"
            thumbnail = config.images["salmon"]
            # if there isn't a salmon rotation happening, show the next one
            if schedule_array[0].start_time > datetime.now():
                next_rotation = schedule_array[0]

        embed = discord.Embed(title=title, color=config.embed_color)
        embed.set_thumbnail(url=thumbnail)

        embed.add_field(name="Mode", value=next_rotation.mode)

        # custom stuff for salmon run
        if schedule_type is ModeTypes.SALMON:
            # Use helper method to generate salmon run info
            embed = await Rotation.generate_salmon_embed(embed, next_rotation)
            # Print warning if detailed salmon run info isn't available
            if next_rotation.stage_a_image is None:
                await ctx.send(":warning: Detailed Salmon Run information is not available!")
        else:
            embed.add_field(name="Stages", value=next_rotation.stage_a + "\n" + next_rotation.stage_b)
            embed.add_field(name="Rotation Time", value=SplatoonRotation.format_time(next_rotation.start_time) + " - " +
                                                        SplatoonRotation.format_time(next_rotation.end_time))

        # Calculates the amount of time until the next rotation
        time = next_rotation.start_time
        time_diff = DateDifference.subtract_datetimes(time, datetime.now())
        time_str = str(time_diff)

        embed.add_field(name="Time Until Next Rotation", value=time_str)

        await Rotation.generate_send_gif(embed, next_rotation, schedule_type, ctx)

    @staticmethod
    async def generate_send_gif(embed, rotation_data: SplatoonRotation, schedule_type: ModeTypes, ctx):
        if schedule_type is not ModeTypes.SALMON:
            #  generate the gif, make it a discord file, and send it off
            channel_id = str(ctx.channel.id)
            generated_gif = await generate_gif(rotation_data, channel_id)
            file = discord.File(generated_gif)
            embed.set_image(url="attachment://" + generated_gif)
            await ctx.send(embed=embed, file=file)
        else:
            await ctx.send(embed=embed)

    @staticmethod
    async def generate_salmon_embed(embed: discord.Embed, rotation: SplatoonRotation):
        # Checking if full rotation has been released yet for salmon
        if rotation.stage_a is None:
            # use special formatting because salmon run can occur between two separate days
            embed.add_field(name="Stage", value="*Not released yet*")
            embed.add_field(name="Rotation Time",
                            value=SplatoonRotation.format_time_sr(rotation.start_time) + " - "
                                  + SplatoonRotation.format_time_sr(rotation.end_time))
            embed.add_field(name="Weapons", value="*Not released yet*")
        else:
            embed.set_image(url=rotation.stage_a_image)
            embed.add_field(name="Stage", value=rotation.stage_a)
            # use special formatting because salmon run can occur between two separate days
            embed.add_field(name="Rotation Time",
                            value=SplatoonRotation.format_time_sr(rotation.start_time) + " - "
                                  + SplatoonRotation.format_time_sr(rotation.end_time))
            embed.add_field(name="Weapons",
                            value=SplatoonRotation.print_sr_weapons(rotation.weapons_array))
        return embed

def setup(bot):
    bot.add_cog(Rotation(bot))
