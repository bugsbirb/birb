from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
analytics = db['analytics']
import time


class analyticss(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_command(self, ctx):
     start_execution_time = time.perf_counter()
     prfx = (time.strftime("%H:%M:%S GMT", time.gmtime()))


     if ctx.guild is None:
        return
     prfx = f"[🤖] {prfx}"
     await analytics.update_one({}, {'$inc': {f'{ctx.command.qualified_name}': 1}}, upsert=True)

     command = ctx.command.qualified_name
     end_execution_time = time.perf_counter()
     execution_duration = end_execution_time - start_execution_time
     execution_duration = round(execution_duration,  3)
     

     print(prfx + f" Command '{command}' executed in {execution_duration} seconds by @{(ctx.author)} at {ctx.guild}")
         

       
    








async def setup(client: commands.Bot) -> None:
    await client.add_cog(analyticss(client))     
