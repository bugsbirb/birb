from discord.ext import commands
import time
class analyticss(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if ctx.guild is None:
            return
        start_execution_time = time.perf_counter()
        prfx = time.strftime("%H:%M:%S GMT", time.gmtime())

        prfx = f"[🤖] {prfx}"
        await self.client.db['analytics'].update_one(
            {}, {"$inc": {f"{ctx.command.qualified_name}": 1}}, upsert=True
        )

        command = ctx.command.qualified_name
        end_execution_time = time.perf_counter()
        execution_duration = end_execution_time - start_execution_time
        execution_duration = round(execution_duration, 3)

        print(
            prfx
            + f" Command '{command}' executed in {execution_duration} seconds by @{(ctx.author)} at {ctx.guild}"
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(analyticss(client))
