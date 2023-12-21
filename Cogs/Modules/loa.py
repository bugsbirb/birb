import discord
import sqlite3
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
from emojis import * 
import time
import os
from dotenv import load_dotenv
from datetime import datetime
import re
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
loa_collection = db['loa']
loachannel = db['LOA Channel']
scollection = db['staffrole']
arole = db['adminrole']
LOARole = db['LOA Role']
modules = db['Modules']
class loamodule(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.check_loa_status.start()




    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['LOA'] == True:   
        return True

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
        if not isinstance(staff_role_ids, list):
          staff_role_ids = [staff_role_ids]     
        if any(role.id in staff_role_ids for role in ctx.author.roles):
            return True

     return False

    @commands.hybrid_group()
    async def loa(self, ctx):
        pass

    @loa.command(description="Request a Leave Of Absence")
    @app_commands.describe(duration="How long do you want the LOA for? (m/h/d/w)", reason="What is the reasonfor this LOA?")
    async def request(self, ctx, duration: str, reason: str):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            
        if not await self.has_staff_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return    
        if not re.match(r'^\d+[mhdw]$', duration):
         await ctx.send(f"{no} **{ctx.author.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.")
         return

        duration_value = int(duration[:-1])
        duration_unit = duration[-1]
        duration_seconds = duration_value

        if duration_unit == 'm':
            duration_seconds *= 60
        elif duration_unit == 'h':
            duration_seconds *= 3600
        elif duration_unit == 'd':
            duration_seconds *= 86400
        elif duration_unit == 'w':    
            duration_seconds *= 604800

        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        embed = discord.Embed(title=f"Loa Request", description=f"* **User:** {ctx.author.mention}\n* **Start Date**: <t:{int(start_time.timestamp())}:f>\n* **End Date:** <t:{int(end_time.timestamp())}:f>\n* **Reason:** {reason}", color=discord.Color.dark_embed())
        embed.set_author(icon_url=ctx.author.display_avatar, name=ctx.author.display_name)
        embed.set_thumbnail(url=ctx.author.display_avatar)
        data = loachannel.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:

          loadata = {'guild_id': ctx.guild.id,
        'user': ctx.author.id,
        'start_time': start_time,
        'end_time': end_time,
        'reason': reason,
        'active': True
        }        
          view = Confirm(loadata, ctx.author, ctx.guild)        
          try:
           await channel.send(embed=embed, view=view)
          except discord.Forbidden:
                await ctx.send(f"{no} Please contact server admins I can't see the LOA Channel.")            
          await ctx.send(f"{tick} LOA Request sent", ephemeral=True)
          print(f"LOA Request @{ctx.guild.name} pending")          
         else:
            await ctx.send(f"{no} {ctx.author.display_name}, I don't have permission to view this channel.")
        else:
          await ctx.send(f"{no} **{ctx.author.display_name}**, the channel is not setup please run `/config`")

      
    @tasks.loop(minutes=10)
    async def check_loa_status(self):
     current_time = datetime.now()

     filter = {'end_time': {'$lte': current_time}}
    
     loa_requests = loa_collection.find(filter)

     for request in loa_requests:
        end_time = request['end_time']
        user_id = request['user']
        guild_id = request['guild_id']
        guild = self.client.get_guild(guild_id)
        user = await self.client.fetch_user(user_id)
        active = request['active']

        if active == True:
         if current_time >= end_time:
            if user:
                await user.send(f"{tick} Your LOA **@{guild.name}** has ended.")
                print(f"End Time: {end_time}")
                print(f"Current Time: {current_time}")
                loa_collection.update_many({'guild_id': guild_id, 'user': user_id}, {'$set': {'active': False}})
                loarole_data = LOARole.find_one({'guild_id': guild.id})
                if loarole_data:
                 loarole = loarole_data['staffrole']
                 if loarole:
                  role = discord.utils.get(guild.roles, id=loarole)
                  if role:
                   member = await guild.fetch_user(user.id)
                   await member.remove_roles(role)       
        else:
            pass


    @loa.command(description="Manage someone leave of Absence")
    async def manage(self, ctx, user: discord.Member):
     if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return            
     await ctx.send(f"<:LOA:1164969910238203995> **Hey,** loa manage has been moved over to `/admin panel`!")




    @loa.command(description="View all Leave Of Absence")
    async def active(self, ctx):
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            
     if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return             
         
     current_time = datetime.now()
     filter = {'guild_id': ctx.guild.id, 'end_time': {'$gte': current_time}, 'active': True}

     loa_requests = list(loa_collection.find(filter))

     if len(loa_requests) == 0:
        await ctx.send(f"{no} **{ctx.author.display_name}**, there aren't any active LOAs in this server.")
     else:
        embed = discord.Embed(
            title="Active LOAs",
            color=discord.Color.dark_embed()
        )
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(icon_url=ctx.guild.icon , name=ctx.guild.name)
        for request in loa_requests:
            user = await self.client.fetch_user(request['user'])
            start_time = request['start_time']
            end_time = request['end_time']
            reason = request['reason']

            embed.add_field(
                name=f"<:LOA:1164969910238203995>{user.name.capitalize()}",
                value=f"<:arrow:1166529434493386823>**Start Date:** <t:{int(start_time.timestamp())}:f>\n<:arrow:1166529434493386823>**End Date:** <t:{int(end_time.timestamp())}:f>\n<:arrow:1166529434493386823>**Reason:** {reason}",
                inline=False
            )

        await ctx.send(embed=embed)




class Confirm(discord.ui.View):
    def __init__(self, loadata, user, guild):
        super().__init__(timeout=None)
        self.loadata = loadata
        self.user = user
        self.guild = guild

    async def has_admin_role(self, interaction):
        filter = {
            'guild_id': interaction.guild.id
        }
        admin_data = arole.find_one(filter)

        if admin_data and 'adminrole' in admin_data:
            admin_role_id = admin_data['adminrole']
            admin_role = discord.utils.get(interaction.guild.roles, id=admin_role_id)
            if admin_role in interaction.user.roles:
                return True

        return False     


    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green, custom_id='persistent_view:confirm', emoji="<:Tick:1140286044114268242>")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):           
        user = self.user
        try:
         await self.user.send(f"{tick} **{self.user.display_name}**, your LOA **@{self.guild.name}** has been accepted.")
        except discord.Forbidden:
                pass          
        loa_collection.insert_one(self.loadata)
        await interaction.response.edit_message(content=f"<:Tick:1140286044114268242> **{interaction.user.display_name}**, I've accepted the LOA", view=None)
        print(f"LOA Request @{self.guild.name} accepted")
        loarole_data = LOARole.find_one({'guild_id': interaction.guild.id})
        if loarole_data:
         loarole = loarole_data['staffrole']
         if loarole:
          role = discord.utils.get(interaction.guild.roles, id=loarole)
          if role:
            await user.add_roles(role)



    @discord.ui.button(label='Deny', style=discord.ButtonStyle.red, custom_id='persistent_view:cancel', emoji="<:X_:1140286086883586150>")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
         await self.user.send(f"{no} **{self.user.display_name}**, your LOA **@{self.guild.name}** has been denied.")        
        except discord.Forbidden:
                pass 
        await interaction.response.edit_message(content=f"<:Tick:1140286044114268242> **{interaction.user.display_name}** I've denied the LOA.", view=None)    
        print(f"LOA Request @{self.guild.name} denied") 


class LOAManage(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author
    @discord.ui.button(label='End', style=discord.ButtonStyle.grey, custom_id='persistent_view:cancel', emoji="<:Exterminate:1164970632262451231>")
    async def End(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.user
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        loadata = {'user': user.id, 'guild_id': interaction.guild.id}    
        loa_collection.delete_one(loadata)
        await interaction.response.edit_message(embed=None, content=f"{tick} Succesfully ended **@{user.display_name}'s** LOA", view=None)
        try:
         await user.send(f"{tick} Your LOA **@{self.guild.name}** has been manually ended.")
        except discord.Forbidden:
                pass 
        loarole_data = LOARole.find_one({'guild_id': interaction.guild.id})
        if loarole_data:
         loarole = loarole_data['staffrole']
         if loarole:
          role = discord.utils.get(interaction.guild.roles, id=loarole)
          if role:
            await user.remove_roles(role)         

async def setup(client: commands.Bot) -> None:
    await client.add_cog(loamodule(client))             