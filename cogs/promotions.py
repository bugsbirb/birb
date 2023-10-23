import discord
import sqlite3
import discord
from discord.ext import commands
from typing import Literal
import datetime
from datetime import timedelta
import asyncio
from discord import app_commands
from discord.ext import commands, tasks
import pytz
import Paginator
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')

client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
promochannel = db['promo channel']
class promo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def has_staff_role(self, ctx):
        filter = {
            'guild_id': ctx.guild.id
        }
        staff_data = scollection.find_one(filter)

        if staff_data and 'staffrole' in staff_data:
            staff_role_id = staff_data['staffrole']
            staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_id)

            if staff_role and staff_role in ctx.author.roles:
                return True

        return False


    async def has_admin_role(self, ctx):
        filter = {
            'guild_id': ctx.guild.id
        }
        admin_data = arole.find_one(filter)

        if admin_data and 'adminrole' in admin_data:
            admin_role_id = admin_data['adminrole']
            admin_role = discord.utils.get(ctx.guild.roles, id=admin_role_id)
            if admin_role in ctx.author.roles:
                return True

        return False

    @commands.hybrid_command(description="Promote a staff member")
    @app_commands.describe(
    staff='What staff member are you promoting?',
    new='What the role you are awarding them with?',
    reason='What makes them deserve the promotion?') 
    async def promote(self, ctx, staff: discord.Member, new: discord.Role, reason: str):
        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return             

        if ctx.author.top_role <= new:
            await ctx.send(f"{no} **{ctx.author.display_name}**, your below the role `{new.name}` you do not have authority to promote this member.", ephemeral=True)
            return

        try:
            await staff.add_roles(new)
        except discord.Forbidden:
            await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, I don't have permission to add roles.", ephemeral=True)
            return



        embed = discord.Embed(title=f"Staff Promotion", color=0x2b2d31, description=f"* **User:** {staff.mention}\n* **Updated Rank:** {new.mention}\n* **Reason:** {reason}")
        embed.set_thumbnail(url=staff.display_avatar)
        embed.set_author(name=f"Signed, {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)


        guild_id = ctx.guild.id
        data = promochannel.find_one({'guild_id': guild_id})

        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
            await ctx.send(f"{tick} **{ctx.author.display_name}**, I've promoted **@{staff.display_name}**")
            await channel.send(f"{staff.mention}", embed=embed)
         else:
            await ctx.send(f"{Warning} {ctx.author.display_name}, I don't have permission to view this channel.")
        else:
          await ctx.send(f"{Warning} **{ctx.author.display_name}**, the channel is not setup please run `/config`")

async def setup(client: commands.Bot) -> None:
    await client.add_cog(promo(client))            