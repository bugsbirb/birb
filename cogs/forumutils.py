import discord
from discord import ui
import time
import platform
import sys
import discord.ext
from discord.ext import commands
from urllib.parse import quote_plus
from discord import app_commands
import os
from dotenv import load_dotenv
import discord
import datetime
from discord.ext import commands, tasks
from jishaku import Jishaku
from pymongo import MongoClient
from typing import Optional

from emojis import *
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']

class Forums(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_group()
    async def forums(self, ctx):
        return

    async def has_staff_role(self, ctx):
        filter = {
            'guild_id': ctx.guild.id
        }
        staff_data = scollection.find_one(filter)

        if staff_data and 'staffrole' in staff_data:
            staff_role_id = staff_data['staffrole']
            staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_id)

            if staff_role and staff_role in ctx.author.roles:
                return True

        return False


    @forums.command(description="Lock a forum thread")        
    async def lock(self, ctx):
     if not await self.has_staff_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return              
     if isinstance(ctx.channel, discord.Thread):        
        await ctx.channel.edit(locked=True, reason=f"{ctx.author.display_name}, locked the forum")
        await ctx.send(f"{tick} Forum **Locked.**")
     else:   
        await ctx.send(f"{no} This command only works in **forum channels.**")

    @forums.command(description="Unlock a forum thread")        
    async def unlock(self, ctx):
     if not await self.has_staff_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return              
     if isinstance(ctx.channel, discord.Thread):        
        await ctx.channel.edit(locked=False, reason=f"{ctx.author.display_name}, unlocked the forum")
        await ctx.send(f"{tick} Forum **Unlocked.**")
     else:   
        await ctx.send(f"{no} This command only works in **forum channels.**")

    @forums.command(description="Archive a forum thread")        
    async def archive(self, ctx):
     if not await self.has_staff_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return            
     if isinstance(ctx.channel, discord.Thread):        
        await ctx.send(f"{tick} Forum **Archived.**")
        await ctx.channel.edit(archived=True, reason=f"{ctx.author.display_name}, archived the forum")
     else:   
        await ctx.send(f"{no} This command only works in **forum channels.**")



async def setup(client: commands.Bot) -> None:
    await client.add_cog(Forums(client))     
                
