import discord
from discord.ext import commands, tasks
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


class GuildJoins(commands.Cog):
    def __init__(self, client):
        self.client = client



    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title=f"Astro Birb - {guild.name}", description=f"<:Arrow:1115743130461933599>**Owner:** {guild.owner.mention}\n<:Arrow:1115743130461933599>**Guild:** {guild.name}\n<:Arrow:1115743130461933599>**Guild ID** {guild.id}\n <:Arrow:1115743130461933599>**Members:** {guild.member_count}\n<:Arrow:1115743130461933599>**Created:** <t:{guild.created_at.timestamp():.0f}:F>", color=discord.Color.blurple())
        embed.set_thumbnail(url=guild.icon)
        channel = self.client.get_channel(1118944466980581376)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        embed = discord.Embed(title=f"Astro Birb - {guild.name}", description=f"<:Arrow:1115743130461933599>**Owner:** {guild.owner.mention}\n<:Arrow:1115743130461933599>**Guild:** {guild.name}\n<:Arrow:1115743130461933599>**Guild ID** {guild.id}\n <:Arrow:1115743130461933599>**Members:** {guild.member_count}\n<:Arrow:1115743130461933599>**Created:** <t:{guild.created_at.timestamp():.0f}:F>", color=discord.Color.blurple())
        embed.set_thumbnail(url=guild.icon)
        channel = self.client.get_channel(1150816700489535508)
        await channel.send(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(GuildJoins(client))   

