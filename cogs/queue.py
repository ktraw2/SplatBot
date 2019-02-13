from discord.ext import commands


class Queue:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def queue(selfself, ctx, *args):
        await ctx.send("Queue!")

def setup(bot):
    bot.add_cog(Queue(bot))
