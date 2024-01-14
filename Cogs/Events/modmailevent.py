
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

class Modmailevnt(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if isinstance(message.channel, discord.DMChannel):
            user_id = message.author.id
            modmail_data = modmail.find_one({'user_id': user_id})
            if message.content.lower().strip() == '!closemodmail':
                    await self.close_modmail(message.author, modmail_data['channel_id'])
                    return
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
                    return
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
                        await message.author.send(f"{tick} Conversation started.\n<:ArrowDropDown:1163171628050563153> Use !closemodmail to end your own modmail.")
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

    

    async def close_modmail(self, user, channel_id):
        channel = self.client.get_channel(channel_id)
        if channel:
            await channel.send(f"<:Messages:1148610048151523339> Modmail conversation closed by {user.display_name}.")
            await user.send("<:Messages:1148610048151523339> You've closed your modmail conversation.")
            modmail.delete_one({'user_id': user.id, 'channel_id': channel.id})
            await channel.delete()

        else:
            await user.send(f"<:dnd:1162074644023627889> There was an issue closing the modmail conversation. Please contact server admins.")
    
async def setup(client: commands.Bot) -> None:
    await client.add_cog(Modmailevnt(client))       
