
import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta


from emojis import *
import os
import chat_exporter
import random
import io
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
modmail = db['modmail']
modules = db['Modules']
modmailcategory = db['modmailcategory']
transcripts = db['Transcripts']
modmailblacklists = db['modmailblacklists']
transcriptschannel = db['transcriptschannel']
modmailping = db['modmailping']
modmailalerts = db['modmailalerts']
options = db['module options']

class Modmailevnt(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.user_last_selection = {}



    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        
        if message.author.bot:
            return

        
        if isinstance(message.channel, discord.DMChannel):
            user_id = message.author.id
            modmail_data = await modmail.find_one({'user_id': user_id})
            if message.content == "!close":
                if not modmail_data:
                    await message.author.send(f"{no} You are not in a modmail conversation.")
                    return
                channel_id = modmail_data['channel_id']
                channel = self.client.get_channel(channel_id)
                if channel is None:
                    await modmail.delete_many({'user_id': user_id})
                    await message.author.send(f"{tick} Conversation closed.")
                    return

                channelcreated = f"{channel.created_at.strftime('%d/%m/%Y')}"
                
                dm_channel = await message.author.create_dm()
                transcriptid = random.randint(100, 5000)
                try:
                 transcript = await chat_exporter.export(channel)    
                except Exception:
                       
                       await modmail.delete_many({'user_id': user_id})
                       await message.author.send(f"{tick} Conversation closed.")                       
                       return
                transcript_file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"transcript-{channel.name}.html")           
                if channel:
                    testchannel = self.client.get_channel(1202756318897774632)
                    message = await testchannel.send("<:infractionssearch:1234997448641085520> **HTML Transcript**", file=transcript_file)
                    link = await chat_exporter.link(message)
                    view = TranscriptChannel(link)                    
                    await channel.send(f"<:Messages:1148610048151523339> **{message.author.display_name}** has closed the modmail conversation.")
                    try:
                     await channel.delete()
                    except Exception:
                       await modmail.delete_many({'user_id': user_id})
                       await dm_channel.send(f"{tick} Conversation closed.")                       
                       return
                    await modmail.delete_many({'user_id': user_id})
                    await dm_channel.send(f"{tick} Conversation closed.")
                    transcriptschannelresult = await transcriptschannel.find_one({'guild_id': channel.guild.id})
                    if transcriptschannelresult:
                     transcriptchannelid = transcriptschannelresult.get('channel_id')
                     transcriptchannel = self.client.get_channel(transcriptchannelid)
                     if transcriptchannel:
                      embed = discord.Embed(title="Modmail Closed", description=f"", color=discord.Color.dark_embed())
                      embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon)
                      embed.add_field(name="<:Document:1191926049857097748> ID", value=transcriptid, inline=True)
                      embed.add_field(name="<:Add:1163095623600447558> Opened", value=message.author.mention, inline=True)
                      embed.add_field(name="<:Exterminate:1223063042246443078> Closed", value=message.author.mention, inline=True)
                      embed.add_field(name="<:casewarningwhite:1191903691750514708> Time Created", value=channelcreated, inline=True)
                      embed.add_field(name="<:reason:1202773873095868476> Reason", value="Closed by modmail author.", inline=True)
                      await dm_channel.send(embed=embed)
                      

                      await transcriptchannel.send(embed=embed, view=view)
                      await transcripts.insert_one({'transcriptid': transcriptid ,'guild_id': channel.guild.id, 'closedby': message.author.id, 'reason': "Closed by modmail author.", 'author': message.author.id,'timestamp': datetime.now(), 'transcriptlink': link})  
                else:
                    await dm_channel.send(f"{no} Modmail channel not found.")
                return
             

            if not modmail_data:
                if message.content.isdigit():
                    return

                last_selection_time = self.user_last_selection.get(user_id, datetime.utcnow() - timedelta(seconds=20))
                time_remaining = timedelta(seconds=20) - (datetime.utcnow() - last_selection_time)
                seconds_remaining = int(time_remaining.total_seconds())
                if seconds_remaining > 0 and seconds_remaining <= 20:
                 await message.author.send(f"{no} **{message.author.display_name},** please wait **{seconds_remaining} seconds** before opening another server list.", delete_after=seconds_remaining)
                 return
                self.user_last_selection[user_id] = datetime.utcnow()
                mutual_servers = [
                    guild for guild in self.client.guilds
                    if discord.utils.get(guild.members, id=user_id)
                    and await modmailcategory.find_one({'guild_id': guild.id})
                    and await modules.find_one({'guild_id': guild.id, 'Modmail': True})
                ]

                if not mutual_servers:
                    await message.author.send(f"{no} **{message.author.name},** you are not a member of any server with modmail enabled.")
                    return

                server_list = "\n".join([f"`{i+1}`. **{server.name}**" for i, server in enumerate(mutual_servers)])
                server_list += "\n\nPlease enter the number of the server you want to communicate with."

                self.user_last_selection[user_id] = datetime.utcnow()
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
                    blacklist = await modmailblacklists.find_one({'guild_id': selected_server.id})
                    if blacklist and user_id in blacklist['blacklist']:
                        await message.author.send(f"{no} **{message.author.display_name},** You are blacklisted from using modmail in **{selected_server.name}**.")
                        return
                except asyncio.TimeoutError:
                    await message.author.send(f"{no} **{message.author.name},** the server selection expired.")
                    return
                except ValueError:
                    await message.author.send(f"{no} **{message.author.name},** That isn't a valid number.")
                    return
                category_idresult = await modmailcategory.find_one({'guild_id': selected_server.id})
                category_id = category_idresult['category_id']

                category = self.client.get_channel(category_id)
                if category and isinstance(category, discord.CategoryChannel):
                    existing_modmail_data = await modmail.find_one({'user_id': user_id, 'guild_id': selected_server.id})
                    if existing_modmail_data:
                        channel_id = existing_modmail_data['channel_id']
                        channel = self.client.get_channel(channel_id)

                        if channel:
                            option = await options.find_one({'guild_id': selected_server.id})
                            if option:
                                    if option.get('MessageFormatting') == 'Messages':
                                     try:
                                        await channel.send(f"{mention}\n<:messagereceived:1201999712593383444> **{message.author.name}**: {message.content}")
                                        return  
                                     except discord.Forbidden:
                                      await message.reply(f"{no} **{message.author.name},** Please contact server admins I can't see the modmail channel.")                                    
                                      return

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
                             await message.reply(f"{no} **{message.author.name},** Please contact server admins I can't see the modmail channel.")                                    
                             return
                    else:
                        try:
                         channel = await category.create_text_channel(f'modmail-{message.author.name}')
                        except discord.Forbidden: 
                            await message.reply(f"{no} **{message.author.name},** please contact the server admins I can't create a channel.")
                            return
                        modmail_data = {
                            'user_id': user_id,
                            'guild_id': selected_server.id,
                            'channel_id': channel.id
                        }

                        modmail.insert_one(modmail_data)
        
                        await message.author.send(f"{tick} Conversation started.\n{dropdown} Use `!close` to close the conversation.")
                        user = await selected_server.fetch_member(user_id)
                        user_roles = " ".join([role.mention for role in user.roles if role != selected_server.default_role][:20])
                        rolecount = len(user.roles) - 1 if selected_server.default_role in user.roles else len(user.roles)

                        
                        modmailpingresult = await modmailping.find_one({'guild_id': selected_server.id})
                        modmailroles = ""
                        if modmailpingresult:
                            modmailroles = [f'<@&{roleid}>' for sublist in modmailpingresult['modmailping'] for roleid in sublist if selected_server.get_role(roleid) is not None]
                            modmailroles = ", ".join(filter(None, modmailroles))
                        info = discord.Embed(title="Member Information", description=f"* **User:** {message.author.mention}\n* **Joined:** <t:{int(user.joined_at.timestamp())}:F>\n* **Created:** <t:{int(user.created_at.timestamp())}:F>",timestamp=datetime.utcnow(), color=discord.Color.dark_embed())
                        if user_roles:
                            info.add_field(name=f"Roles [{rolecount}]", value=user_roles, inline=False)
                        info.set_author(name=message.author, icon_url=message.author.display_avatar)
                        info.set_thumbnail(url=message.author.display_avatar)
                        info.set_footer(text=f"ID: {message.author.id}")
                        await channel.send(f"{modmailroles}\n<:Messages:1148610048151523339> **{message.author.display_name}** has started a modmail conversation.", embed=info)
                        option = await options.find_one({'guild_id': selected_server.id})
                        if option:
                                    if option.get('MessageFormatting') == 'Messages':
                                     try:
                                        await channel.send(f"<:messagereceived:1201999712593383444> **{message.author.name}**: {message.content}")
                                        return  
                                     except discord.Forbidden:
                                      await message.reply(f"{no} **{message.author.name},** Please contact server admins I can't see the modmail channel.")                                    
                                      return                        
                        embed = discord.Embed(
                                    color=discord.Color.dark_embed(),
                                    title=message.author,
                                    description=f"```{message.content}```"
                                )                     
                        embed.set_author(name=message.author, icon_url=message.author.display_avatar)
                        embed.set_thumbnail(url=message.author.display_avatar)   
                        if message.attachments:
                            files = [await file.to_file() for file in message.attachments]
                            if message.content:
                                embed = discord.Embed(
                                    color=discord.Color.dark_embed(),
                                    title=message.author,
                                    description=f"```{message.content}```"
                                )
                                embed.set_author(name=message.author, icon_url=message.author.display_avatar)
                                embed.set_thumbnail(url=message.author.display_avatar)
                                msg = await channel.send(embed=embed)
                                await msg.reply("<:Image:1223063095417765938> **Attachment(s)** sent by the user.", files=files)
                                return
                            else:
                                await channel.send("<:Image:1223063095417765938> **Attachment(s)** sent by the user.", files=files)
                                return
                        try:
                            await channel.send(embed=embed)
                        except discord.Forbidden: 
                            await message.reply(f"{no} **{message.author.name}**, I can't see the modmail channel contact a server admin.")
                else:
                    await message.author.send(f"{no} **{message.author.name},** the servers modmail category is not found.")
            else:
                channel_id = modmail_data['channel_id']
                channel = self.client.get_channel(channel_id)
                mention = ""



                if channel:
                    modmailalertsresult = await modmailalerts.find_one({'channel_id': channel.id})
                    if modmailalertsresult:
                        mention = modmailalertsresult.get('alert')
                        modmailalerts.delete_one({'channel_id': channel.id, 'alert': mention})                         
                        if mention:
                            mention = f"<@{mention}>"

   
                    if message.attachments:
                      

                     files = [await file.to_file() for file in message.attachments]
                     if message.content:
                      embed = discord.Embed(
                      color=discord.Color.dark_embed(),
                      title=message.author,
                      description=f"```{message.content}```")
    
                      embed.set_author(name=message.author, icon_url=message.author.display_avatar)
                      embed.set_thumbnail(url=message.author.display_avatar)
                      msg = await channel.send(mention, embed=embed)
                      await msg.reply("<:Image:1223063095417765938> **Attachment(s)** sent by the user.", files=files)
                      return
                     else:
                      
                      await channel.send(f"{mention}\n<:Image:1223063095417765938> **Attachment(s)** sent by the user.", files=files)
                      return
                    await message.add_reaction('📨') 
                    
                    embed = discord.Embed(
                        color=discord.Color.dark_embed(),
                        title=message.author,
                        description=f"```{message.content}```"
                    )
                    embed.set_author(name=message.author, icon_url=message.author.display_avatar)
                    embed.set_thumbnail(url=message.author.display_avatar)
                    option = await options.find_one({'guild_id': channel.guild.id})
                    if option:
                            if option.get('MessageFormatting') == 'Messages':
                                await channel.send(f"{mention}\n<:messagereceived:1201999712593383444> **{message.author.name}**: {message.content}")
                                return                         
                    await channel.send(mention, embed=embed)
        elif isinstance(message.channel, discord.TextChannel):
         if message.guild is None:
            return
         option = await options.find_one({'guild_id': message.guild.id})
         media = ""
         if option and option.get('automessage') == True:
          modmail_data = await modmail.find_one({'channel_id': message.channel.id})
          if modmail_data:
                    channel = message.channel
                    if modmail_data.get('user_id'):
                        user_id = modmail_data.get('user_id')
                        user = await self.client.fetch_user(user_id)
                        mediamsg = ""
                        if message.attachments:
                            media = message.attachments[0].url
                            mediamsg = "**Attachment Below**"                    
                        
                        if option and option.get('MessageFormatting') == 'Messages':
                                 try: 
                                  await channel.send(f"<:messagereceived:1201999712593383444> **(Staff)** {message.author.name}: {message.content}\n{media}")
                                  await user.send(f"<:messagereceived:1201999712593383444> **(Staff)** {message.author.name}: {message.content}\n{media}")
                                  try:
                                   await message.delete()
                                  except discord.Forbidden:
                                     print('Couldn\'t delete the modmail message from a staff!') 
                                     return

                                 except discord.Forbidden: 
                                  print('I can\'t see the channel message in modmail.')                            
                                  return        
                        else:
                            embed = discord.Embed(color=discord.Color.dark_embed(), title=f"**(Staff)** {message.author.name}", description=f"```{message.content}```\n{mediamsg}")
                            embed.set_author(name=message.guild.name, icon_url=message.guild.icon)
                            embed.set_thumbnail(url=message.guild.icon)
                            embed.set_image(url=media)                            
                                
                            try:
                             await user.send(embed=embed)  
                             await channel.send(embed=embed)
                            except discord.Forbidden: 
                                print('I can\'t see the channel message in modmail.')
                            try:
                                   await message.delete()
                            except discord.Forbidden:
                                     print('Couldn\'t delete the modmail message from a staff!') 
                                     return
    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send(f"{no} **{ctx.author.display_name},** I can't execute commands in DMs. Please use the bot in a server.")
            return
            


class TranscriptChannel(discord.ui.View):
    def __init__(self, url):
        super().__init__()
        self.add_item(discord.ui.Button(label='Transcript', url=url, style=discord.ButtonStyle.blurple))




async def setup(client: commands.Bot) -> None:
    await client.add_cog(Modmailevnt(client))       
