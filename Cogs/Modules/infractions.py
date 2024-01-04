import sqlite3
import discord
from discord.ext import commands
from typing import Literal
import random
import string
import asyncio
from typing import Union, Optional
import sqlite3
from discord.ext import commands
import datetime
from discord import app_commands
import Paginator
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from emojis import *
from permissions import *
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
collection = db['infractions']
scollection = db['staffrole']
arole = db['adminrole']
infchannel = db['infraction channel']
appealable = db['Appeal Toggle']
appealschannel = db['Appeals Channel']
consent = db['consent']
modules = db['Modules']




class Infractions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client



    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['infractions'] == True:   
        return True

     
    @commands.hybrid_command(description="Infract staff members")
    async def infract(self, ctx, staff: discord.Member, reason: str, action: Literal['Activity Notice', 'Verbal Warning', 'Warning', 'Strike', 'Demotion', 'Termination'], notes: Optional[str]):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return    

        if not await has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return           

        if ctx.author == staff:
         await ctx.send(f"{no} **{ctx.author.display_name}**, you can't infract yourself.")
         return

        random_string = ''.join(random.choices(string.digits, k=8))
        if notes:
         embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Notes:** {notes}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
        else:
         embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=staff.display_avatar)
        embed.set_author(name=f"Signed, {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
        embed.set_footer(text=f"Infraction ID | {random_string}")
        infract_data = {
            'management': ctx.author.id,
            'staff': staff.id,
            'action': action,
            'reason': reason,
            'notes': notes,
            'random_string': random_string,
            'guild_id': ctx.guild.id
        }

        guild_id = ctx.guild.id
        data = infchannel.find_one({'guild_id': guild_id})
        consent_data = consent.find_one({"user_id": staff.id})
        if consent_data is None:
            consent.insert_one({"user_id": staff.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled"})            
            consent_data = {"user_id": staff.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled"}


        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:      

            try:
             await channel.send(f"{staff.mention}", embed=embed)
             await ctx.send(f"{tick} **{ctx.author.display_name}**, I've infracted **@{staff.display_name}**")
             collection.insert_one(infract_data)
            except discord.Forbidden: 
             await ctx.send(f"{no} I don't have permission to view that channel.")             
             return
            if consent_data['infractionalert'] == "Enabled":
             try:
                await staff.send(f"<:SmallArrow:1140288951861649418> From **{ctx.guild.name}**", embed=embed)
             except discord.Forbidden:
                pass
            else:
                pass
         else:
            await ctx.send(f"{Warning} {ctx.author.display_name}, I don't have permission to view this channel.")
        else:
          await ctx.send(f"{Warning} **{ctx.author.display_name}**, the channel is not setup please run `/config`")

    @commands.hybrid_command(description="View a staff members infractions")
    async def infractions(self, ctx, staff: discord.Member):
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return    

     if not await has_staff_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return               

     print(f"Searching infractions for staff ID: {staff.id} in guild ID: {ctx.guild.id}")

     filter = {
        'guild_id': ctx.guild.id,
        'staff': staff.id,
    }

     infractions = collection.find(filter)

     infraction_list = []

     for infraction in infractions:
        infraction_info = {
            'id': infraction['random_string'],
            'action': infraction['action'],
            'reason': infraction['reason'],
            'notes': infraction['notes'],
            'management': infraction['management']
        }
        infraction_list.append(infraction_info)

     if not infraction_list:
        await ctx.send(f"{no} **{ctx.author.display_name}**, there is no infractions found for **@{staff.display_name}**.")
        return

     print(f"Found {len(infraction_list)} infractions for {staff.display_name}")

     embed = discord.Embed(
        title=f"{staff.name}'s Infractions",
        description=f"* **User:** {staff.mention}\n* **User ID:** {staff.id}",
        color=discord.Color.dark_embed()
    )
     embed.set_thumbnail(url=staff.display_avatar)
     embed.set_author(icon_url=staff.display_avatar, name=staff.display_name)
     for infraction_info in infraction_list:
        management = await self.client.fetch_user(infraction_info['management'])        
        embed.add_field(
            name=f"<:Document:1166803559422107699> Infraction | {infraction_info['id']}",
            value=f"<:arrow:1166529434493386823>**Infracted By:** {management.mention}\n<:arrow:1166529434493386823>**Action:** {infraction_info['action']}\n<:arrow:1166529434493386823>**Reason:** {infraction_info['reason']}\n<:arrow:1166529434493386823>**Notes:** {infraction_info['notes']}",
            inline=False
        )

     await ctx.send(embed=embed)

    @commands.hybrid_group()
    async def infraction(self, ctx):
        return

    @infraction.command(description="Void a staff member's infraction")
    async def void(self, ctx, id: str):
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return         
     if not await has_admin_role(ctx):
        await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
        return

     filter = {
        'guild_id': ctx.guild.id,
        'random_string': id
    }

     infraction = collection.find_one(filter)

     if infraction is None:
        await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find the infraction with ID `{id}` in this guild.")
        return

     collection.delete_one(filter)
 
     await ctx.send(f"{tick} **{ctx.author.display_name}**, I've voided the infraction with ID `{id}` in this guild.")
     



async def setup(client: commands.Bot) -> None:
    await client.add_cog(Infractions(client))       