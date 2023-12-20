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
        channel_id = 1178362100737916988 
        channel = self.client.get_channel(channel_id)
        if channel:
            webhook = discord.utils.get(await channel.webhooks(), name="Public Bot Logs")

            await webhook.send(f"<:join:1140670830792159373> Welcomed to **@{guild.name}.** I am now in {len(self.client.guilds)} guilds.", username=guild.name, avatar_url=guild.icon)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel_id = 1178362100737916988 
        channel = self.client.get_channel(channel_id)
        if channel:
            webhook = discord.utils.get(await channel.webhooks(), name="Public Bot Logs")

            await webhook.send(f"<:leave:1140670848664096789> Farewell, **@{guild.name}.** I am now in {len(self.client.guilds)} guilds.", username=guild.name, avatar_url=guild.icon)



async def setup(client: commands.Bot) -> None:
    await client.add_cog(GuildJoins(client))   