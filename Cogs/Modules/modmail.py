
import discord
from discord.ext import commands
from emojis import *
import os
import random
import Paginator
import chat_exporter
import io   
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from discord import app_commands
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
modmail = db['modmail']
modmailalerts = db['modmailalerts']
modmailblacklists = db['modmailblacklists']
modmailcategory = db['modmailcategory']
transcriptschannel = db['transcriptschannel']
transcripts = db['Transcripts']
modules = db['Modules']
from permissions import has_admin_role, has_staff_role
class Modmail(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def modulecheck(self, ctx: commands.Context): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata.get('Modmail', False) == True: 
        return True
     else:   
        return False



    @commands.hybrid_group(alias="m", description="Modmail commands")
    async def modmail(self, ctx: commands.Context):
        return
    

    @modmail.command(description="Pings you for the next message")
    async def alert(self, ctx: commands.Context):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the modmail module isn't enabled.")
         return         
        if not await has_staff_role(ctx):
            return
        await ctx.send(f"{tick} **{ctx.author.display_name},** you will be alerted for the next message.", ephemeral=True)
        await modmailalerts.update_one({'channel_id': ctx.channel.id}, {'$set': {'alert': ctx.author.id}}, upsert=True)     

    @modmail.command(description="Blacklist someone from using modmail")
    @app_commands.describe(member = "The member you want to blacklist from using modmail")
    async def blacklist(self, ctx: commands.Context, member: discord.Member):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the modmail module isn't enabled.")
         return                 
        if not await has_admin_role(ctx):
            return
        blacklist = await modmailblacklists.find_one({'guild_id': ctx.guild.id})
        if blacklist:
            if member.id in blacklist['blacklist']:
                await ctx.send(f"{no} **{member.display_name}** is already blacklisted.")
                return
        await modmailblacklists.update_one({'guild_id': ctx.guild.id}, {'$push': {'blacklist': member.id}}, upsert=True)
        await ctx.send(f"{tick} **{member.display_name}** has been blacklisted from using modmail.")
       
    @modmail.command(description="Unblacklist someone from using modmail")
    @app_commands.describe(member = "The member you want to unblacklist from using modmail")
    async def unblacklist(self, ctx: commands.Context, member: discord.Member):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the modmail module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return                 
        if not await has_admin_role(ctx):
            return
        blacklist = await modmailblacklists.find_one({'guild_id': ctx.guild.id})
        if blacklist:
            if member.id not in blacklist['blacklist']:
                await ctx.send(f"{no} **{member.display_name}** is not blacklisted.", allowed_mentions=discord.AllowedMentions.none())
                return
        await modmailblacklists.update_one({'guild_id': ctx.guild.id}, {'$pull': {'blacklist': member.id}}, upsert=True)
        await ctx.send(f"{tick} **{member.display_name}** has been unblacklisted from using modmail.", allowed_mentions=discord.AllowedMentions.none())

    @modmail.command(description="Reply to a modmail")
    @app_commands.describe(content = 'The message you want to send to the user.', media = "The media you want to send to the user.")
    async def reply(self, ctx: commands.Context, *, content, media: discord.Attachment = None):
     await ctx.defer(ephemeral=True)
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the modmail module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return              
     if not await has_staff_role(ctx):
         return        
          
     if isinstance(ctx.channel, discord.TextChannel):
        channel_id = ctx.channel.id
        modmail_data = await modmail.find_one({'channel_id': channel_id})
        mediamsg = ""
        if media:
           mediamsg = f"**Attachment Below**"

        if modmail_data:
            user_id = modmail_data.get('user_id')
            selected_server_id = modmail_data.get('guild_id')

            if user_id and selected_server_id:
                selected_server = discord.utils.get(self.client.guilds, id=selected_server_id)
                user = await self.client.fetch_user(user_id)

                if selected_server and user:
                    embed = discord.Embed(color=discord.Color.dark_embed(), title=f"**(Staff)** {ctx.author}", description=f"```{content}```\n{mediamsg}")
                    embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
                    embed.set_thumbnail(url=ctx.guild.icon)
                    embed.set_image(url=media)
                    await user.send(embed=embed)

                    channel = self.client.get_channel(channel_id)
                    
                    try:
                     await ctx.send(f"{tick} Response sent.", ephemeral=True)
                     await channel.send(embed=embed)
                    except discord.Forbidden: 
                        await ctx.send(f"{no} I can't find or see this channel.", ephemeral=True)
                    return
        await ctx.send(f"{no} No active modmail channel found for that user.")
     else:
        await ctx.send(f"{no} You can only use the reply command in a modmail channel")

    @modmail.command(description="View the modmail logs for a member")
    @app_commands.describe(member = "The member you want to view the modmail logs for")
    async def logs(self, ctx: commands.Context, member: discord.User):
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the modmail module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return              
        if not await has_admin_role(ctx):
            return

        result = await transcripts.find({'author': member.id, 'guild_id': ctx.guild.id}).to_list(None)
        if not result:
            await ctx.send(f"{no} No modmail logs found for this user.")
            return

        embeds = []
        for i, logs in enumerate(result):
            embed = discord.Embed(title=f"{(member.name).capitalize()}'s Modmail Logs", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=member.display_avatar)
            embed.set_author(name=member.name, icon_url=member.display_avatar)
            value = f"<:arrow:1166529434493386823>**Transcript:** [View Online]({logs.get('transcriptlink')})\n<:arrow:1166529434493386823>**Closed By:** <@{logs.get('closedby')}>\n<:arrow:1166529434493386823>**Date:** <t:{int(logs.get('timestamp').timestamp())}:d>\n<:arrow:1166529434493386823>**Closure Reason:** {logs.get('reason')}"
            if len(value) > 1024:
                value = value[:1021] + "..."
            embed.add_field(name=f"#{logs.get('transcriptid')}", value=value, inline=False)
            embeds.append(embed)

            if (i + 1) % 9 == 0:
                embeds.append(embed)

        PreviousButton = discord.ui.Button(emoji="<:chevronleft:1220806425140531321>")
        NextButton = discord.ui.Button(emoji="<:chevronright:1220806430010118175>")
        FirstPageButton = discord.ui.Button(emoji="<:chevronsleft:1220806428726661130>")
        LastPageButton = discord.ui.Button(emoji="<:chevronsright:1220806426583371866>")
        InitialPage = 0
        timeout = 42069

        if len(embeds) <= 1:
            PreviousButton.disabled = True
            NextButton.disabled = True
            FirstPageButton.disabled = True
            LastPageButton.disabled = True

        paginator = Paginator.Simple(
            PreviousButton=PreviousButton,
            NextButton=NextButton,
            FirstEmbedButton=FirstPageButton,
            LastEmbedButton=LastPageButton,
            InitialPage=InitialPage,
            timeout=timeout
        )

        await paginator.start(ctx, pages=embeds) 
       
       
    
    @commands.command(description="Reply to a modmail channel.")
    async def mreply(self, ctx: commands.Context, *, content):
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the modmail module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return              
     if not await has_staff_role(ctx):
         return             
     if isinstance(ctx.channel, discord.TextChannel):
        channel_id = ctx.channel.id
        modmail_data = await modmail.find_one({'channel_id': channel_id})
        media = None
        mediamsg = ""
        if ctx.message.attachments:
            media = ctx.message.attachments[0].url
            mediamsg = f"**Attachment Below**"


        if modmail_data:
            user_id = modmail_data.get('user_id')
            selected_server_id = modmail_data.get('guild_id')

            if user_id and selected_server_id:
                selected_server = discord.utils.get(self.client.guilds, id=selected_server_id)
                user = await self.client.fetch_user(user_id)

                if selected_server and user:
                    embed = discord.Embed(color=discord.Color.dark_embed(), title=f"**(Staff)** {ctx.author}", description=f"```{content}```\n{mediamsg}")
                    embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
                    embed.set_thumbnail(url=ctx.guild.icon)
                    embed.set_image(url=media)
                    await user.send(embed=embed)

                    channel = self.client.get_channel(channel_id)
                    
                    try:
                     await channel.send(embed=embed)
                    except discord.Forbidden: 
                        await ctx.send(f"{no} I can't find or see this channel.", ephemeral=True)
                    await ctx.message.delete()  
                    
                    return
                    
        await ctx.send(f"{no} No active modmail channel found for that user.")
     else:
        await ctx.send(f"{no} You can only use the reply command in a modmail channel")
    @commands.command(description="Close a modmail channel.", name="mclose")
    async def close2(self, ctx: commands.Context, *, reason = None):
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the modmail module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return              
     if not await has_staff_role(ctx):
         return             
     if isinstance(ctx.channel, discord.TextChannel):
        channel_id = ctx.channel.id
        modmail_data = await modmail.find_one({'channel_id': channel_id})

        if modmail_data:
            selected_server_id = modmail_data.get('guild_id')
            selected_server = discord.utils.get(self.client.guilds, id=selected_server_id)

            if selected_server:

                await modmail.delete_one({'channel_id': channel_id}) 
                channel = ctx.guild.get_channel(modmail_data.get('channel_id'))
                print(channel)
                channelcreated = f"{channel.created_at.strftime('%d/%m/%Y')}"
                

                transcriptid = random.randint(100, 5000)
                transcriptresult = await transcripts.find_one({'guild_id': ctx.guild.id, 'transcriptid': transcriptid})
                if transcriptresult:
                    transcriptid = random.randint(100, 5000)
                transcript = await chat_exporter.export(ctx.channel)    
                transcript_file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"transcript-{ctx.channel.name}.html",
    )     
                try:   
                 await ctx.channel.send(f"{tick} Modmail channel has been closed.", allowed_mentions=discord.AllowedMentions.none())    
                 await channel.delete()

                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name},** I can't delete this channel please contact the server admins.", allowed_mentions=discord.AllowedMentions.none())
                    return                               
                testchannel = self.client.get_channel(1202756318897774632)
                message = await testchannel.send("<:infractionssearch:1200479190118576158> **HTML Transcript**", file=transcript_file)
                link = await chat_exporter.link(message)  
                user_id = modmail_data.get('user_id')
                if user_id:
                    user = await self.client.fetch_user(user_id)
                    if user:
                        try:
                         if reason is None:
                            reason = "No reason provided."
                         embed = discord.Embed(title="Modmail Closed", description=f"", color=discord.Color.dark_embed())
                         embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
                         embed.add_field(name="<:Document:1191926049857097748> ID", value=transcriptid, inline=True)
                         embed.add_field(name="<:Add:1163095623600447558> Opened", value=user.mention, inline=True)
                         embed.add_field(name="<:Exterminate:1223063042246443078> Closed", value=ctx.author.mention, inline=True)
                         embed.add_field(name="<:casewarningwhite:1191903691750514708> Time Created", value=channelcreated, inline=True)
                         embed.add_field(name="<:reason:1202773873095868476> Reason", value=reason, inline=True)
                         await user.send(f"{tick} Your modmail channel has been closed.", embed=embed) 
                         await transcripts.insert_one({'transcriptid': transcriptid ,'guild_id': ctx.guild.id, 'closedby': ctx.author.id, 'reason': reason, 'author': user.id,'timestamp': datetime.now(), 'transcriptlink': link})  
                        except discord.Forbidden:
                            
                            pass     
                      
                transcriptchannelresult = await transcriptschannel.find_one({'guild_id': ctx.guild.id})
                if transcriptchannelresult:
                    transcriptchannelid = transcriptchannelresult['channel_id']
                    transcriptchannel = ctx.guild.get_channel(transcriptchannelid)
                    if transcriptchannel:
                     embed = discord.Embed(title="Modmail Closed", description=f"", color=discord.Color.dark_embed())
                     embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
                     embed.add_field(name="<:Document:1191926049857097748> ID", value=transcriptid, inline=True)
                     embed.add_field(name="<:Add:1163095623600447558> Opened", value=user.mention, inline=True)
                     embed.add_field(name="<:Exterminate:1223063042246443078> Closed", value=ctx.author.mention, inline=True)
                     embed.add_field(name="<:casewarningwhite:1191903691750514708> Time Created", value=channelcreated, inline=True)
                     embed.add_field(name="<:reason:1202773873095868476> Reason", value=reason, inline=True)

                     print(link)
                     view = TranscriptChannel(link)
                     await transcriptchannel.send(embed=embed, view=view)
            else:
                await ctx.send(f"{Warning} Selected server not found.")
        else:
            await ctx.send(f"{no} No active modmail channel found for this channel.")
     else:
        await ctx.send(f"{no} You can only use the close command in a modmail channel.") 
        

    @modmail.command(description="Close a modmail channel.")
    @app_commands.describe(reason="The reason for closing the modmail channel.")
    async def close(self, ctx: commands.Context, *, reason = None):
     await ctx.defer()
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the modmail module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return              
     if not await has_staff_role(ctx):
         return             
     if isinstance(ctx.channel, discord.TextChannel):
        channel_id = ctx.channel.id
        modmail_data = await modmail.find_one({'channel_id': channel_id})

        if modmail_data:
            selected_server_id = modmail_data.get('guild_id')
            selected_server = discord.utils.get(self.client.guilds, id=selected_server_id)

            if selected_server:

                await modmail.delete_one({'channel_id': channel_id}) 
                channel = ctx.guild.get_channel(modmail_data.get('channel_id'))
                print(channel)
                channelcreated = f"{channel.created_at.strftime('%d/%m/%Y')}"
                

                transcriptid = random.randint(100, 5000)
                transcriptresult = await transcripts.find_one({'guild_id': ctx.guild.id, 'transcriptid': transcriptid})
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
                    await ctx.send(f"{no} **{ctx.author.display_name},** I can't delete this channel please contact the server admins.", allowed_mentions=discord.AllowedMentions.none())
                    return                               
                testchannel = self.client.get_channel(1202756318897774632)
                message = await testchannel.send("<:infractionssearch:1200479190118576158> **HTML Transcript**", file=transcript_file)
                link = await chat_exporter.link(message)   
                user_id = modmail_data.get('user_id')
                if user_id:
                    user = await self.client.fetch_user(user_id)
                    if user:
                        try:
                         if reason is None:
                            reason = "No reason provided."
                         embed = discord.Embed(title="Modmail Closed", description=f"", color=discord.Color.dark_embed())
                         embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
                         embed.add_field(name="<:Document:1191926049857097748> ID", value=transcriptid, inline=True)
                         embed.add_field(name="<:Add:1163095623600447558> Opened", value=user.mention, inline=True)
                         embed.add_field(name="<:Exterminate:1223063042246443078> Closed", value=ctx.author.mention, inline=True)
                         embed.add_field(name="<:casewarningwhite:1191903691750514708> Time Created", value=channelcreated, inline=True)
                         embed.add_field(name="<:reason:1202773873095868476> Reason", value=reason, inline=True)
                         await user.send(f"{tick} Your modmail channel has been closed.", embed=embed) 
                         await transcripts.insert_one({'transcriptid': transcriptid ,'guild_id': ctx.guild.id, 'closedby': ctx.author.id, 'reason': reason, 'author': user.id,'timestamp': datetime.now(), 'transcriptlink': link})  
                        except discord.Forbidden:
                            
                            pass     
                      
                transcriptchannelresult = await transcriptschannel.find_one({'guild_id': ctx.guild.id})
                if transcriptchannelresult:
                    transcriptchannelid = transcriptchannelresult['channel_id']
                    transcriptchannel = ctx.guild.get_channel(transcriptchannelid)
                    if transcriptchannel:
                     embed = discord.Embed(title="Modmail Closed", description=f"", color=discord.Color.dark_embed())
                     embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
                     embed.add_field(name="<:Document:1191926049857097748> ID", value=transcriptid, inline=True)
                     embed.add_field(name="<:Add:1163095623600447558> Opened", value=user.mention, inline=True)
                     embed.add_field(name="<:Exterminate:1223063042246443078> Closed", value=ctx.author.mention, inline=True)
                     embed.add_field(name="<:casewarningwhite:1191903691750514708> Time Created", value=channelcreated, inline=True)
                     embed.add_field(name="<:reason:1202773873095868476> Reason", value=reason, inline=True)

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