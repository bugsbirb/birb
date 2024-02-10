from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
from emojis import *
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
        await ctx.send(f"{tick} {ctx.author.display_name}, I have blacklisted the user with the id `{id}`")

    @commands.command()
    @commands.is_owner()
    async def unblacklist(self, ctx, id: int):
        result = await blacklists.find_one({'user': id})
        if result:
           await ctx.send(f"{no} {ctx.author.display_name}, The user with the id `{id}` is not blacklisted")
           return
        await blacklists.delete_one({'user': id})
        await ctx.send(f"{tick} {ctx.author.display_name}, I have unblacklisted the user with the id `{id}`")





async def setup(client: commands.Bot) -> None:
    await client.add_cog(blacklist(client))     
