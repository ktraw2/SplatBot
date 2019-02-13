import discord
from discord.ext import commands


class Misc():
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    # remove the default help command so the better one can be used
    bot.remove_command("help")
    bot.add_cog(Misc(bot))
