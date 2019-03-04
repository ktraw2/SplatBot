import config
import discord
from modules.splatoon_schedule import SplatoonSchedule, ModeTypes
from datetime import datetime, timedelta
from dateutil.parser import parse
from discord.ext import commands
from misc_date_utilities.date_difference import DateDifference


class Schedule:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(case_insensitive=True, invoke_without_command=True, aliases=["rotation", "info"])
    async def schedule(self, ctx, *args):
        await ctx.send("Available subcommands are: `regular`, `ranked`, `league`, `salmon`\n"
                       "Available subcommands for `ranked`, `league`, and `salmon` are: `upcoming`")

    @schedule.group(case_insensitive=True, invoke_without_command=True, aliases=["turf", "t", "reg"])
    async def regular(self, ctx, *args):
        await self.make_schedule(ModeTypes.REGULAR, ctx, *args)

    @schedule.group(case_insensitive=True, invoke_without_command=True, aliases=["rank", "rk"])
    async def ranked(self, ctx, *args):
        await self.make_schedule(ModeTypes.RANKED, ctx, *args)

    @schedule.group(case_insensitive=True, invoke_without_command=True, aliases=["l"])
    async def league(self, ctx, *args):
        await self.make_schedule(ModeTypes.LEAGUE, ctx, *args)

    @schedule.group(case_insensitive=True, invoke_without_command=True, aliases=["sr", "s"])
    async def salmon(self, ctx, *args):

        await self.make_schedule(ModeTypes.SALMON, ctx, *args)

    @salmon.command(name="upcoming", aliases=["next", "future", "list"])
    async def sr_upcoming(self, ctx, *args):
        await self.print_full_schedule(ModeTypes.SALMON, ctx)

    @ranked.command(name="upcoming", aliases=["next", "future", "list"])
    async def ranked_upcoming(self, ctx, *args):
        await self.print_full_schedule(ModeTypes.RANKED, ctx)

    @league.command(name="upcoming", aliases=["next", "future", "list"])
    async def league_upcoming(self, ctx, *args):
        await self.print_full_schedule(ModeTypes.LEAGUE, ctx)

    @regular.command(name="upcoming", aliases=["next", "future", "list"])
    async def turf_upcoming(self, ctx, *args):
        await self.print_full_schedule(ModeTypes.REGULAR, ctx)

    async def make_schedule(self, schedule_type: ModeTypes, ctx, *args):
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

        schedule = SplatoonSchedule(time, schedule_type, self.bot.session)
        success = await schedule.populate_data()

        if success:
            title = "Schedule Information - "
            thumbnail = ""
            if schedule_type == ModeTypes.REGULAR:
                title += "Regular Battle"
                thumbnail = config.images["regular"]
            elif schedule_type == ModeTypes.RANKED:
                title += "Ranked Battle"
                thumbnail = config.images["ranked"]
            elif schedule_type == ModeTypes.LEAGUE:
                title += "League Battle"
                thumbnail = config.images["league"]
            elif schedule_type == ModeTypes.SALMON:
                title += "Salmon Run"
                thumbnail = config.images["salmon"]

            embed = discord.Embed(title=title, color=config.embed_color)
            embed.set_thumbnail(url=thumbnail)

            embed.add_field(name="Mode", value=schedule.mode)

            # custom stuff for salmon run
            if schedule_type == ModeTypes.SALMON:
                # Checking if full schedule has been released yet for salmon
                if schedule.stage_a is None:
                    # use special formatting because salmon run can occur between two separate days
                    embed.add_field(name="Stage", value="*Not released yet*")
                    embed.add_field(name="Rotation Time",
                                    value=SplatoonSchedule.format_time_sr(schedule.start_time) + " - "
                                          + SplatoonSchedule.format_time_sr(schedule.end_time))
                    embed.add_field(name="Weapons", value="*Not released yet*")
                else:
                    embed.set_image(url=schedule.stage_a_image)
                    embed.add_field(name="Stage", value=schedule.stage_a)
                    # use special formatting because salmon run can occur between two separate days
                    embed.add_field(name="Rotation Time",
                                    value=SplatoonSchedule.format_time_sr(schedule.start_time) + " - "
                                          + SplatoonSchedule.format_time_sr(schedule.end_time))
                    embed.add_field(name="Weapons", value=schedule.weapons_array[0] + "\n" +
                                    schedule.weapons_array[1] + "\n" +
                                    schedule.weapons_array[2] + "\n" +
                                    schedule.weapons_array[3])

            else:
                embed.set_image(url=schedule.stage_a_image)
                embed.add_field(name="Stages", value=schedule.stage_a + "\n" + schedule.stage_b)
                embed.add_field(name="Rotation Time", value=SplatoonSchedule.format_time(schedule.start_time) + " - " +
                                                            SplatoonSchedule.format_time(schedule.end_time))

            await ctx.send(embed=embed)
        else:
            await ctx.send(":x: No schedule information was found for the given time.")

    async def print_full_schedule(self, schedule_type: ModeTypes, ctx):
        schedule_array = await SplatoonSchedule.populate_array(time=datetime.now(), schedule_type=schedule_type,
                                                               session=self.bot.session)

        next_rot_val = 0  # Array val to access the next rotation
        title = "Schedule Information - "
        thumbnail = ""
        if schedule_type == ModeTypes.REGULAR:
            title += "Regular Battle"
            thumbnail = config.images["regular"]
        elif schedule_type == ModeTypes.RANKED:
            title += "Ranked Battle"
            thumbnail = config.images["ranked"]
        elif schedule_type == ModeTypes.LEAGUE:
            title += "League Battle"
            thumbnail = config.images["league"]
        elif schedule_type == ModeTypes.SALMON:
            title += "Salmon Run"
            thumbnail = config.images["salmon"]

        embed = discord.Embed(title=title, color=config.embed_color)
        embed.set_thumbnail(url=thumbnail)

        # custom stuff for salmon run
        if schedule_type == ModeTypes.SALMON:
            embed.add_field(name="Mode", value=schedule_array[0].mode)
            value = ""
            for element in schedule_array:
                value = value + SplatoonSchedule.format_time_sr(element.start_time) + " - " + \
                        SplatoonSchedule.format_time_sr(element.end_time) + "\n"
            embed.add_field(name="Rotation Times", value=value)
        else:
            next_rot_val = 1
            for element in schedule_array:
                fmt_time = SplatoonSchedule.format_time_sch(element.start_time) + " - " \
                            + SplatoonSchedule.format_time_sch(element.end_time)
                embed.add_field(name="Rotation Time", value=fmt_time, inline=True)
                embed.add_field(name="Mode", value=element.mode, inline=True)

        # Calculates the amount of time until the next rotation
        time = schedule_array[next_rot_val].start_time
        time_diff = DateDifference.subtract_datetimes(time, datetime.now())
        time_str = str(time_diff)
        # For Salmon Run only: print if the rotation is happening right now
        if schedule_type == ModeTypes.SALMON and time_diff <= DateDifference(0):
            time_str = "Rotation is happening now!"

        embed.add_field(name="Time Until Next Rotation", value=time_str)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Schedule(bot))
