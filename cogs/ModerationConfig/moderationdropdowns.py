
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
from cogs.ModerationConfig.moderationpermissions import *
from cogs.ModerationConfig.moderationchannels import *
from cogs.ModerationConfig.moderationpoints import *

class ModerationConfig(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Moderation Permissions', emoji='<:Config:1148610134147338381>'),
            discord.SelectOption(label='Logging', emoji=f'{folder}'),
            discord.SelectOption(label="Points", emoji=f'<:Infraction:1162134605885870180>')

        
            
        ]
        super().__init__(placeholder='Config Menu', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if color == 'Moderation Permissions':
            embed = discord.Embed(title="Moderation Permissions", description="* **Warning Role**\n> What users can warn people?\n\n* **Muting Role**\n> What users can mute people?\n\n* **Kicking Role**\n> What users can kick people?\n\n* **Banning Role**\n> What users can ban people?", color=discord.Color.dark_embed())
            embed.set_author(icon_url=interaction.guild.icon, name=interaction.guild.name)
            embed.set_thumbnail(url=interaction.guild.icon)
            view = ModerationPerms()
        if color == 'Logging':    
            embed = discord.Embed(title="Logging Channel", description="* **What does this actually log?**\n> In this channel it logs, `autobans`, `warnings`, `mutes`, `kicks`, `bans`.", color=discord.Color.dark_embed())
            embed.set_author(icon_url=interaction.guild.icon, name=interaction.guild.name)
            embed.set_thumbnail(url=interaction.guild.icon)            
            view = ModerationsChannel()

        if color == 'Points':    
            view = PointsValues()
            embed = discord.Embed(title="Point Values", description="* **What do the values represent?**\n> The values respresents how many points does a punishment give for each punishment.\n\n* **What does autoban do?**\n> Once the user reaches the max points it'll autoban them if this is toggled on.\n\n* **What is the max value for?**\n> The max value is the max value before it prompts a message saying they've reached the max amount of points.", color=discord.Color.dark_embed())
            embed.set_author(icon_url=interaction.guild.icon, name=interaction.guild.name)
            embed.set_thumbnail(url=interaction.guild.icon) 
        await interaction.response.edit_message(embed=embed, view=view)
class ModerationConfigdrop(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ModerationConfig())
