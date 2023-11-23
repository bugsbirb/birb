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
from cogs.ConfigurationFolder.Configuration2 import *

import os
MONGO_URL = os.getenv('MONGO_URL')

mongo = MongoClient('mongodb://bugsbirt:deezbird2768@172.93.103.8:55199/?authMechanism=SCRAM-SHA-256&authSource=admin')
dbq = mongo['quotab']
message_quota_collection = dbq["message_quota"]

client = MongoClient(MONGO_URL)
db = client['astro']
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

class QuotaToggle(discord.ui.Select):
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
            await interaction.response.send_message(content="<:Tick:1140286044114268242> Enabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Quota': True}}, upsert=True)  

        if color == 'Disable':    
            await interaction.response.send_message(content="<:X_:1140286086883586150> Disabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Quota': False}}, upsert=True) 


class QuotaAmount(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="100"),
            discord.SelectOption(label="200"),
            discord.SelectOption(label="300"),
            discord.SelectOption(label="500"),        
            discord.SelectOption(label="Custom Amount"),                   
        ]
        super().__init__(placeholder='Quota Amount', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        if color == 'Custom Amount':        
            await interaction.response.send_modal(MessageQuota())
        else:    
         message_quota_collection.update_one(
            {'guild_id': interaction.guild.id},
            {'$set': {'quota': color}},
            upsert=True  
        )            
         await interaction.response.edit_message(content=None)

class MessageQuota(discord.ui.Modal, title='Quota Amount'):

    quota = discord.ui.TextInput(
        label='Message Quota',
        placeholder='Enter the guild\'s message quota here...',
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            quota_value = int(self.quota.value)
        except ValueError:
            await interaction.response.send_message('Invalid input. Please enter a valid number for the message quota.', ephemeral=True)
            return


        guild_id = interaction.guild.id

        message_quota_collection.update_one(
            {'guild_id': guild_id},
            {'$set': {'quota': quota_value}},
            upsert=True  
        )
        await interaction.response.send_message(content=f"{tick} Succesfully updated message quota.", ephemeral=True)