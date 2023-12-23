import discord
from discord.ext import commands, tasks
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import pytz
from discord import app_commands
from pymongo import MongoClient
from emojis import *
import typing
import Paginator
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
connectionroles = db['connectionroles']

class ConnectionRolesEvent(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        added_roles = set(after.roles) - set(before.roles)
        removed_roles = set(before.roles) - set(after.roles)


        for role in added_roles:
            parent_role_data = await connectionroles.find_one({"parent": role.id})
            if parent_role_data:
                child_role_id = parent_role_data["child"]
                
                child_role = after.guild.get_role(child_role_id)
                if child_role:
                    await after.add_roles(child_role)


        for role in removed_roles:
            parent_role_data = await connectionroles.find_one({"parent": role.id})
            if parent_role_data:
                child_role_id = parent_role_data["child"]
                
                child_role = after.guild.get_role(child_role_id)
                if child_role:
                    await after.remove_roles(child_role)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(ConnectionRolesEvent(client))   