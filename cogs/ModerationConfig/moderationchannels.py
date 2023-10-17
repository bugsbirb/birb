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
ModerationChannel = db['Moderations Channel']

class ModlogsChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder='Moderation Logging Channel')

    async def callback(self, interaction: discord.Interaction):
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = ModerationChannel.find_one(filter)

            if existing_record:
                ModerationChannel.update_one(filter, {'$set': data})
            else:
                ModerationChannel.insert_one(data)
               
            await interaction.response.edit_message(content=f"{tick} Configuration Updated", embed=None, view=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")

class ModerationsChannel(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ModlogsChannel())
