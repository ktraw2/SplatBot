import sys
import config
from discord.ext import commands
from modules import embeds


def check_user_is_developer(ctx):
    is_developer = False
    for id in config.developers:
        if ctx.author.id == id:
            is_developer = True
    return is_developer


class Misc:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(case_insensitive=True, invoke_without_command=True, aliases=["commands"])
    async def help(self, ctx, *args):
        """default help message for TVBot"""
        if len(args) == 0:
            help_embed = embeds.generate_base_help_embed(self.bot)
            help_embed.add_field(name=":question: **Help Categories**",
                                 value="To get help for the various parts of " + self.bot.user.name + ", "
                                       "use `s!help [page]` to view any of the pages listed below:\n\n"
                                       "1. Lobby Commands\n"
                                       "2. Schedule Commands\n"
                                       "3. Misc. Commands\n"
                                       "3. Command Syntax Help\n\n"
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

    @help.command(name="2", aliases=["Schedule"])
    async def misc_commands(self, ctx):
        help_embed = embeds.generate_base_help_embed(self.bot)
        embeds.add_help_embed_field(help_embed, "schedule_commands")
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
    @commands.check(check_user_is_developer)
    async def update(self, ctx, *args):
        await ctx.send(":white_check_mark: Updating and restarting " + self.bot.user.name + "...")
        sys.exit(3)  # exit code will be interpreted by bash to update bot

    @commands.command()
    async def hello(self, ctx, *args):
        await ctx.send("Hello!")


def setup(bot):
    # remove the default help command so the better one can be used
    bot.remove_command("help")
    bot.add_cog(Misc(bot))
