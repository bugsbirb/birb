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


class ToggleConnectionRoles(discord.ui.Select):
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
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Connection': True}}, upsert=True)    

        if color == 'Disable':    
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Connection': False}}, upsert=True)            

    