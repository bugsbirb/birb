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
from emojis import * 

mongo = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = mongo['astro']
badges = db['User Badges']

class management(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command()
    @commands.is_owner()    
    async def addbadge(self, ctx, user: discord.Member, *, badge):
        badge = {
            'user_id': user.id,
            'badge': badge
        }
        badges.insert_one(badge)  
        await ctx.send(f"{tick} added **`{badge}`** to **@{user.display_name}**")

    @commands.command()
    @commands.is_owner()
    async def removebadge(self, ctx, user: discord.Member, *, badge):
        badge = {
            'user_id': user.id,
            'badge': badge
        }
        badges.delete_one(badge)  
        await ctx.send(f"{tick} removed **`{badge}`** to **@{user.display_name}**")

async def setup(client: commands.Bot) -> None:
    await client.add_cog(management(client))     
