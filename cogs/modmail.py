
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
from typing import Literal
import os
from dotenv import load_dotenv
import Paginator
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
modmail = db['modmail']
modmailcategory = db['modmailcategory']

class Modmail(commands.Cog):
    def __init__(self, client):
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

    @commands.hybrid_group()
    async def modmail(self, ctx):
        return
    

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if isinstance(message.channel, discord.DMChannel):
            user_id = message.author.id
            modmail_data = modmail.find_one({'user_id': user_id})

            if not modmail_data:
                if message.content.isdigit():
                    return

                mutual_servers = [
                    guild for guild in self.client.guilds
                    if discord.utils.get(guild.members, id=user_id)
                    and modmailcategory.find_one({'guild_id': guild.id})
                ]

                if not mutual_servers:
                    await message.author.send(f"{no} You are not a member of any server with modmail enabled.")
                    return

                server_list = "\n".join([f"`{i+1}`. **{server.name}**" for i, server in enumerate(mutual_servers)])
                server_list += "\n\nPlease enter the number of the server you want to communicate with."

                embed = discord.Embed(
                    title="Server List",
                    description=server_list,
                    color=discord.Color.dark_embed()
                )
                embed.set_thumbnail(url=self.client.user.display_avatar)
                embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar)

                await message.author.send(embed=embed)

                def check(response):
                    return (
                        response.author == message.author
                        and response.content.isdigit()
                        and 1 <= int(response.content) <= len(mutual_servers)
                    )

                try:
                    response = await self.client.wait_for('message', check=check, timeout=10)
                    selected_server = mutual_servers[int(response.content) - 1]
                except asyncio.TimeoutError:
                    await message.author.send(f"{no} Server selection expired.")
                    return
                except ValueError:
                    await message.author.send(f"{no} Invalid server number. Please enter a valid number.")

                category_id = modmailcategory.find_one({'guild_id': selected_server.id})['category_id']

                category = self.client.get_channel(category_id)
                if category and isinstance(category, discord.CategoryChannel):
                    existing_modmail_data = modmail.find_one({'user_id': user_id, 'guild_id': selected_server.id})
                    if existing_modmail_data:
                        channel_id = existing_modmail_data['channel_id']
                        channel = self.client.get_channel(channel_id)

                        if channel:
                            embed = discord.Embed(
                                color=discord.Color.dark_embed(),
                                title=message.author,
                                description=f"```{message.content}```"
                            )
                            embed.set_author(name=message.author, icon_url=message.author.display_avatar)
                            embed.set_thumbnail(url=message.author.display_avatar)
                            try:
                             await channel.send(embed=embed)
                            except discord.Forbidden:
                             await message.reply(f"{no} Please contact server admins I can't see the modmail channel.")                                    
                             return
                    else:
                        try:
                         channel = await category.create_text_channel(f'modmail-{message.author.name}')
                        except discord.Forbidden: 
                            await message.reply(f"{no} Please contact the server admins I can't create a channel.")
                            return
                        modmail_data = {
                            'user_id': user_id,
                            'guild_id': selected_server.id,
                            'channel_id': channel.id
                        }
                        modmail.insert_one(modmail_data)
                        await message.author.send(f"{tick} Conversation started.")
                        await channel.send(f"<:Messages:1148610048151523339> **{message.author.display_name}** has started a modmail conversation.")
                        embed = discord.Embed(
                            color=discord.Color.dark_embed(),
                            title=message.author,
                            description=f"```{message.content}```"
                        )
                        embed.set_author(name=message.author, icon_url=message.author.display_avatar)
                        embed.set_thumbnail(url=message.author.display_avatar)
                        try:
                         await channel.send(embed=embed)
                        except discord.Forbidden: 
                            await message.reply(f"{no} I can't see the modmail channel contact a server admin.")
                else:
                    await message.author.send("Selected category not found.")
            else:
                channel_id = modmail_data['channel_id']
                channel = self.client.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        color=discord.Color.dark_embed(),
                        title=message.author,
                        description=f"```{message.content}```"
                    )
                    embed.set_author(name=message.author, icon_url=message.author.display_avatar)
                    embed.set_thumbnail(url=message.author.display_avatar)
                    await channel.send(embed=embed)


    @modmail.command(description="Reply to a modmail")
    async def reply(self, ctx, *, content):
     if not await self.has_staff_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return             
     if isinstance(ctx.channel, discord.TextChannel):
        channel_id = ctx.channel.id
        modmail_data = modmail.find_one({'channel_id': channel_id})

        if modmail_data:
            user_id = modmail_data.get('user_id')
            selected_server_id = modmail_data.get('guild_id')

            if user_id and selected_server_id:
                selected_server = discord.utils.get(self.client.guilds, id=selected_server_id)
                user = self.client.get_user(user_id)

                if selected_server and user:
                    embed = discord.Embed(color=discord.Color.dark_embed(), title=f"**(Staff)** {ctx.author}", description=f"```{content}```")
                    embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
                    embed.set_thumbnail(url=ctx.guild.icon)
                    await user.send(embed=embed)

                    channel = self.client.get_channel(channel_id)
                    await ctx.send(f"{tick} Response sent.", ephemeral=True)
                    try:
                     await channel.send(embed=embed)
                    except discord.Forbidden: 
                        await ctx.send(f"{no} I can't find or see this channel.", ephemeral=True)
                    return
        await ctx.send(f"{no} No active modmail channel found for that user.")
     else:
        await ctx.send(f"{no} You can only use the reply command in a modmail channel")


    @modmail.command(description="Close a modmail channel.")
    async def close(self, ctx):
     if not await self.has_staff_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return             
     if isinstance(ctx.channel, discord.TextChannel):
        channel_id = ctx.channel.id
        modmail_data = modmail.find_one({'channel_id': channel_id})

        if modmail_data:
            selected_server_id = modmail_data.get('guild_id')
            selected_server = discord.utils.get(self.client.guilds, id=selected_server_id)

            if selected_server:
                user_id = modmail_data.get('user_id')
                if user_id:
                    user = self.client.get_user(user_id)
                    if user:
                        await user.send(f"{tick} Your modmail channel has been closed.")
                await ctx.send(f"{tick} Modmail channel has been closed.")                
                await ctx.channel.delete() 
                modmail.delete_one({'channel_id': channel_id}) 
                
            else:
                await ctx.send(f"{Warning} Selected server not found.")
        else:
            await ctx.send(f"{no} No active modmail channel found for this channel.")
     else:
        await ctx.send(f"{no} You can only use the close command in a modmail channel.") 
        


    @modmail.command(name="config" ,description="Set up modmail configuration")
    @commands.has_guild_permissions(administrator=True)
    async def config(self, ctx, category: discord.CategoryChannel = None, data: Literal['Reset Data'] = None):
     if not category and not data:
        await ctx.send(f"{no} Please specify either a category or 'Reset Data' to configure modmail.")

     if data and data.lower() == "reset data":
        modmailcategory.delete_one({'guild_id': ctx.guild.id})
        await ctx.send(f"{tick} Modmail configuration data has been reset.")

     if category:
        if ctx.guild.me.guild_permissions.manage_channels:
            try:
                modmailcategory.update_one({'guild_id': ctx.guild.id}, {'$set': {'category_id': category.id}}, upsert=True)
                embed = discord.Embed(title=f"{tick} Configuration Updated",description=f"* **Modmail Category:** **`{category.name}`**", color=discord.Color.dark_embed())
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"An error occurred: {str(e)}")
        else:
            await ctx.send(f"{no} I don't have permission to create channels. Please give me `manage channels` permissions.")

            
    @config.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to configure this server.\n<:Arrow:1115743130461933599>**Required:** ``Administrator``")              


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Modmail(client))      
