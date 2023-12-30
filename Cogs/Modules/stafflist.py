import discord
from discord.ext import commands, tasks
import os
from pymongo import MongoClient
from emojis import *
from typing import Literal, Optional
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
modules = db['Modules']
class StaffList(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata.get('StaffList', False) == True: 
        return True
     else:   
        return False

    async def has_staff_role(self, ctx):
     filter = {
        'guild_id': ctx.guild.id
    }
     staff_data = scollection.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_ids)
        if not isinstance(staff_role_ids, list):
          staff_role_ids = [staff_role_ids]   
        if any(role.id in staff_role_ids for role in ctx.author.roles):
            return True

     return False


    async def has_admin_role(self, ctx):
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

     return False

    @commands.hybrid_command(description="Lists the staff team")
    async def stafflist(self, ctx, display: Optional[Literal['True', 'False']]):
        guild_id = ctx.guild.id
        guild = self.client.get_guild(guild_id)
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return    

        if not await self.has_staff_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return        
        if guild:
            staff_role_ids = self.get_role_ids(guild, "staffrole")
            admin_role_ids = self.get_role_ids(guild, "adminrole")

            embed = discord.Embed(title="<:List:1179470251860185159> Staff List", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=guild.icon)

            hoisted_roles = sorted([role for role in guild.roles if role.hoist], key=lambda x: x.position, reverse=True)
            members_by_role = {}

            for role in hoisted_roles:
                if role.id in staff_role_ids or role.id in admin_role_ids:
                    members = self.get_members_with_top_role(guild, [role.id])
                    if members:
                        role_mentions = set()
                        for member in members:
                            mention = member.mention
                            role_mentions.add(f"<:SmallArrow:1140288951861649418>{mention}")

                        if role_mentions:
                            if role.name not in members_by_role:
                                members_by_role[role.name] = set()
                            members_by_role[role.name].update(role_mentions)

            for role_name, mentions in members_by_role.items():
                value = "\n".join(mentions)[:1024]
                embed.add_field(name=f"<:astroDot:1190671915057160223>{role_name}", value=value, inline=False)

            channel = ctx.channel
            if display == 'True':
                await channel.send(embed=embed)
                if ctx.interaction:
                 await ctx.send(f"{tick} Sent the **stafflist**", ephemeral=True)
                else: 
                    return
            else:
                await ctx.send(embed=embed)

    def get_role_ids(self, guild, role_type):
        filter = {
            'guild_id': guild.id
        }
        role_data = db[role_type].find_one(filter)

        if role_data and 'staffrole' in role_data:
            role_ids = role_data['staffrole']

            if not isinstance(role_ids, list):
                role_ids = [role_ids]

            return role_ids

        return []

    def get_members_with_top_role(self, guild, role_ids):
        members = set()
        for role_id in role_ids:
            role = discord.utils.get(guild.roles, id=role_id)
            if role:
                members.update(role.members)
        return members

async def setup(client: commands.Bot) -> None:
    await client.add_cog(StaffList(client))     
