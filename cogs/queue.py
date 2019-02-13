from discord.ext import commands
from modules.queue_data import Queue_Data


class Queue:
    def __init__(self, bot):
        self.bot = bot
        self.queues = []

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def queue(self, ctx, *args):
        queue = self.find_queue(ctx.channel.id)
        if queue is None:
            await ctx.send("Available queue commands are: start, add, remove, end")
        else:
            await ctx.send("You have a queue!")

    @queue.command()
    async def start(self, ctx, *args):
        queue = self.find_queue(ctx.channel.id)
        if queue is None:
            self.queues.append(Queue_Data(ctx.channel.id))
            await ctx.send(":white_check_mark: Created a queue in " + ctx.channel.mention)
        else:
            await ctx.send(":x: A queue already exists in " + ctx.channel.mention)

    @queue.command()
    async def add(self, ctx, *args):
        pass

    @queue.command()
    async def remove(self, ctx, *args):
        pass

    @queue.command(alias=["delete"])
    async def end(self, ctx, *args):
        queue = self.find_queue(ctx.channel.id)
        if queue is not None:
            self.queues.remove(queue)
            await ctx.send(":white_check_mark: Deleted the queue from " + ctx.channel.mention)
        else:
            await ctx.send(":x: There is currently no active queue in " + ctx.channel.mention)

    def find_queue(self, channel):
        for queue in self.queues:
            if queue.channel_id == channel:
                return queue
        return None

def setup(bot):
    bot.add_cog(Queue(bot))
