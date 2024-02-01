
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
import chat_exporter
import random
import io
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
modmail = db['modmail']
modules = db['Modules']
modmailcategory = db['modmailcategory']
transcripts = db['transcripts']
modmailblacklists = db['modmailblacklists']
transcriptschannel = db['transcriptschannel']
modmailalerts = db['modmailalerts']
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
            if message.content == f"!close":
                if not modmail_data:
                    await message.author.send(f"{no} You are not in a modmail conversation.")
                    return
                channel_id = modmail_data['channel_id']
                channel = self.client.get_channel(channel_id)
                channelcreated = f"{channel.created_at.strftime('%d/%m/%Y')}"
                
                
                transcriptid = random.randint(100, 5000)
                transcript = await chat_exporter.export(channel)    
                transcript_file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"transcript-{channel.name}.html")           
                if channel:
                    await channel.send(f"<:Messages:1148610048151523339> **{message.author.display_name}** has closed the modmail conversation.")
                    await channel.delete()
                    modmail.delete_many({'user_id': user_id})
                    await message.author.send(f"{tick} Conversation closed.")
                    transcriptschannelresult = transcriptschannel.find_one({'guild_id': channel.guild.id})
                    if transcriptschannelresult:
                     transcriptchannelid = transcriptschannelresult.get('channel_id')
                     transcriptchannel = self.client.get_channel(transcriptchannelid)
                     if transcriptchannel:
                      embed = discord.Embed(title=f"Modmail #{transcriptid}", description=f"**Modmail Info**\n> **User:** <@{message.author.id}>\n> **Closed By:** {message.author.mention}\n> **Created:** {channelcreated}\n> **Closed:** {datetime.utcnow().strftime('%d/%m/%Y')}", color=discord.Color.dark_embed())
                      embed.set_thumbnail(url=message.author.display_avatar.url)
                      message = await transcriptchannel.send("<:infractionssearch:1200479190118576158> **HTML Transcript**", file=transcript_file)
                      link = await chat_exporter.link(message)
                      print(link)
                      view = TranscriptChannel(link)
                      await transcriptchannel.send(embed=embed, view=view)
                else:
                    await message.author.send(f"{no} Modmail channel not found.")
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
                    blacklist = modmailblacklists.find_one({'guild_id': selected_server.id})
                    if blacklist:
                        if user_id in blacklist['blacklist']:
                            await message.author.send(f"{no} **{message.author.display_name},** You are blacklisted from using modmail in **{selected_server.name}**.")
                            return
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
        
                        await message.author.send(f"{tick} Conversation started.\n{dropdown} Use `!close` to close the conversation.")
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
                mention = ""
                if channel:
                    modmailalertsresult = modmailalerts.find_one({'channel_id': channel.id})
                    if modmailalertsresult:
                        mention = modmailalertsresult.get('alert')
                        print2 = modmailalerts.delete_one({'channel_id': channel.id, 'alert': mention})                         
                        if mention:
                            mention = f"<@{mention}>"

   
                        
                    embed = discord.Embed(
                        color=discord.Color.dark_embed(),
                        title=message.author,
                        description=f"```{message.content}```"
                    )
                    embed.set_author(name=message.author, icon_url=message.author.display_avatar)
                    embed.set_thumbnail(url=message.author.display_avatar)
                    await channel.send(mention, embed=embed)


class TranscriptChannel(discord.ui.View):
    def __init__(self, url):
        super().__init__()
        self.add_item(discord.ui.Button(label='Transcript', url=url, style=discord.ButtonStyle.blurple))




async def setup(client: commands.Bot) -> None:
    await client.add_cog(Modmailevnt(client))       
