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
from typing import Literal, Optional
import os
from dotenv import load_dotenv
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
tags = db['tags']
modules = db['Modules']
ApplicationsChannel = db['Applications Channel']
ApplicationsRolesDB = db['Applications Roles']
class ApplicationResults(commands.Cog):
    def __init__(self, client):
        self.client = client
 
    async def has_staff_role(self, ctx):
     filter = {
        'guild_id': ctx.guild.id
    }
     staff_data = scollection.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_ids)
        if not isinstance(staff_role_ids, list):
          staff_role_ids = [staff_role_ids]   
        if any(role.id in staff_role_ids for role in ctx.author.roles):
            return True

     return False


    async def has_admin_role(self, ctx):
     filter = {
        'guild_id': ctx.guild.id
    }
     staff_data = arole.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_ids)
        if not isinstance(staff_role_ids, list):
          staff_role_ids = [staff_role_ids]     
        if any(role.id in staff_role_ids for role in ctx.author.roles):
            return True

     return False

    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Applications'] == True:   
        return True


    @commands.hybrid_group()
    async def application(self, ctx):
        return

    @application.command(description="Log Application results")
    async def results(
        self,
        ctx,
        applicant: discord.Member,
        result: Literal["Passed", "Failed"],
        *,
        feedback,
    ):

        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return    

        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return           


        if result == "Passed":
            if not feedback:
                feedback = "None Given"
            embed = discord.Embed(
                title=f"<:Tick_1:1178749612929069096> Application Passed",
                description=f"**Applicant:** {applicant.mention}\n**Feedback:** {feedback}",
                color=discord.Color.brand_green(),
            )
        elif result == "Failed":
            if not feedback:
                feedback = "None Given"
            embed = discord.Embed(
                title=f"<:crossX:1140623638207397939> Application Failed",
                description=f"**Applicant:** {applicant.mention}\n**Feedback:** {feedback}",
                color=discord.Color.brand_red(),
            )
        embed.set_thumbnail(url=applicant.display_avatar)
        embed.set_author(
            name=f"Reviewed by {ctx.author.display_name.capitalize()}",
            icon_url=ctx.author.display_avatar,
        )
        
        channeldata = ApplicationsChannel.find_one({"guild_id": ctx.guild.id})
        if channeldata:
            channelid = channeldata["channel_id"]
            channel = self.client.get_channel(channelid)
            if channel:
                try:
                    msg = await channel.send(f"{applicant.mention}", embed=embed)
                    await ctx.send(f"{tick} **{ctx.author.display_name}**, submitted application results for **@{applicant.display_name}**")
                except discord.Forbidden:
                    await ctx.send(
                        f"{no} **{ctx.author.display_name}**, I don't have permission to send messages in {channel.mention}."
                    )                    
                view = JumpUrl(msg.jump_url)
                try:
                 await applicant.send(f"<:ApplicationFeedback:1178754449125167254> **{applicant.display_name}**, you application has been reviewed.", view=view)
                except discord.Forbidden:
                  pass
                if result == 'Passed':
                     roles_data = ApplicationsRolesDB.find_one({"guild_id": ctx.guild.id})
                     if roles_data:
                      application_roles = roles_data.get("applicationroles", [])
                      member = ctx.guild.get_member(applicant.id)
                      roles_to_add = [discord.utils.get(ctx.guild.roles, id=role_id) for role_id in application_roles]
                      if roles_to_add and None not in roles_to_add:
                            try:
                                await member.add_roles(*roles_to_add)
                            except discord.Forbidden as e:
                             await ctx.send(f"{no} **{ctx.author.display_name},** Please check if I have permission to add roles and if I'm higher than the role.")
                             return

                        
            else:           
                await ctx.send(
                    f"{no} {ctx.author.display_name}, the specified channel doesn't exist."
                )
        else:
            await ctx.send(
                f"{no} {ctx.author.display_name}, this channel isn't configured. Please do `/config`."
            )
class JumpUrl(discord.ui.View):
    def __init__(self, jumpurl):
        super().__init__()
        url = jumpurl
        self.add_item(discord.ui.Button(label='Results', url=url, style=discord.ButtonStyle.blurple))

async def setup(client: commands.Bot) -> None:
    await client.add_cog(ApplicationResults(client))        