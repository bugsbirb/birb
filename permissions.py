import discord
import platform
import sys
sys.dont_write_bytecode = True
import discord.ext
from discord.ext import commands
from urllib.parse import quote_plus
from discord import app_commands
import discord
from discord.ext import commands, tasks

from Cogs.Modules.loa import *
import os
from dotenv import load_dotenv
from jishaku import Jishaku
from motor.motor_asyncio import AsyncIOMotorClient
import time
from pymongo import MongoClient
MONGO_URL = os.getenv('MONGO_URL')
mongo = MongoClient(MONGO_URL)
db = mongo['astro']
ReportModeratorRole = db['Report Moderator Role']
scollection = db['staffrole']
arole = db['adminrole']

async def has_staff_role(ctx):
    filter = {'guild_id': ctx.guild.id}
    staff_data = scollection.find_one(filter)

    if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        staff_role_ids = staff_role_ids if isinstance(staff_role_ids, list) else [staff_role_ids]


        admin_data = arole.find_one(filter)


        if not admin_data:

            pass
        else:
            if 'staffrole' in admin_data:
                admin_role_ids = admin_data['staffrole']
                admin_role_ids = admin_role_ids if isinstance(admin_role_ids, list) else [admin_role_ids]

                if any(role.id in staff_role_ids + admin_role_ids for role in ctx.author.roles):
                    return True


        if any(role.id in staff_role_ids for role in ctx.author.roles):
            return True
    else:
         if ctx.author.guild_permissions.administrator:
            

          await ctx.send(f"{no} **{ctx.author.display_name}**, the staff role isn't set please run </config:1140463441136586784>!", view=PermissionsButtons())
         else:
              await ctx.send(f"{no} **{ctx.author.display_name}**, the admin role is not setup please tell an admin to run </config:1140463441136586784> to fix it!", view=PermissionsButtons()) 
         return
    await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Staff Role`")
    return False



async def has_admin_role(ctx):   
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
     else:
         if ctx.author.guild_permissions.administrator:
            

          await ctx.send(f"{no} **{ctx.author.display_name}**, the admin role isn't set please run </config:1140463441136586784>", view=PermissionsButtons())
         else:
              await ctx.send(f"{no} **{ctx.author.display_name}**, the admin role is not setup please tell an admin to run </config:1140463441136586784> to fix it.", view=PermissionsButtons()) 
         return
     await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`")
     return False


async def has_moderator_role(ctx):
     if ctx.author.guild_permissions.administrator:
        return True     
     filter = {
        'guild_id': ctx.guild.id
    }
     staff_data = ReportModeratorRole.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_ids)
        if not isinstance(staff_role_ids, list):
          staff_role_ids = [staff_role_ids]   
        if any(role.id in staff_role_ids for role in ctx.author.roles):
            return True
     else:
         if ctx.author.guild_permissions.administrator:
            

          await ctx.send(f"{no} **{ctx.author.display_name}**, the reports moderator role isn't set please run </config:1140463441136586784>", view=PermissionsButtons())
         else:
              await ctx.send(f"{no} **{ctx.author.display_name}**, the reports moderator role isn't setup please tell an admin to run </config:1140463441136586784> to fix it.", view=PermissionsButtons())
         return
     return False


class PermissionsButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        url1 = f'https://discord.gg/DhWdgfh3hN'
        self.add_item(discord.ui.Button(label='Support Server', url=url1, style=discord.ButtonStyle.blurple))
        self.add_item(discord.ui.Button(label='Documentation', url="https://docs.astrobirb.dev/overview", style=discord.ButtonStyle.blurple))