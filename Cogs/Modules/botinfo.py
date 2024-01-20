import discord
from discord.ext import commands
from discord.ext import commands
import platform
from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
infractions = db['infractions']
suggestions_collection = db["suggestions"]
loa_collection = db['loa']
class botinfo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(name="botinfo", description="Statstics + Information about the bot.")
    async def botinfo(self, ctx):
        infractions_count = await infractions.count_documents({})
        loa_count = await loa_collection.count_documents({})        
        embed = discord.Embed(title="**Astro Birb**", description=f"**Discord.py Version:** {discord.__version__}\n**Python Version:** {str(platform.python_version())}\n**Database:** MongoDB", color=discord.Color.dark_embed())
        embed.add_field(name="Developers", value="**[@bugsbirt](<https://discord.com/users/795743076520820776>)**\n**[@zippybonzo](<https://discord.com/users/1125518069482139658>)**\n**[@mark.api](<https://discord.com/users/856971748549197865>)**")
        embed.add_field(name="Links", value="[**Support Server**](https://discord.gg/Qsz6DyGMTB)\n[**Upvote Astro Birb**](https://top.gg/bot/1113245569490616400/vote)")
        embed.add_field(name="Stats", value=f"**Global Users:** {len(self.client.users)}\n**Server Count:** {len(self.client.guilds)}\n**Infractions:** {infractions_count}\n**LOAs:** {loa_count}")
        embed.set_thumbnail(url=self.client.user.avatar.url)
        await ctx.send(embed=embed)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(botinfo(client))     
