# Add this bot: https://discordapp.com/oauth2/authorize?client_id=545107229842472971&scope=bot&permissions=16384

import discord
import aiohttp
import config
import traceback
import sys
from modules import checks
from modules.database import Database
from discord.ext import commands
import os
import asyncio

print("Starting SplatBot...")
SPLATBOT_EXTENSIONS = ["cogs.rotation",
                       "cogs.lobby",
                       "cogs.help",
                       "cogs.dev",
                       "cogs.fun",
                       "cogs.settings"]

exit_code = 0


class SplatBot(commands.Bot):
    def __init__(self, extensions):
        checks.make_sure_file_exists("config.py")
        super().__init__(command_prefix=config.prefix, description=config.description, case_insensitive=True)

        global exit_code
        self.exit = exit_code
        self.session = None
        self.database = Database()
        self.database.create_database()

        for e in extensions:
            self.load_extension(e)

        self.loop.create_task(self.garbage_collector())

    async def garbage_collector(self):
        """Removes all .gif and .png files from gif generation for lobby/rotation info"""
        await self.wait_until_ready()
        while not self.is_closed():
            print("[Splatbot] Deleting old files...")
            for f in os.listdir():
                if f.endswith(".gif") or f.endswith(".png"):
                    os.remove(f)
            print("[Splatbot] Deleted all old files")
            await asyncio.sleep(300)  # removes every 5 min/300 sec

    async def on_ready(self):
        print("Connected")
        self.session = aiohttp.ClientSession()
        await self.get_channel(config.online_logger_id).send("*Connected to Discord*")
        await self.change_presence(activity=discord.Game(name="Say s!help"))

    async def on_disconnect(self):
        global exit_code
        exit_code = self.exit

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
            await self.send_unexpected_error(ctx, error)
        elif isinstance(error, discord.ext.commands.CommandNotFound):
            if config.send_invalid_command:
                await ctx.send(":x: Sorry, `" + ctx.invoked_with +
                               "` is not a valid command.  Type `s!help` for a list of commands.")
            await self.get_channel(config.online_logger_id).send("Invalid command received from `" + ctx.author.name +
                                                                 "` on `" + ctx.guild.name + "`: " +
                                                                 ctx.message.content)
        elif isinstance(error, discord.ext.commands.CheckFailure):
            await ctx.send(":x: Sorry, `" + ctx.invoked_with +
                           "` is not a valid command in this context.  Type `s!help` for a list of commands.")
        elif isinstance(error, discord.ext.commands.BadArgument):
            await ctx.send(":x: Your command arguments could not be interpreted, please try again (Did you forget a"
                           " \" character?).")
            await self.get_channel(config.online_logger_id).send("Invalid command arguments received from `" +
                                                                 ctx.author.name + "` on `" + ctx.guild.name + "`: " +
                                                                 ctx.message.content)
        else:
            await self.send_unexpected_error(ctx, error)

    async def send_unexpected_error(self, ctx, error):
        await ctx.send(":warning: An unexpected error occurred and a report has been sent to the developer.")
        tb = traceback.extract_tb(tb=error.original.__traceback__)
        await self.get_channel(config.online_logger_id).send(":warning: An unexpected error occurred of type `" +
                                                             type(error).__name__ + "` for message `" +
                                                             ctx.message.content + "`: `" + str(error) + "`" +
                                                             " in function `" + tb[-1].name + "`" +
                                                             " on line `" + str(tb[-1].lineno) + "`" +
                                                             " in file `" + tb[-1].filename + "`")


SplatBot(SPLATBOT_EXTENSIONS).run(config.token)
sys.exit(exit_code)
