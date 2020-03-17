import math
import config
from discord.ext import commands
from modules import checks


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["🍑"])
    @commands.guild_only()
    @checks.message_from_guild(config.ts_guild_id)
    @commands.check(checks.off_topic_commands_enabled)
    async def buttcheeks(self, ctx, *args):
        await ctx.message.add_reaction("🍑")
        await ctx.send("Who is buttcheeks???")

    @commands.command(aliases=["reminddavid"])
    @commands.guild_only()
    @checks.message_from_guild(config.ts_guild_id)
    @commands.check(checks.off_topic_commands_enabled)
    async def remind_david(self, ctx, *, arg):
        if len(arg) == 0:
            await ctx.send("<@283480526336163840> reminder to bring gcn to wgf kthxbai")
        else:
            await ctx.send("<@283480526336163840> " + arg)

    @commands.command()
    @commands.guild_only()
    @checks.message_from_guild(config.ts_guild_id)
    @commands.check(checks.off_topic_commands_enabled)
    async def kevin(self, ctx, *args):
        await ctx.send(ctx.guild.get_role(config.ts_guild_id).mention + " KEVIN GANG KEVIN GANG KEVIN GANG")

    @commands.command()
    @commands.check(checks.off_topic_commands_enabled)
    async def boxie(self, ctx, *args):
        await ctx.send("#PreventBridgettAbuse :package:")

    @commands.command(aliases=["listkevins", "kevins"])
    @commands.guild_only()
    @checks.message_from_guild(config.ts_guild_id)
    @commands.check(checks.off_topic_commands_enabled)
    async def list_kevins(self, ctx, *args):
        kevin_str = "Kevin #1: <@394434644642103296>" + "\n" + \
                    "Kevin #2: <@333435876275388426>" + "\n" + \
                    "Kevin #3: " + "\n" + \
                    "Kevin #4: " + "\n" + \
                    "Kevin #5: " + "\n" + \
                    "Kevin #6: " + "\n" + \
                    "Kevin # Rainmaker Main: <@192053720236818432>" + "\n"
        await ctx.send(kevin_str)

    @commands.command()
    @commands.guild_only()
    @checks.message_from_guild(config.ts_guild_id)
    @commands.check(checks.off_topic_commands_enabled)
    async def list_uncool_people(self, ctx, *args):
        await ctx.send("Uncool People:\n"
                       "For being dum dum: <@192053720236818432>")

    @commands.command(case_insensitive=True, aliases=["f"])
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
                await ctx.send(":x: `@everyone` and `@here` have been blacklisted. Please try again.")
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
            await ctx.send(":warning: Output exceeds Discord character limit. Please try a smaller input.")
        else:
            await ctx.send(str_to_send)

def setup(bot):
    bot.add_cog(Fun(bot))