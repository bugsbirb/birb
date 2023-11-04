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
import asyncio
from typing import Literal
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
forumsconfig = db['Forum Configuration']

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

    @forums.command(name="config", description="Configure on forum creation embed")
    @commands.has_permissions(administrator=True)
    async def configuration(self, ctx, option: Literal['Enable', 'Disable'], channel: discord.ForumChannel, role: discord.Role = None, title: str = None, description: str = None, thumbnail: discord.Attachment = None):
        guild_id = ctx.guild.id
        if option == 'Enable':
         config_data = {
        "channel_id": channel.id,
        "role": role.id if role else None,
        "title": title if title else f"<:forum:1162134180218556497> {ctx.guild.name} Support",
        "description": description if description else f"> Welcome to {ctx.guild.name} support please wait for a support resprenstive to respond!",
        "thumbnail": thumbnail.url if thumbnail else None,
        "guild_id": ctx.guild.id
    }
         forumsconfig.update_one({"guild_id": guild_id}, {"$set": config_data}, upsert=True)
         embed = discord.Embed(title="Forum Configuration Updated", description=f"* **Forum Channel:** {channel.mention}\n* **Role:** {role}\n* **Title:** {title}\n* **Description:** {description}\n* **Thumbnail:** {thumbnail}", color=discord.Color.dark_embed())
         embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
         await ctx.send(embed=embed)
        elif option == 'Disable' :
         forumsconfig.delete_one({"guild_id": ctx.guild.id})
         await ctx.send(f"{tick} All Forum configuration data purged.")

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
         embed = discord.Embed(title=config_data["title"], description=config_data["description"], color=discord.Color.dark_embed())
         thumbnail_url = config_data['thumbnail']
         if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)

         role = discord.utils.get(thread.guild.roles, id=config_data['role'])

         mention = role.mention if role else ""
         msg = await thread.send(content=f"{mention}", embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))


    @configuration.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to configure this server.\n<:Arrow:1115743130461933599>**Required:** ``Administrator``")              

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Forums(client))     
                
