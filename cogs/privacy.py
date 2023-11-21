import discord
from discord.ext import commands
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import pytz
from discord import app_commands
from pymongo import MongoClient
from emojis import *
import typing
import Paginator
import os
from dotenv import load_dotenv

class privacy(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(name="privacy", description="Statstics + Information about the bot.")
    async def privacy(self, ctx):
        embed = discord.Embed(title="**Astro Birb Privacy**")
        embed.add_field(name="Data Management", value="All your data is automatically deleted from the bot after 30 days of inactivity (defined by not running a command.)")
        embed.add_field(name="Help", value="To prevent automatic deletion of data contact us in our [**Support Server**](https://discord.gg/Qsz6DyGMTB)")
        embed.add_field(name="Coming soon", value=f"Data management module")
        embed.set_thumbnail(url=self.client.user.avatar.url)
        await ctx.send(embed=embed)
    
async def setup(client: commands.Bot) -> None:
    await client.add_cog(privacy(client))             
