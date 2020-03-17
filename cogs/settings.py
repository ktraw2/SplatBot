from discord.ext import commands
from discord.ext.commands import Context
from dateutil import tz


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = bot.database

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def settings(self, ctx: Context):
        await ctx.send("Available subcommands are: `get`, `set`")

    @settings.group(case_insensitive=True, invoke_without_command=True)
    async def get(self, ctx: Context):
        await ctx.send("Available subcommands are: `timezone`")

    @get.command(name="timezone")
    async def get_timezone(self, ctx: Context):
        zone = self.database.time_zone_for_server(ctx.guild.id)
        if zone is tz.tzutc():
            name = "UTC"
        else:
            name = zone._filename
        await ctx.send("The timezone for `" + ctx.guild.name + "` is: `" + name + "`")

    @settings.group(case_insensitive=True, invoke_without_command=True)
    async def set(self, ctx: Context):
        await ctx.send("Available subcommands are: `timezone`")

    @set.command(name="timezone")
    async def set_timezone(self, ctx: Context, timezone: str):
        try:
            self.database.set_time_zone_for_server(ctx.guild.id, timezone)
            await ctx.send(":white_check_mark: Successfully changed the timezone for `" + ctx.guild.name +
                           "` to `" + timezone + "`")
        except AttributeError:
            await ctx.send(":x: You gave an invalid timezone. Please provide a timzone from the tz database. "
                           "You can find valid names "
                           "here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones. No settings have "
                           "been changed.")


def setup(bot):
    bot.add_cog(Settings(bot))
