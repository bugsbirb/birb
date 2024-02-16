import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
import os
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
blacklists = db['blacklists']

class GuildJoins(commands.Cog):
    def __init__(self, client):
        self.client = client



    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        blacklist = await blacklists.find_one({'user': guild.owner.id})
        if blacklist:  
            blacklisted = {tick}
        else:
            blacklisted = {no}
        
        embed = discord.Embed(title=f"Astro Birb - {guild.name}", description=f"<:Arrow:1115743130461933599>**Owner:** {guild.owner.mention}\n<:Arrow:1115743130461933599>**Guild:** {guild.name}\n<:Arrow:1115743130461933599>**Guild ID** {guild.id}\n <:Arrow:1115743130461933599>**Members:** {guild.member_count}\n<:Arrow:1115743130461933599>**Created:** <t:{guild.created_at.timestamp():.0f}:F>\n<:Arrow:1115743130461933599>**Blacklisted:** {blacklisted}", color=discord.Color.blurple())
        embed.set_thumbnail(url=guild.icon)
        channel = self.client.get_channel(1118944466980581376)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild.owner.id is None:
            print(f"Left guild {guild.name} owned by a user that is not in the cache")
            return
        blacklist = await blacklists.find_one({'user': guild.owner.id})
        if blacklist:  
            blacklisted = {tick}
        else:
            blacklisted = {no}        
        embed = discord.Embed(title=f"Astro Birb - {guild.name}", description=f"<:Arrow:1115743130461933599>**Owner:** {guild.owner.mention}\n<:Arrow:1115743130461933599>**Guild:** {guild.name}\n<:Arrow:1115743130461933599>**Guild ID** {guild.id}\n <:Arrow:1115743130461933599>**Members:** {guild.member_count}\n<:Arrow:1115743130461933599>**Created:** <t:{guild.created_at.timestamp():.0f}:F>\n<:Arrow:1115743130461933599>**Blacklisted:** {blacklisted}", color=discord.Color.blurple())
        embed.set_thumbnail(url=guild.icon)
        channel = self.client.get_channel(1150816700489535508)
        await channel.send(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(GuildJoins(client))   

