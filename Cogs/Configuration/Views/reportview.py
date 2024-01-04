
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
from Cogs.Configuration.Configuration import *

import os
MONGO_URL = os.getenv('MONGO_URL')

mongo = MongoClient(MONGO_URL)
db = mongo['astro']
modules = db['Modules']
scollection = db['staffrole']
arole = db['adminrole']
LOARole = db['LOA Role']
infchannel = db['infraction channel']
repchannel = db['report channel']
loachannel = db['loa channel']
promochannel = db['promo channel']
feedbackch = db['Staff Feedback Channel']
partnershipch = db['partnership channel']
appealable = db['Appeal Toggle']
appealschannel = db['Appeals Channel']
loachannel = db['LOA Channel']
partnershipsch = db['Partnerships Channel']
modules = db['Modules']
ReportModeratorRole = db['Report Moderator Role']

class ReportChannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(placeholder='Report Channel')
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                  
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = repchannel.find_one(filter)

            if existing_record:
                repchannel.update_one(filter, {'$set': data})
            else:
                repchannel.insert_one(data)

            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")        

class ReportsModeratorRole(discord.ui.RoleSelect):
    def __init__(self, author):
        super().__init__(placeholder='Reports Moderator')
        self.author = author
        
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_id = self.values[0]

        filter = {
            'guild_id': interaction.guild.id
        }        
        data = {
            'guild_id': interaction.guild.id, 
            'staffrole': selected_role_id.id  
        }
        try:
            existing_record = ReportModeratorRole.find_one(filter)

            if existing_record:
                ReportModeratorRole.update_one(filter, {'$set': data})
            else:
                ReportModeratorRole.insert_one(data)

            await interaction.response.edit_message( content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"selected_role_id: {selected_role_id.id}")

class ToggleReportsDropdown(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Enable"),
            discord.SelectOption(label="Disable"),
            

        
            
        ]
        super().__init__(placeholder='Module Toggle', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        if color == 'Enable':    
            await interaction.response.send_message(content=f"{tick} Enabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Reports': True}}, upsert=True)  

        if color == 'Disable':    
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Reports': False}}, upsert=True)            

    