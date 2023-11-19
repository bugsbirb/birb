import discord
import discord
from discord.ext import commands
from typing import Literal
import datetime
from datetime import timedelta
import asyncio
from discord import app_commands
from discord.ext import commands, tasks
import pytz
from pymongo import MongoClient
import platform

class botinfo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(name="botinfo", description="Statstics + Information about the bot.")
    async def botinfo(self, ctx):
        embed = discord.Embed(title="**Astro Birb**", description=f"**Discord.py Version:** {discord.__version__}\n**Python Version:** {str(platform.python_version())}\n**Database:** MongoDB", color=discord.Color.dark_embed())
        embed.add_field(name="Developer", value="**[@bugsbirt](<https://discord.com/users/795743076520820776>)**")
        embed.add_field(name="Links", value="[**Support Server**](https://discord.gg/Qsz6DyGMTB)\n[**Upvote Astro Birb**](https://top.gg/bot/1113245569490616400/vote)")
        embed.add_field(name="Stats", value=f"**Global Users:** {len(self.client.users)}\n**Server Count:** {len(self.client.guilds)}")
        embed.set_thumbnail(url=self.client.user.avatar.url)
        await ctx.send(embed=embed)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(botinfo(client))     
