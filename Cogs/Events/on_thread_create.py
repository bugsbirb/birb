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
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
forumsconfig = db['Forum Configuration']
modules = db['Modules']

class ForumCreaton(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        guild_id = thread.guild.id
        config_data = forumsconfig.find_one({"guild_id": guild_id})
        if not config_data or "channel_id" not in config_data:
         return

        if thread.guild.id != guild_id:
            return
        if thread.parent_id != config_data['channel_id']:
            return
        await asyncio.sleep(1)
        if config_data:
         if config_data["embed"] == True:   
          embed = discord.Embed(title=config_data["title"], description=config_data["description"], color=discord.Color.dark_embed())
          thumbnail_url = config_data['thumbnail']
          if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)

          role = discord.utils.get(thread.guild.roles, id=config_data['role'])

          mention = role.mention if role else ""
          msg = await thread.send(content=f"{mention}", embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
         else:
            role = discord.utils.get(thread.guild.roles, id=config_data['role'])
            mention = role.mention if role else ""
            msg = await thread.send(content=f"{mention}")     


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ForumCreaton(client))   