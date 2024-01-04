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


class webGuildJoins(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel_id = 1178362100737916988 
        channel = self.client.get_channel(channel_id)
        if channel:
            webhook = discord.utils.get(await channel.webhooks(), name="Public Bot Logs")

            await webhook.send(f"<:join:1140670830792159373> I am now in {len(self.client.guilds)} guilds.", username=guild.name, avatar_url=guild.icon)
        owner = guild.owner
        view = Support()
        await owner.send(f"🎉 Thank you for adding **Astro Birb** to your server. To get started run </config:1140463441136586784>!\n<:ArrowDropDown:1163171628050563153> Guild `#{len(self.client.guilds)}`", view=view)

class Support(discord.ui.View):
    def __init__(self):
        super().__init__()
        url1 = f'https://discord.gg/DhWdgfh3hN'
        self.add_item(discord.ui.Button(label='Support Server', url=url1, style=discord.ButtonStyle.blurple))
        self.add_item(discord.ui.Button(label='Documentation', url="https://docs.astrobirb.dev/overview", style=discord.ButtonStyle.blurple))

    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel_id = 1178362100737916988 
        channel = self.client.get_channel(channel_id)
        if channel:
            webhook = discord.utils.get(await channel.webhooks(), name="Public Bot Logs")

            await webhook.send(f"<:leave:1140670848664096789> Farewell, **@{guild.name}.** I am now in {len(self.client.guilds)} guilds.", username=guild.name, avatar_url=guild.icon)
        


async def setup(client: commands.Bot) -> None:
    await client.add_cog(webGuildJoins(client))   