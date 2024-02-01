
import discord
from discord.ext import commands, tasks
from pymongo import MongoClient
from emojis import *
from typing import Literal
import os
from discord import Button
import random
import logging
from datetime import datetime
import chat_exporter
import typing
from dotenv import load_dotenv
import io   
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
modmail = db['modmail']
modmailalerts = db['modmailalerts']
modmailblacklists = db['modmailblacklists']
transcripts = db['transcripts']
modmailcategory = db['modmailcategory']
transcriptschannel = db['transcriptschannel']
from permissions import has_admin_role, has_staff_role
class Modmail(commands.Cog):
    def __init__(self, client):
        self.client = client



    @commands.hybrid_group()
    async def modmail(self, ctx):
        return
    

    @modmail.command(description="Pings you for the next message")
    async def alert(self, ctx):
        if not await has_staff_role(ctx):
            return
        await ctx.send(f"{tick} **{ctx.author.display_name},** you will be alerted for the next message.", ephemeral=True)
        modmailalerts.update_one({'channel_id': ctx.channel.id}, {'$set': {'alert': ctx.author.id}}, upsert=True)     

    @modmail.command(description="Blacklist someone from using modmail")
    async def blacklist(self, ctx, member: discord.Member):
        if not await has_admin_role(ctx):
            return
        blacklist = modmailblacklists.find_one({'guild_id': ctx.guild.id})
        if blacklist:
            if member.id in blacklist['blacklist']:
                await ctx.send(f"{no} **{member.display_name}** is already blacklisted.")
                return
        modmailblacklists.update_one({'guild_id': ctx.guild.id}, {'$push': {'blacklist': member.id}}, upsert=True)
        await ctx.send(f"{tick} **{member.display_name}** has been blacklisted from using modmail.")
       
    @modmail.command(description="Unblacklist someone from using modmail")
    async def unblacklist(self, ctx, member: discord.Member):
        if not await has_admin_role(ctx):
            return
        blacklist = modmailblacklists.find_one({'guild_id': ctx.guild.id})
        if blacklist:
            if member.id not in blacklist['blacklist']:
                await ctx.send(f"{no} **{member.display_name}** is not blacklisted.")
                return
        modmailblacklists.update_one({'guild_id': ctx.guild.id}, {'$pull': {'blacklist': member.id}}, upsert=True)
        await ctx.send(f"{tick} **{member.display_name}** has been unblacklisted from using modmail.")

    @modmail.command(description="Reply to a modmail")
    async def reply(self, ctx, *, content):
     if not await has_staff_role(ctx):
         return             
     if isinstance(ctx.channel, discord.TextChannel):
        channel_id = ctx.channel.id
        modmail_data = modmail.find_one({'channel_id': channel_id})

        if modmail_data:
            user_id = modmail_data.get('user_id')
            selected_server_id = modmail_data.get('guild_id')

            if user_id and selected_server_id:
                selected_server = discord.utils.get(self.client.guilds, id=selected_server_id)
                user = await self.client.fetch_user(user_id)

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
     await ctx.defer()
     if not await has_staff_role(ctx):
         return             
     if isinstance(ctx.channel, discord.TextChannel):
        channel_id = ctx.channel.id
        modmail_data = modmail.find_one({'channel_id': channel_id})

        if modmail_data:
            selected_server_id = modmail_data.get('guild_id')
            selected_server = discord.utils.get(self.client.guilds, id=selected_server_id)

            if selected_server:

                modmail.delete_one({'channel_id': channel_id}) 
                channel = ctx.guild.get_channel(modmail_data.get('channel_id'))
                print(channel)
                channelcreated = f"{channel.created_at.strftime('%d/%m/%Y')}"
                

                transcriptid = random.randint(100, 5000)
                transcriptresult = transcripts.find_one({'guild_id': ctx.guild.id, 'transcriptid': transcriptid})
                if transcriptresult:
                    transcriptid = random.randint(100, 5000)
                transcript = await chat_exporter.export(ctx.channel)    
                transcript_file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"transcript-{ctx.channel.name}.html",
    )     
                try:   
                 await ctx.channel.send(f"{tick} Modmail channel has been closed.")    
                 await channel.delete()

                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name},** I can't delete this channel please contact the server admins.")
                    return                               
 
                user_id = modmail_data.get('user_id')
                if user_id:
                    user = await self.client.fetch_user(user_id)
                    if user:
                        try:
                         await user.send(f"{tick} Your modmail channel has been closed.") 
                        except discord.Forbidden:
                            
                            pass     
                transcriptchannelresult = transcriptschannel.find_one({'guild_id': ctx.guild.id})
                if transcriptchannelresult:
                    transcriptchannelid = transcriptchannelresult['channel_id']
                    transcriptchannel = ctx.guild.get_channel(transcriptchannelid)
                    if transcriptchannel:
                     embed = discord.Embed(title=f"Modmail #{transcriptid}", description=f"**Modmail Info**\n> **User:** <@{user_id}>\n> **Closed By:** {ctx.author.mention}\n> **Created:** {channelcreated}\n> **Closed:** {datetime.utcnow().strftime('%d/%m/%Y')}", color=discord.Color.dark_embed())
                     embed.set_thumbnail(url=user.display_avatar.url)
                     testchannel = self.client.get_channel(1202756318897774632)
                     message = await testchannel.send("<:infractionssearch:1200479190118576158> **HTML Transcript**", file=transcript_file)
                     link = await chat_exporter.link(message)
                     print(link)
                     view = TranscriptChannel(link)
                     await transcriptchannel.send(embed=embed, view=view)
            else:
                await ctx.send(f"{Warning} Selected server not found.")
        else:
            await ctx.send(f"{no} No active modmail channel found for this channel.")
     else:
        await ctx.send(f"{no} You can only use the close command in a modmail channel.") 
        



class TranscriptChannel(discord.ui.View):
    def __init__(self, url):
        super().__init__()
        self.add_item(discord.ui.Button(label='Transcript', url=url, style=discord.ButtonStyle.blurple))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Modmail(client))      