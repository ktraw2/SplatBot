# Add this bot: https://discordapp.com/oauth2/authorize?client_id=545107229842472971&scope=bot&permissions=16384

import discord
import os
import aiohttp
import config
from discord.ext import commands

print("Starting SplatBot...")
SPLATBOT_EXTENSIONS = ["cogs.lobby",
                       "cogs.misc",
                       "cogs.schedule"]


class SplatQueues(commands.Bot):
    def __init__(self, extensions):
        SplatQueues.make_sure_file_exists("config.py")
        super().__init__(command_prefix=config.prefix, description=config.description, case_insensitive=True)

        self.session = aiohttp.ClientSession()

        for e in extensions:
            self.load_extension(e)

    async def on_ready(self):
        print("Connected")
        await self.get_channel(config.online_logger_id).send("*Connected to Discord*")
        await self.change_presence(activity=discord.Game(name="Say s!help"))

    async def on_guild_join(self, guild):
        await self.get_channel(config.online_logger_id).send("Joined `" + guild.name + "`")

    async def on_guild_remove(self, guild):
        await self.get_channel(config.online_logger_id)("Left `" + guild.name + "`")

    async def on_command(self, ctx):
        await self.get_channel(config.online_logger_id).send("Command received from `" + ctx.author.name + "` on `" +
                                                             ctx.guild.name + "`: " + ctx.message.content)

    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.Forbidden) or "missing permissions" in str(error).lower():
            await ctx.send(":x: I do not have permission to send embedded messages in this channel and/or server!  "
                           "Make sure I have the permission `Embed Links`, or I can't function!")
            await self.get_channel(config.online_logger_id).send(":information_source: A handled error occured "
                                                                 "of type `" + type(error).__name__ + "` for message `"
                                                                 + ctx.message.content + "`: `" + str(error) + "`")
        elif (isinstance(error, discord.HTTPException) or isinstance(error, aiohttp.ClientOSError)) \
                and not hasattr("on_error", ctx.command):
            await ctx.send(":warning: An unexpected error occurred and a report has been sent to the developer.")
            await self.get_channel(config.online_logger_id).send(":warning: An unexpected error occurred of type `" +
                                                                 type(error).__name__ + "` for message `" +
                                                                 ctx.message.content + "`: `" + str(error) + "`")
        elif isinstance(error, discord.ext.commands.CommandNotFound):
            if config.send_invalid_command:
                await ctx.send(":x: Sorry, `" + ctx.invoked_with +
                               "` is not a valid command.  Type `s!help` for a list of commands.")
            await self.get_channel(config.online_logger_id).send("Invalid command received from `" + ctx.author.name +
                                                                 "` on `" + ctx.guild.name + "`: " +
                                                                 ctx.message.content)
        elif isinstance(error, discord.ext.commands.CheckFailure):
            if isinstance(error, discord.ext.commands.NotOwner):
                await ctx.send(":warning: You are not authorized to run this command, "
                               "to be able to run `" + ctx.invoked_with +
                               "` you must be the owner of this bot.")
            else:
                if ctx.invoked_with == "form":
                    await ctx.send(":warning: You are not authorized to run this command.")
                else:
                    await ctx.send(":warning: You are not authorized to run this command, "
                                   "to be able to run `" + ctx.invoked_with +
                                   "` you must have a role named `TVManager` or have one or more of "
                                   "the following permissions: `Administrator`, `Manage Channels`, "
                                   "and/or `Manage Server`.")
        else:
            await ctx.send(":warning: An unexpected error occurred and a report has been sent to the developer.")
            await self.get_channel(config.online_logger_id).send(":warning: An unexpected error occurred of type `" +
                                                                 type(error).__name__ + "` for message `" +
                                                                 ctx.message.content + "`: `" + str(error) + "`")

    @staticmethod
    def make_sure_file_exists(path, default_config=""):
        if not os.path.isfile(path):
            # logger.log(level=logging.WARNING, msg=path + " does not exist. Creating a default configuration.")
            print("WARNING: " + path + " does not exist. Creating a default configuration.")
            new_file = open(path, "w")
            new_file.write(default_config)
            new_file.close()


SplatQueues(SPLATBOT_EXTENSIONS).run(config.token)
