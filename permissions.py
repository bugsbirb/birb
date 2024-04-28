import discord
import sys
sys.dont_write_bytecode = True
import discord
import os
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *

MONGO_URL = os.getenv('MONGO_URL')
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo['astro']

ReportModeratorRole = db['Report Moderator Role']
scollection = db['staffrole']
arole = db['adminrole']
premiums = db['premium']



async def has_staff_role(ctx):
    filter = {'guild_id': ctx.guild.id}
    staff_data = await scollection.find_one(filter)

    if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        staff_role_ids = staff_role_ids if isinstance(staff_role_ids, list) else [staff_role_ids]


        admin_data = await arole.find_one(filter)


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
            

          await ctx.send(f"{no} **{ctx.author.display_name}**, the staff role isn't set please run </config:1140463441136586784>!", view=PermissionsButtons(), allowed_mentions=discord.AllowedMentions.none())
         else:
              await ctx.send(f"{no} **{ctx.author.display_name}**, the admin role is not setup please tell an admin to run </config:1140463441136586784> to fix it!", view=PermissionsButtons(), allowed_mentions=discord.AllowedMentions.none()) 
         return
    await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Staff Role`", allowed_mentions=discord.AllowedMentions.none())
    return False


async def premium(ctx):
    result = await premiums.find_one({'guild_id': ctx.guild.id})
    if result:
        return True
    else:
        return False






async def has_admin_role(ctx):   
     filter = {
        'guild_id': ctx.guild.id
    }
     staff_data = await arole.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_ids)
        if not isinstance(staff_role_ids, list):
          staff_role_ids = [staff_role_ids] 

          
             
        if any(role.id in staff_role_ids for role in ctx.author.roles):
            return True
     else:
         if ctx.author.guild_permissions.administrator:
            

          await ctx.send(f"{no} **{ctx.author.display_name}**, the admin role isn't set please run </config:1140463441136586784>", view=PermissionsButtons(), allowed_mentions=discord.AllowedMentions.none())
         else:
              await ctx.send(f"{no} **{ctx.author.display_name}**, the admin role is not setup please tell an admin to run </config:1140463441136586784> to fix it.", view=PermissionsButtons(), allowed_mentions=discord.AllowedMentions.none()) 
         return
     await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`",  allowed_mentions=discord.AllowedMentions.none())
     return False




class PermissionsButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        url1 = 'https://discord.gg/DhWdgfh3hN'
        self.add_item(discord.ui.Button(label='Support Server', url=url1, style=discord.ButtonStyle.blurple))
        self.add_item(discord.ui.Button(label='Documentation', url="https://docs.astrobirb.dev/overview", style=discord.ButtonStyle.blurple))


