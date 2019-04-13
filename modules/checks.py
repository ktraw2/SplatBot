import os
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


# not a discord.py check, but it still checks things
def make_sure_file_exists(path, default_config=b''):
    if not os.path.isfile(path):
        # logger.log(level=logging.WARNING, msg=path + " does not exist. Creating a default configuration.")
        print("WARNING: " + path + " does not exist. Creating a default configuration.")
        new_file = open(path, "wb")
        new_file.write(default_config)
        new_file.close()