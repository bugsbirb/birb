import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
blacklists = db['blacklists']

class blacklist(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
     blacklist = await blacklists.find_one({'user': guild.owner.id})

     if blacklist:
        await guild.leave()
        print(f'Left guild {guild.name} owned by blacklisted user {guild.owner}')
     else:
       pass
    


    @commands.command()
    @commands.is_owner()
    async def blacklist(self, ctx, id: int):
        await blacklists.insert_one({'user': id})







async def setup(client: commands.Bot) -> None:
    await client.add_cog(blacklist(client))     
