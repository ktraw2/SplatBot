import config
import discord
from modules.splatoon_schedule import SplatoonSchedule, ScheduleTypes
from datetime import datetime, timedelta
from dateutil.parser import parse
from discord.ext import commands
from misc_date_utilities.date_difference import DateDifference


class Schedule:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def schedule(self, ctx, *args):
        await ctx.send("Available subcommands are: regular, ranked, league, salmon")

    @schedule.command()
    async def regular(self, ctx, *args):
        await self.make_schedule(ScheduleTypes.REGULAR, ctx, *args)

    @schedule.command()
    async def ranked(self, ctx, *args):
        await self.make_schedule(ScheduleTypes.RANKED, ctx, *args)

    @schedule.command()
    async def league(self, ctx, *args):
        await self.make_schedule(ScheduleTypes.LEAGUE, ctx, *args)

    @schedule.command()
    async def salmon(self, ctx, *args):
        await ctx.send(":warning: This command is being beta tested.")
        await self.make_schedule(ScheduleTypes.SALMON, ctx, *args)

    async def make_schedule(self, schedule_type: ScheduleTypes, ctx, *args):
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
            if schedule_type == ScheduleTypes.REGULAR:
                title += "Regular Battle"
                thumbnail = config.images["regular"]
            elif schedule_type == ScheduleTypes.RANKED:
                title += "Ranked Battle"
                thumbnail = config.images["ranked"]
            elif schedule_type == ScheduleTypes.LEAGUE:
                title += "League Battle"
                thumbnail = config.images["league"]
            elif schedule_type == ScheduleTypes.SALMON:
                title += "Salmon Run"
                thumbnail = config.images["salmon"]

            embed = discord.Embed(title=title, color=config.embed_color)
            embed.set_thumbnail(url=thumbnail)

            embed.add_field(name="Mode", value=schedule.mode)

            # custom stuff for salmon run
            if schedule_type == ScheduleTypes.SALMON:
                # Checking if full schedule has been released yet for salmon
                if schedule.stage_a is None:
                    await ctx.send(":warning: Weapons and stage have not been released yet: " +
                                   "showing rotation time only:")
                    # use special formatting because salmon run can occur between two separate days
                    embed.add_field(name="Rotation Time",
                                    value=SplatoonSchedule.format_time_sr(schedule.start_time) + " - "
                                          + SplatoonSchedule.format_time_sr(schedule.end_time))
                else:
                    embed.set_image(url=schedule.stage_a_image)
                    embed.add_field(name="Stages", value=schedule.stage_a)
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


def setup(bot):
    bot.add_cog(Schedule(bot))
