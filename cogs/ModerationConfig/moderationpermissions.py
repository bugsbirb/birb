
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
import os
from dotenv import load_dotenv
import platform
from emojis import * 
MONGO_URL = os.getenv('MONGO_URL')


mongo = MongoClient(MONGO_URL)
db = mongo['astro']
pointsmanagerole = db['Points Manage Role']
warningrole = db['WarnRole']
kickrole = db['KickRole']
banrole = db['BanRole']
muterole = db['MuteRole']

class PointsManage(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder='What role can manage points?')

    async def callback(self, interaction: discord.Interaction):
        selected_role_id = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'guild_id': interaction.guild.id, 
            'staffrole': selected_role_id.id  
        }

        try:
            existing_record = pointsmanagerole.find_one(filter)

            if existing_record:
                pointsmanagerole.update_one(filter, {'$set': data})
            else:
                pointsmanagerole.insert_one(data)


            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"selected_role_id: {selected_role_id.id}")

class WarningRole(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder='What role can warn people?')

    async def callback(self, interaction: discord.Interaction):
        selected_role_id = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'guild_id': interaction.guild.id, 
            'staffrole': selected_role_id.id  
        }

        try:
            existing_record = warningrole.find_one(filter)

            if existing_record:
                warningrole.update_one(filter, {'$set': data})
            else:
                warningrole.insert_one(data)


            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"selected_role_id: {selected_role_id.id}")

class MuteRole(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder='What role can mute people?')

    async def callback(self, interaction: discord.Interaction):
        selected_role_id = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'guild_id': interaction.guild.id, 
            'staffrole': selected_role_id.id  
        }

        try:
            existing_record = muterole.find_one(filter)

            if existing_record:
                muterole.update_one(filter, {'$set': data})
            else:
                muterole.insert_one(data)


            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"selected_role_id: {selected_role_id.id}")

class BanRole(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder='What role can ban people?')

    async def callback(self, interaction: discord.Interaction):
        selected_role_id = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'guild_id': interaction.guild.id, 
            'staffrole': selected_role_id.id  
        }

        try:
            existing_record = banrole.find_one(filter)

            if existing_record:
                banrole.update_one(filter, {'$set': data})
            else:
                banrole.insert_one(data)


            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"selected_role_id: {selected_role_id.id}")

class KickRole(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder='What role can kick people?')

    async def callback(self, interaction: discord.Interaction):
        selected_role_id = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'guild_id': interaction.guild.id, 
            'staffrole': selected_role_id.id  
        }

        try:
            existing_record = kickrole.find_one(filter)

            if existing_record:
                kickrole.update_one(filter, {'$set': data})
            else:
                kickrole.insert_one(data)


            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"selected_role_id: {selected_role_id.id}")

class ModerationPerms(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(PointsManage())
        self.add_item(WarningRole())
        self.add_item(MuteRole())
        self.add_item(KickRole())
        self.add_item(BanRole())


        