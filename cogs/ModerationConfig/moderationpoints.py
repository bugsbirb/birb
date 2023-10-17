
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

mongo = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = mongo['astro']
WarningPointValue = db['Warning Value']
MutePointValue = db['Mute Value']
KickPointValue = db['Kick Value']
SoftBanPointValue = db['Softban Value']
BanPointValue = db['Ban Value']
AutoBanValue = db['Points Autoban Config']
MaxPointValue = db['Max Point Value']
class PointsValues(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.autoban_toggled = False


    @discord.ui.button(label='Warn Value', style=discord.ButtonStyle.grey)
    async def WarnValue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WarnValue())

    @discord.ui.button(label='Mute Value', style=discord.ButtonStyle.grey)
    async def MuteValue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MuteValue())

    @discord.ui.button(label='Kick Value', style=discord.ButtonStyle.grey)
    async def KickValue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(KickValue())

    @discord.ui.button(label='Ban Value', style=discord.ButtonStyle.grey)
    async def BanValue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(Ban())        

    @discord.ui.button(label='Max Points Value', style=discord.ButtonStyle.grey)
    async def MaxValue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MaxPoints())    

    @discord.ui.button(label='Autoban', style=discord.ButtonStyle.blurple)
    async def toggle_autoban(self, interaction: discord.Interaction, button: discord.ui.Button):
     self.autoban_toggled = not self.autoban_toggled
     guild_id = interaction.guild.id
     if self.autoban_toggled:
        AutoBanValue.update_one({'guild_id': guild_id}, {'$set': {'toggle': self.autoban_toggled}}, upsert=True)
     else:
        AutoBanValue.delete_one({'guild_id': guild_id})
     await interaction.response.send_message(content=f"{tick} Autoban {'enabled' if self.autoban_toggled else 'disabled'}", ephemeral=True)

class WarnValue(discord.ui.Modal, title='Warnings'):
    def __init__(self):
        super().__init__()

    WarnPointValue = discord.ui.TextInput(
        label='How many points does a warn give?',
        placeholder='',
    )

    async def on_submit(self, interaction: discord.Interaction):
     value = self.WarnPointValue.value
     WarningPointValue.update_one({'guild_id': interaction.guild.id}, {'$set': {'pointvalue': value}}, upsert=True)
     await interaction.response.send_message(content=f"{tick} Successfully set the Warns Points Value as `{value}`", ephemeral=True)

class MuteValue(discord.ui.Modal, title='Mute'):
    def __init__(self):
        super().__init__()

    WarnPointValue = discord.ui.TextInput(
        label='How many points does a mute give?',
        placeholder='',
    )

    async def on_submit(self, interaction: discord.Interaction):
     value = self.WarnPointValue.value
     MutePointValue.update_one({'guild_id': interaction.guild.id}, {'$set': {'pointvalue': value}}, upsert=True)
     await interaction.response.send_message(content=f"{tick} Successfully set the Mute Points Value as `{value}`", ephemeral=True)

class KickValue(discord.ui.Modal, title='Kicks'):
    def __init__(self):
        super().__init__()

    WarnPointValue = discord.ui.TextInput(
        label='How many points does a kick give?',
        placeholder='',
    )

    async def on_submit(self, interaction: discord.Interaction):
     value = self.WarnPointValue.value
     KickPointValue.update_one({'guild_id': interaction.guild.id}, {'$set': {'pointvalue': value}}, upsert=True)
     await interaction.response.send_message(content=f"{tick} Successfully set the Kicks Points Value as `{value}`", ephemeral=True)


class Ban(discord.ui.Modal, title='Ban'):
    def __init__(self):
        super().__init__()

    WarnPointValue = discord.ui.TextInput(
        label='How many points does a Ban give?',
        placeholder='',
    )

    async def on_submit(self, interaction: discord.Interaction):
     value = self.WarnPointValue.value
     BanPointValue.update_one({'guild_id': interaction.guild.id}, {'$set': {'pointvalue': value}}, upsert=True)
     await interaction.response.send_message(content=f"{tick} Successfully set the Ban Points Value as `{value}`", ephemeral=True)


class MaxPoints(discord.ui.Modal, title='Ban'):
    def __init__(self):
        super().__init__()

    WarnPointValue = discord.ui.TextInput(
        label='Whats the max amount of points you can reach',
        placeholder='',
    )

    async def on_submit(self, interaction: discord.Interaction):
     value = self.WarnPointValue.value
     MaxPointValue.update_one({'guild_id': interaction.guild.id}, {'$set': {'pointvalue': int(value)}}, upsert=True)
     await interaction.response.send_message(content=f"{tick} Successfully set the MaxPoints Value as `{value}`", ephemeral=True)