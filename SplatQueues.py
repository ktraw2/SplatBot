import discord
import config
from discord.ext import commands

print("Starting SplatQueues...")
SPLATQUEUES_EXTENSIONS = ["cogs.queue"]


class SplatQueues(commands.Bot):
    def __init__(self, extensions):
        super().__init__(command_prefix=config.prefix, description=config.description, case_insensitive=True)

        for e in extensions:
            self.load_extension(e)

SplatQueues(SPLATQUEUES_EXTENSIONS).run(config.token)
