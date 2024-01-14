import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
analytics = db['analytics']


class analyticss(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if ctx.guild is None:
            return
        await analytics.update_one({}, {'$inc': {f'{ctx.command.qualified_name}': 1}}, upsert=True)




        

       
    








async def setup(client: commands.Bot) -> None:
    await client.add_cog(analyticss(client))     
