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
     if guild.owner.id in blacklist:
        await guild.leave()
        print(f'Left guild {guild.name} owned by blacklisted user {guild.owner}')


    @commands.command()
    @commands.is_owner()
    async def blacklist(self, ctx, user: discord.Member):
        user = self.client.fetch_user(user.id)
        await blacklists.insert_one({'user': user.id})







async def setup(client: commands.Bot) -> None:
    await client.add_cog(blacklist(client))     
