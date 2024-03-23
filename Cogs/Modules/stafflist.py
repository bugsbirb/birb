import discord
from discord import app_commands
from discord.ext import commands
import os
from emojis import *
from typing import Literal, Optional
from permissions import *

MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
modules = db['Modules']
class StaffList(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client





    @commands.hybrid_command(description="Lists the staff team (Doesn't use staff DB)")
    @app_commands.describe(display = 'If you want the staff list to be displayed')
    async def stafflist(self, ctx: commands.Context, display: Optional[Literal['True', 'False']]):
        guild_id = ctx.guild.id
        guild = self.client.get_guild(guild_id)


        if not await has_staff_role(ctx):
    
         return        
        if guild:
            staff_role_ids = await self.get_role_ids(guild, "staffrole")
            admin_role_ids = await self.get_role_ids(guild, "adminrole")

            embed = discord.Embed(title="<:List:1179470251860185159> Staff List", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=guild.icon)

            hoisted_roles = sorted([role for role in guild.roles if role.hoist], key=lambda x: x.position, reverse=True)
            members_by_role = {}

            for role in hoisted_roles:
                if role.id in staff_role_ids or role.id in admin_role_ids:
                    members = await self.get_members_with_top_role(guild, [role.id])
                    if members:
                        role_mentions = set()
                        for member in members:
                            mention = member.mention
                            role_mentions.add(f"{smallarrow}{mention}")

                        if role_mentions:
                            if role.name not in members_by_role:
                                members_by_role[role.name] = set()
                            members_by_role[role.name].update(role_mentions)

            for role_name, mentions in members_by_role.items():
                value = "\n".join(mentions)[:1024]
                embed.add_field(name=f"<:Dot:1220476818272944308>{role_name}", value=value, inline=False)

            channel = ctx.channel
            if display == 'True':
                await channel.send(embed=embed)
                if ctx.interaction:
                 await ctx.send(f"{tick} Sent the **stafflist**", ephemeral=True)
                else: 
                    return
            else:
                await ctx.send(embed=embed)

    async def get_role_ids(self, guild, role_type):
        filter = {
            'guild_id': guild.id
        }
        role_data = await db[role_type].find_one(filter)

        if role_data and 'staffrole' in role_data:
            role_ids = role_data['staffrole']

            if not isinstance(role_ids, list):
                role_ids = [role_ids]

            return role_ids

        return []

    async def get_members_with_top_role(self, guild, role_ids):
        members = set()
        for role_id in role_ids:
            role = discord.utils.get(guild.roles, id=role_id)
            if role:
                members.update(role.members)
        return members

async def setup(client: commands.Bot) -> None:
    await client.add_cog(StaffList(client))     
