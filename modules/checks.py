import config
from discord.ext import commands

def user_is_developer(ctx):
    is_developer = False
    for id in config.developers:
        if ctx.author.id == id:
            is_developer = True
    return is_developer


def off_topic_commands_enabled(ctx):
    return config.off_topic_commands_enabled


def message_from_guild(id):
    def predicate(ctx):
        return ctx.message.guild.id == id
    return commands.check(predicate)