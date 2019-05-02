import sys
import math
import config
from discord.ext import commands
from modules.async_client import AsyncClient
from modules import embeds, checks


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(case_insensitive=True, invoke_without_command=True, aliases=["commands"])
    async def help(self, ctx, *args):
        """default help message for SplatBot"""
        if len(args) == 0:
            help_embed = embeds.generate_base_help_embed(self.bot)
            help_embed.add_field(name=":question: **Help Categories**",
                                 value="To get help for the various parts of " + self.bot.user.name + ", "
                                       "use `s!help [page]` to view any of the pages listed below:\n\n"
                                       "1. Lobby Commands\n"
                                       "2. Rotation Commands\n"
                                       "3. Misc. Commands\n"
                                       "4. Command Syntax Help\n\n"
                                       "You can also type `s!help full` "
                                       "if you would like the view the full contents of the help in a DM.")
            embeds.add_help_embed_footer_links(help_embed, self.bot)
            await ctx.send(embed=help_embed)
        else:
            await ctx.send(":x: Sorry, that is not a valid help page. Type `s!help` to view the valid help pages.")

    @help.command(name="1", aliases=["Lobby"])
    async def lobby_commands(self, ctx):
        help_embed = embeds.generate_base_help_embed(self.bot)
        embeds.add_help_embed_field(help_embed, "lobby_commands")
        await ctx.send(embed=help_embed)

    @help.command(name="2", aliases=["Rotation", "Schedule"])
    async def rotation_commands(self, ctx):
        help_embed = embeds.generate_base_help_embed(self.bot)
        embeds.add_help_embed_field(help_embed, "rotation_commands")
        await ctx.send(embed=help_embed)

    @help.command(name="3", aliases=["Misc"])
    async def misc_commands(self, ctx):
        help_embed = embeds.generate_base_help_embed(self.bot)
        embeds.add_help_embed_field(help_embed, "misc_commands")
        await ctx.send(embed=help_embed)

    @help.command(name="4", aliases=["Command"])
    async def command_syntax(self, ctx):
        help_embed = embeds.generate_base_help_embed(self.bot)
        embeds.add_help_embed_field(help_embed, "command_syntax")
        await ctx.send(embed=help_embed)

    @help.command()
    async def full(self, ctx):
        help_embed = embeds.generate_base_help_embed(self.bot)
        for key, field in embeds.help_embed_fields.items():
            help_embed.add_field(name=field["title"], value=field["body"])
        embeds.add_help_embed_footer_links(help_embed, self.bot)
        await ctx.author.send(embed=help_embed)
        await ctx.send(":white_check_mark: " + ctx.author.mention +
                       ", the full help for " + self.bot.user.name + " has been DMed to you to prevent spam.")

    @commands.command()
    @commands.check(checks.user_is_developer)
    async def update(self, ctx, *args):
        self.bot.exit = 3  # exit code will be interpreted by bash to update bot
        await ctx.send(":white_check_mark: Updating and restarting " + self.bot.user.name + "...")
        if self.bot.session is not None:
            await self.bot.session.close()
        await self.bot.logout()

    @commands.command()
    async def hello(self, ctx, *args):
        await ctx.send("Hello, World!")

    @commands.command(aliases=["🍑"])
    async def buttcheeks(self, ctx, *args):
        await ctx.message.add_reaction("🍑")
        await ctx.send("Who is buttcheeks???")

    @commands.command()
    @commands.guild_only()
    @checks.message_from_guild(config.ts_guild_id)
    @commands.check(checks.off_topic_commands_enabled)
    async def kevin(self, ctx, *args):
        await ctx.send(ctx.guild.get_role(config.ts_guild_id).mention + " KEVIN GANG KEVIN GANG KEVIN GANG")

    @commands.command()
    @commands.check(checks.off_topic_commands_enabled)
    async def boxie(self, ctx, *args):
        await ctx.send("VIAN WHERE'S BRIDGETT :(")

    @commands.command()
    @commands.guild_only()
    @checks.message_from_guild(config.ts_guild_id)
    @commands.check(checks.off_topic_commands_enabled)
    async def list_kevins(self, ctx, *args):
        kevin_str = "Only Kevin: <@192053720236818432>"
        await ctx.send(kevin_str)

    @commands.command(aliases=["f"])
    @commands.check(checks.off_topic_commands_enabled)
    async def eff(self, ctx, *args):
        # embedded function for small calculation
        def get_num_f(base_size):
            return int(math.ceil(base_size * size_mult))

        char_to_print = "F"
        str_to_send = ""
        size_mult = 1
        if len(args) > 0:
            char_to_print = args[0]

            # Blacklisting @everyone and @here to prevent pinging everyone
            if "@everyone" in char_to_print or "@here" in char_to_print:
                return

            size_mult = 0.5

        # Builds the big F
        for x in range(get_num_f(3)):
            for y in range(get_num_f(19)):
                str_to_send = str_to_send + char_to_print
            str_to_send = str_to_send + "\n"

        for x in range(get_num_f(3)):
            for y in range(get_num_f(6)):
                str_to_send = str_to_send + char_to_print
            str_to_send = str_to_send + "\n"

        for x in range(get_num_f(3)):
            for y in range(get_num_f(12)):
                str_to_send = str_to_send + char_to_print
            str_to_send = str_to_send + "\n"

        for x in range(get_num_f(5)):
            for y in range(get_num_f(6)):
                str_to_send = str_to_send + char_to_print
            str_to_send = str_to_send + "\n"

        if len(str_to_send) > 2000:
            await ctx.send(":warning: Output exceeds character limit. Please try a smaller output.")
        else:
            await ctx.send(str_to_send)

    @commands.command()
    @commands.is_owner()
    @commands.check(checks.off_topic_commands_enabled)
    async def getip(self, ctx, *args):
        ip_text = await AsyncClient(session=self.bot.session).send_request("http://checkip.dyndns.org/")
        # scrape page for body
        body = ip_text[ip_text.index("<body>") + len("<body>"):ip_text.index("</body>")]
        await ctx.send(body)


def setup(bot):
    # remove the default help command so the better one can be used
    bot.remove_command("help")
    bot.add_cog(Misc(bot))
