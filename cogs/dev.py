from discord.ext import commands
from modules.async_client import AsyncClient
from modules import checks


class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx, *args):
        await ctx.send("Hello, World!")

    @commands.command()
    @commands.check(checks.user_is_developer)
    async def update(self, ctx, *args):
        self.bot.exit = 3  # exit code will be interpreted by bash to update bot
        await ctx.send(":white_check_mark: Updating and restarting " + self.bot.user.name + "...")
        if self.bot.session is not None:
            await self.bot.session.close()
        await self.bot.logout()

    @commands.command()
    @commands.is_owner()
    @commands.check(checks.off_topic_commands_enabled)
    async def getip(self, ctx, *args):
        ip_text = await AsyncClient(session=self.bot.session).send_request("http://checkip.dyndns.org/")
        # scrape page for body
        body = ip_text[ip_text.index("<body>") + len("<body>"):ip_text.index("</body>")]
        await ctx.send(body)

def setup(bot):
    bot.add_cog(Dev(bot))
