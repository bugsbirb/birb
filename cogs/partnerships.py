import discord
from discord.ext import commands, tasks
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import pytz
from discord import app_commands
from typing import Literal
from typing import Optional
from pymongo import MongoClient
from emojis import *
import typing
import os
from dotenv import load_dotenv
import Paginator
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
partnerships = db['Partnerships']
partnershipsch = db['Partnerships Channel']
modules = db['Modules']
class Partnerships(commands.Cog):
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

    async def servers_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        filter = {
            'guild_id': interaction.guild_id 
        }

        tag_names = partnerships.distinct("server", filter)

        filtered_names = [name for name in tag_names if current.lower() in name.lower()]

        choices = [app_commands.Choice(name=name, value=name) for name in filtered_names]

        return choices

    @commands.hybrid_group()
    async def partnership(self, ctx):
        pass

    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Partnerships'] == True:   
        return True

    @partnership.command(description="Log a partnership")
    async def log(self, ctx, owner: discord.Member, server: str, invite: str):

        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            

        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return      
        data = partnershipsch.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
          await ctx.send(f"{tick} **Partnership** logged.")
          partnershipdata = {
            'guild_id': ctx.guild.id,
            'owner': owner.id,
            'admin': ctx.author.id,
            'invite': invite,
            'server': server
        }

          partnerships.insert_one(partnershipdata)
          embed = discord.Embed(title=f"{(server).capitalize()}", description=f"* **Owner:** {owner.mention}\n* **Invite:** {invite}", color=discord.Color.dark_embed())
          embed.set_author(name=f"Partnership logged by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
          embed.set_thumbnail(url=owner.display_avatar)
          try:
           await channel.send(embed=embed)
          except discord.Forbidden: 
            await ctx.send(f"{no} I don't have permission to view that channel.")
        else:  
         await ctx.send(f"{no} **{ctx.author.display_name}**, the channel is not setup please run `/config`")

    @partnership.command(description="Terminate a server partnership")     
    @app_commands.autocomplete(server=servers_autocomplete)    
    async def terminate(self, ctx, server, reason: str):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            

        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return              


        partnership_data = partnerships.find_one({'guild_id': ctx.guild.id, 'server': server})
        if partnership_data is None:   
            await ctx.send(f"{no} I could not find that partnership.")
            return
        if partnership_data:
            server = partnership_data['server']
            ownerid = partnership_data['owner']
            invite = partnership_data['invite']            
            owner = ctx.guild.get_member(ownerid)

        data = partnershipsch.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
          await ctx.send(f"{tick} **Partnership** terminiated.")

          embed = discord.Embed(title=f"{(server).capitalize()} Terminated", description=f"* **Owner:** {owner.mention}\n* **Invite:** {invite}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
          embed.set_author(name=f"Partnership terminiated by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
          embed.set_thumbnail(url=owner.display_avatar)
          try:
           await channel.send(embed=embed)
          except discord.Forbidden: 
            await ctx.send(f"{no} I don't have permission to view that channel.")           
          partnerships.delete_one({'guild_id': ctx.guild.id, 'server': server})
        else:  
         await ctx.send(f"{no} **{ctx.author.display_name}**, the channel is not setup please run `/config`")        

    @partnership.command(description="View all Partnerships in this server.")
    async def all(self, ctx):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            

        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return              
        partnership_data = partnerships.find({'guild_id': ctx.guild.id})
        if not partnership_data:
            await ctx.send(f"No active partnerships on this server.")
            return

        embeds = []

        for partnership in partnership_data:
            server = partnership['server']
            owner_id = partnership['owner']
            invite = partnership['invite']
            admin_id = partnership['admin']
            admin = ctx.guild.get_member(admin_id)
            owner = ctx.guild.get_member(owner_id)
            
            embed = discord.Embed(title="Active Partnerships", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=ctx.guild.icon)
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            embed.add_field(name=server, value=f"> **Invite:** {invite}\n> **Owner:** {owner.mention}\n> **Logged By:** {admin.display_name}")

            embeds.append(embed)

        if not embeds:
            await ctx.send(f"No active partnerships on this server.")
            return

        PreviousButton = discord.ui.Button(label="<")
        NextButton = discord.ui.Button(label=">")
        FirstPageButton = discord.ui.Button(label="<<")
        LastPageButton = discord.ui.Button(label=">>")
        InitialPage = 0
        timeout = 42069

        paginator = Paginator.Simple(
            PreviousButton=PreviousButton,
            NextButton=NextButton,
            FirstEmbedButton=FirstPageButton,
            LastEmbedButton=LastPageButton,
            InitialPage=InitialPage,
            timeout=timeout
        )

        await paginator.start(ctx, pages=embeds)


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        partnership_data = partnerships.find_one({'guild_id': member.guild.id})

        if partnership_data and partnership_data['owner'] == member.id:
            partnerships.delete_one({'guild_id': member.guild.id, 'owner': member.id})
            print(f"@{member.guild.name} partnership terminated")
            server = partnership_data['server']
            adminid = partnership_data['admin']
            invite = partnership_data['invite']            
            admin = member.guild.get_member(adminid)
            data = partnershipsch.find_one({'guild_id': member.guild.id})
            if data:
                channel_id = data['channel_id']
                channel = self.client.get_channel(channel_id)
                print(f"@{member.guild.name} partnership channel found")
                if channel:
                    embed = discord.Embed(title="Partnership Termination", description=f"* **Owner:** {member.mention}\n* **Server:** {server}\n* **Invite:** {invite}\n* **Reason:** Owner of **@{server}** left this server.", color=discord.Color.dark_embed())
                    embed.set_thumbnail(url=member.display_avatar)
                    embed.set_author(name=f"{server}", icon_url=member.display_avatar)
                    await channel.send(embed=embed)
                    print(f"@{member.guild.name} partnership revoke message sent")



async def setup(client: commands.Bot) -> None:
    await client.add_cog(Partnerships(client))      