import discord
from discord.ext import commands
from discord.ext import commands
from emojis import *
from discord import app_commands
import os
import typing
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from permissions import has_admin_role
import string
import random
import re
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']

custom_commands = db['Custom Commands']
CustomVoting = db['Commands Voting']
commandslogging = db['Commands Logging']
prefixdb = db['prefixes']
class CustomCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client



    async def commands_auto_complete(
        ctx: commands.Context,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        try:
            filter = {
                'guild_id': interaction.guild_id 
            }

            tag_names = await custom_commands.distinct("name", filter)

 
            filtered_names = [name for name in tag_names if current.lower() in name.lower()]


            choices = [app_commands.Choice(name=name, value=name) for name in filtered_names[:25]]

            return choices
        except Exception as e:
            print(f"Error in commands_auto_complete: {e}")
            return []
        
    @commands.hybrid_group()
    async def command(self, ctx):
        pass
     
    @commands.command()
    async def prefix(self, ctx: commands.Context, prefix: str = None):
        result = await prefixdb.find_one({'guild_id': ctx.guild.id})
        currentprefix = result.get('prefix', "!!")
        if prefix is None:
            
            await ctx.send(f"<:command1:1199456319363633192> **{ctx.author.display_name},** the prefix is `{currentprefix}`", allowed_mentions=discord.AllowedMentions.none()) 
        else:
            if ctx.author.guild_permissions.manage_guild:
             await prefixdb.update_one({'guild_id': ctx.guild.id}, {'$set': {'prefix': prefix}}, upsert=True)
             await ctx.send(f"<:whitecheck:1190819388941668362> **{ctx.author.display_name},** I've set the prefix to `{prefix}`", allowed_mentions=discord.AllowedMentions.none())
            else:
                  await ctx.send(f"<:command1:1199456319363633192> **{ctx.author.display_name},** the prefix is `{currentprefix}`", allowed_mentions=discord.AllowedMentions.none()) 






    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot: 
            return

        if not message.guild:  
            return

        try:
            
            result = await custom_commands.find({'guild_id': message.guild.id}).to_list(length=None)



            prefixes = await self.client.get_prefix(message)
            for prefix in prefixes:
                if message.content.startswith(prefix):
                    command = message.content[len(prefix):]
                    command = re.sub(r'^[^a-zA-Z0-9]+', '', command)
                    break
            else:
                
                return

            for command_data in result:

                
                if command_data.get('name') == command:
                    
                    if not await has_customcommandrole2(message, command):
                        return
                    if 'buttons' in command_data:
                        if command_data['buttons'] == "Voting Buttons":
                            view = Voting()
                        elif command_data['buttons'] == "Link Button":
                            view = URL(command_data['url'], command_data['button_label'])
                        elif command_data['buttons'] == "Embed Button":
                            label = command_data['button_label']
                            colour = command_data['colour']
                            name = command_data['cmd']
                            view = ButtonEmbed(name)
                            view.button_callback.label = label

                            if colour == "Blurple":
                                view.button_callback.style = discord.ButtonStyle.blurple
                            elif colour == "Green":
                                view.button_callback.style = discord.ButtonStyle.green
                            elif colour == "Red":
                                view.button_callback.style = discord.ButtonStyle.red
                            elif colour == "Grey":
                                view.button_callback.style = discord.ButtonStyle.grey    
                            else:
                                view.button_callback.style = discord.ButtonStyle.grey  

                            emoji_data = command_data.get('emoji', None)
                            
                            if emoji_data:
                                emoji_id_str = emoji_data.split(':')[2][:-1]
                                emoji_id = int(emoji_id_str)
                                emoji = message.guild.get_emoji(emoji_id)
                                if emoji:
                                    view.button_callback.emoji = command_data.get('emoji', None)
                        else:
                            view = None
                    else:
                        view = None


                    timestamp = datetime.utcnow().timestamp()
                    timestampformat = f"<t:{int(timestamp)}:F>"
                    replacements = {
                        '{author.mention}': message.author.mention,
                        '{author.name}': message.author.display_name,
                        '{author.id}': str(message.author.id),
                        '{timestamp}': timestampformat,
                        '{guild.name}': message.guild.name if message.guild else '',
                        '{guild.id}': str(message.guild.id) if message.guild else '',
                        '{guild.owner.mention}': message.guild.owner.mention if message.guild and message.guild.owner else '',
                        '{guild.owner.name}': message.guild.owner.display_name if message.guild and message.guild.owner else '',
                        '{guild.owner.id}': str(message.guild.owner.id) if message.guild and message.guild.owner else '',
                        '{random}': int(random.randint(1, 1000000)),
                        '{guild.members}': int(message.guild.member_count),
                        '{channel.name}': message.channel.name if message.channel else message.channel.name,
                        '{channel.id}': str(message.channel.id) if message.channel else str(message.channel.id),
                        '{channel.mention}': message.channel.mention if message.channel else message.channel.mention,
                    }

                    content = await self.replace_variables(command_data.get('content', ''), replacements)
                    if content == "":
                        content = ""


                    if 'embed' in command_data and command_data['embed']:
                        embed_title = await self.replace_variables(command_data['title'], replacements)
                        embed_description = await self.replace_variables(command_data['description'], replacements)
                        embed_author = await self.replace_variables(command_data['author'], replacements)

                        if embed_title in ["None", None]:
                            embed_title = ""
                        if embed_description in ["None", None]:
                            embed_description = ""
                        color_value = command_data.get('color', None)
                        colors = discord.Colour(int(color_value, 16)) if color_value else discord.Colour.dark_embed()

                        embed = discord.Embed(
                            title=embed_title,
                            description=embed_description, color=colors)

                        if embed_author in ["None", None]:
                            embed_author = ""
                        if 'image' in command_data:
                            embed.set_image(url=command_data['image'])
                        if 'thumbnail' in command_data:
                            embed.set_thumbnail(url=command_data['thumbnail'])
                        if 'author' in command_data and 'author_icon' in command_data:
                            embed.set_author(name=embed_author, icon_url=command_data['author_icon'])
                        try:
                                if content or embed or view:
                                    try:
                                     msg = await message.channel.send(content, embed=embed, view=view)
                                    except discord.Forbidden:
                                        print("[ERROR] I couldn't send a custom command in a command trigger") 
                                        return
                                    try:
                                        await message.delete()
                                    except discord.Forbidden:
                                        print("[ERROR] I couldn't delete a command trigger")



                                    loggingdata = await commandslogging.find_one({"guild_id": message.guild.id})
                                    if loggingdata:
                                        loggingchannel = self.client.get_channel(loggingdata["channel_id"])
                                        if loggingchannel:
                                         embed = discord.Embed(
                                            title="Custom Command Usage",
                                            description=f"Command **{command}** was used by {message.author.mention} in {message.channel.mention}",
                                            color=discord.Color.dark_embed(),
                                        )
                                         embed.set_author(
                                            name=message.author.display_name, icon_url=message.author.display_avatar
                                        )
                                         try:
                                            await loggingchannel.send(embed=embed)
                                         except (discord.Forbidden, discord.HTTPException):
                                            print(
                                                f"I could not find the channel to send the tag usage (guild: {message.guild.name})"
                                            )
                                        else:
                                            print("I could not find the channel to send the command usage")                                    
                                else:
                                    await message.channel.send(f"{no} **{message.author.display_name},** This command does not have any content or embed.", allowed_mentions=discord.AllowedMentions.none())
                                    return
                                

                        except discord.Forbidden:
                                print('[ERROR CUSTOM COMMAND AUTORESPONSE] I couldn\'t send a message in that channel.')
                                return
                        
                    else:
                        if content is None:
                            await message.channel.send(f"{no} **{message.author.display_name},** That command does not have any content or embeds.", allowed_mentions=discord.AllowedMentions.none())
                            return
                        try:
                         if content or view:
                                    try:
                                     msg = await message.channel.send(content, view=view)
                                    except discord.Forbidden: 
                                     print(f"I couldn't send a message in that channel.") 
                                     return
                                    try:
                                     await message.delete()
                                    except discord.Forbidden: 
                                     print(f"I couldn't delete the message that triggered the command")                                   
                                    loggingdata = await commandslogging.find_one({"guild_id": message.guild.id})
                                    if loggingdata:
                                        loggingchannel = self.client.get_channel(loggingdata["channel_id"])
                                        if loggingchannel:
                                         embed = discord.Embed(
                                            title="Custom Command Usage",
                                            description=f"Command **{command}** was used by {message.author.mention} in {message.channel.mention}",
                                            color=discord.Color.dark_embed(),
                                        )
                                         embed.set_author(
                                            name=message.author.display_name, icon_url=message.author.display_avatar
                                        )
                                         try:
                                            await loggingchannel.send(embed=embed)
                                         except (discord.Forbidden, discord.HTTPException):
                                            print(
                                                f"I could not find the channel to send the tag usage (guild: {message.guild.name})"
                                            )
                                        else:
                                            print("I could not find the channel to send the command usage")                                        
                         else:
                             await message.channel.send(f"{no} **{message.author.display_name},** This command does not have any content or embed.", allowed_mentions=discord.AllowedMentions.none())
                             return

                         
                         
                        except discord.Forbidden:
                            print('[ERROR] I do not have permission to send messages in that channel or can\' delete the message.')
                            return
                    if command_data.get('buttons', None) == "Voting Buttons":
                     print("Yes, there are buttons")
                     voting_data = {
                        'guild_id': message.guild.id,
                        'message_id': msg.id,
                        'author': message.author.id,
                        'votes': 0,
                        'Voters': []
                    }
                     await CustomVoting.insert_one(voting_data)

        except (discord.NotFound, discord.HTTPException):
            print('Error occurred')
            return
          


    @command.command(description="Run one of your servers custom commands.")
    @app_commands.autocomplete(command=commands_auto_complete)
    @app_commands.describe(command = 'The name of the command you want to run.')
    async def run(self, ctx: commands.Context, command, channel: discord.TextChannel = None):
        await ctx.defer(ephemeral=True)
        if not await has_customcommandrole(ctx, command):
            return
        
        command_data  = await custom_commands.find_one({'name': command, 'guild_id': ctx.guild.id})
        if command_data is None:
            return await ctx.send(f'{no} **{ctx.author.display_name},** That command does not exist.', allowed_mentions=discord.AllowedMentions.none())
        
        if 'buttons' in command_data and command_data['buttons'] == "Voting Buttons":
            view = Voting()
        elif 'buttons' in command_data and command_data['buttons'] == "Link Button":
            view = URL(command_data['url'], command_data['button_label'])

        elif 'buttons' in command_data and command_data['buttons'] == "Embed Button":
            label = command_data['button_label']
            colour = command_data['colour']
            name = command_data['cmd']
            print(name)


            view = ButtonEmbed(name)   
            view.button_callback.label = label
            

            if colour == "Blurple":
                view.button_callback.style = discord.ButtonStyle.blurple
            elif colour == "Green":
                view.button_callback.style = discord.ButtonStyle.green
            elif colour == "Red":
                view.button_callback.style = discord.ButtonStyle.red
            elif colour == "Grey":
                view.button_callback.style = discord.ButtonStyle.grey    
            else:
                view.button_callback.style = discord.ButtonStyle.grey  
            emoji_data = command_data.get('emoji', None)
            print(emoji_data)

                    
            if emoji_data:
                emoji_id_str = emoji_data.split(':')[2][:-1]
                emoji_id = int(emoji_id_str)

                emoji = ctx.guild.get_emoji(emoji_id)
                if emoji:
                      view.button_callback.emoji = command_data.get('emoji', None)
        else:
            view = None               
        timestamp = datetime.utcnow().timestamp()
        timestampformat = f"<t:{int(timestamp)}:F>"

        replacements = {
            '{author.mention}': ctx.author.mention,
            '{author.name}': ctx.author.display_name,
            '{author.id}': str(ctx.author.id),
            '{timestamp}': timestampformat,
            '{guild.name}': ctx.guild.name if ctx.guild else '',
            '{guild.id}': str(ctx.guild.id) if ctx.guild else '',
            '{guild.owner.mention}': ctx.guild.owner.mention if ctx.guild and ctx.guild.owner else '',
            '{guild.owner.name}': ctx.guild.owner.display_name if ctx.guild and ctx.guild.owner else '',
            '{guild.owner.id}': str(ctx.guild.owner.id) if ctx.guild and ctx.guild.owner else '',
            '{random}': int(random.randint(1, 1000000)),
            '{guild.members}': int(ctx.guild.member_count),
            '{channel.name}': channel.name if channel else ctx.channel.name,
            '{channel.id}': str(channel.id) if channel else str(ctx.channel.id),
            '{channel.mention}': channel.mention if channel else ctx.channel.mention,

        }
               
             

        content = await self.replace_variables(command_data.get('content', ''), replacements)
        if content == "":
            content = ""

        if 'embed' in command_data and command_data['embed']:
            embed_title = await self.replace_variables(command_data['title'], replacements)
            embed_description = await self.replace_variables(command_data['description'], replacements)
            embed_author = await self.replace_variables(command_data['author'], replacements)

            if embed_title in ["None", None]:
                embed_title = ""
            if embed_description in ["None", None]:
                embed_description = ""
            color_value = command_data.get('color', None)
            colors = discord.Colour(int(color_value, 16)) if color_value else discord.Colour.dark_embed()

            embed = discord.Embed(
                title=embed_title,
                description=embed_description, color=colors)

            if embed_author in ["None", None]:
                embed_author = ""
            if 'image' in command_data:
                embed.set_image(url=command_data['image'])
            if 'thumbnail' in command_data:
                embed.set_thumbnail(url=command_data['thumbnail'])
            if 'author' in command_data and 'author_icon' in command_data:
                embed.set_author(name=embed_author, icon_url=command_data['author_icon'])

            if channel:
                try:
                    if content or embed or view:
                        msg = await channel.send(content, embed=embed, view=view)


                    else:
                        await ctx.send(f"{no} **{ctx.author.display_name},** This command does not have any content or embed.", allowed_mentions=discord.AllowedMentions.none())
                        return
                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name},** I do not have permission to send messages in that channel.", allowed_mentions=discord.AllowedMentions.none())
                    return
                await ctx.send(f"{tick} **{ctx.author.display_name},** The command has been sent", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

            else:
                try:
                    if content or embed or view:
                        msg = await ctx.channel.send(content, embed=embed, view=view)


                    else:
                        await ctx.send(f"{no} **{ctx.author.display_name},** This command does not have any content or embed.", allowed_mentions=discord.AllowedMentions.none())
                        return
                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name},** I do not have permission to send messages in that channel.", allowed_mentions=discord.AllowedMentions.none())
                    return
                await ctx.send(f"{tick} **{ctx.author.display_name},** The command has been sent", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                loggingdata = await commandslogging.find_one({"guild_id": ctx.guild.id})
                if loggingdata:
                    loggingchannel = self.client.get_channel(loggingdata["channel_id"])
                    if loggingchannel:
                     embed = discord.Embed(
                        title="Custom Command Usage",
                        description=f"Command **{command}** was used by {ctx.author.mention} in {ctx.channel.mention}",
                        color=discord.Color.dark_embed(),
                    )
                     embed.set_author(
                        name=ctx.author.display_name, icon_url=ctx.author.display_avatar
                    )
                     try:
                        await loggingchannel.send(embed=embed)
                     except (discord.Forbidden, discord.HTTPException):
                        print(
                            f"I could not find the channel to send the tag usage (guild: {ctx.guild.name})"
                        )
        else:
            if content is None:
                await ctx.send(f"{no} **{ctx.author.display_name},** That command does not have any content or embeds.", allowed_mentions=discord.AllowedMentions.none())
                return
            if channel:
                try:
                    if content or view:
                        msg = await channel.send(content, view=view)

                    else:
                        await ctx.send(f"{no} **{ctx.author.display_name},** This command does not have any content or embed.", allowed_mentions=discord.AllowedMentions.none())
                        return
                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name},** I do not have permission to send messages in that channel.", allowed_mentions=discord.AllowedMentions.none())
                    return
                await ctx.send(f"{tick} **{ctx.author.display_name},** The command has been sent", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

            else:
                try:
                    if content or view:
                        msg = await ctx.channel.send(content, view=view)

                    else:
                        await ctx.send(f"{no} **{ctx.author.display_name},** This command does not have any content or embed.", allowed_mentions=discord.AllowedMentions.none())
                        return
                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name},** I do not have permission to send messages in that channel.", allowed_mentions=discord.AllowedMentions.none())
                    return
                await ctx.send(f"{tick} {ctx.author.display_name}, The command has been sent", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())    
                loggingdata = await commandslogging.find_one({"guild_id": ctx.guild.id})
                if loggingdata:
                    loggingchannel = self.client.get_channel(loggingdata["channel_id"])
                    if loggingchannel:
                     embed = discord.Embed(
                        title="Custom Command Usage",
                        description=f"Command **{command}** was used by {ctx.author.mention} in {ctx.channel.mention}",
                        color=discord.Color.dark_embed(),
                    )
                     embed.set_author(
                        name=ctx.author.display_name, icon_url=ctx.author.display_avatar
                    )
                     try:
                        await loggingchannel.send(embed=embed)
                     except (discord.Forbidden, discord.HTTPException):
                        print(
                            f"I could not find the channel to send the tag usage (guild: {ctx.guild.name})"
                        )
                    else:
                        print("I could not find the channel to send the command usage")
        if command_data.get('buttons', None) == "Voting Buttons":
            print("yes there are buttons")
            voting_data = {
                'guild_id': ctx.guild.id,
                'message_id': msg.id,
                'author': ctx.author.id,
                'votes': 0,
                'Voters': []
            }
            await CustomVoting.insert_one(voting_data)



    @staticmethod
    async def replace_variables(message, replacements):
     for placeholder, value in replacements.items():
        if value is not None:
            message = str(message).replace(placeholder, str(value))
        else:
            message = str(message).replace(placeholder, "")  
     return message
        
        
class Voting(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        


    @discord.ui.button(label="0", style=discord.ButtonStyle.green, emoji=f"{tick}", custom_id="vote")
    async def upvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        message_id = interaction.message.id
        print(interaction.message.id)
        
 

        voting = await CustomVoting.find_one({"message_id": interaction.message.id})
        print(voting)

        if interaction.user.id in voting.get('Voters', []):
         CustomVoting.update_one(
        {"message_id": message_id},
        {
            "$inc": {"votes": -1},
            "$pull": {"Voters": interaction.user.id},
        },
         )
         new_label = str(voting.get('votes', 0) - 1)
         button.label = new_label
         await interaction.message.edit(view=self)
         await interaction.followup.send(f"{tick} **{interaction.user.display_name},** You have successfully unvoted.", ephemeral=True)
         return

        CustomVoting.update_one(
        {"message_id": message_id},
        {
            "$inc": {"votes": 1},
            "$push": {"Voters": interaction.user.id},
        },
         )
        new_label = str(voting.get('votes', 0) + 1)
        button.label = new_label

        await interaction.followup.send(f"{tick} **{interaction.user.display_name},** You have successfully voted.", ephemeral=True)

        await interaction.message.edit(view=self)
 
    @discord.ui.button(label="Voters", style=discord.ButtonStyle.blurple, emoji=f"{folder}", custom_id="viewlist")
    async def list(self, interaction: discord.Interaction, button: discord.ui.Button):
        voting = await CustomVoting.find_one({"message_id": interaction.message.id})
        voters = voting.get('Voters', [])
        if not voters: 
         voters_str = f"**{interaction.user.display_name},** there are no voters!"
        else:
         voters_str = "\n".join([f"<@{voter}> ({voter})" for voter in voters])
 

        embed_description = str(voters_str)[:4096]
        embed = discord.Embed(title="Voters", description=embed_description, color=discord.Color.dark_embed())
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def has_customcommandrole2(message: discord.Message, command):
    filter = {
        'guild_id': message.guild.id,
        'name': command
    }
    role_data = await custom_commands.find_one(filter)

    if role_data and 'permissionroles' in role_data:
        role_ids = role_data['permissionroles']
        if not isinstance(role_ids, list):
            role_ids = [role_ids]

        if any(role.id in role_ids for role in message.author.roles):
            return True
        else:
            await message.reply(f"{no} **{message.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Custom Command Permission`")
            return False
    else:
        return True
async def has_customcommandrole(ctx, command):
    filter = {
        'guild_id': ctx.guild.id,
        'name': command
    }
    role_data = await custom_commands.find_one(filter)

    if role_data and 'permissionroles' in role_data:
        role_ids = role_data['permissionroles']
        if not isinstance(role_ids, list):
            role_ids = [role_ids]

        if any(role.id in role_ids for role in ctx.author.roles):
            return True
        else:
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Custom Command Permission`")
            return False
    else:

        return await has_admin_role(ctx)

class URL(discord.ui.View):
    def __init__(self, url, buttonname):
        super().__init__()
        self.add_item(discord.ui.Button(label=buttonname, url=url, style=discord.ButtonStyle.blurple))
        
class ButtonEmbed(discord.ui.View):
    def __init__(self, name):
        super().__init__()    
        self.name = name

    @discord.ui.button()
    async def button_callback(self, interaction: discord.Interaction, button):

        command = self.name
        command_data  = await custom_commands.find_one({'name': command, 'guild_id': interaction.guild.id})
        if command_data is None:
            return await interaction.response.send(f'{no} **{interaction.user.display_name},** That command does not exist.', allowed_mentions=discord.AllowedMentions.none())
        

        if 'buttons' in command_data and command_data['buttons'] == "Link Button":
            view = URL(command_data['url'], command_data['button_label'])
        else:
            view = None

        timestamp = datetime.utcnow().timestamp()
        timestampformat = f"<t:{int(timestamp)}:F>"
        channel = interaction.channel
        

        replacements = {
            '{author.mention}': interaction.user.mention,
            '{author.name}': interaction.user.display_name,
            '{author.id}': str(interaction.user.id),
            '{timestamp}': timestampformat,
            '{guild.name}': interaction.guild.name if interaction.guild else '',
            '{guild.id}': str(interaction.guild.id) if interaction.guild else '',
            '{guild.owner.mention}': interaction.guild.owner.mention if interaction.guild and interaction.guild.owner else '',
            '{guild.owner.name}': interaction.guild.owner.display_name if interaction.guild and interaction.guild.owner else '',
            '{guild.owner.id}': str(interaction.guild.owner.id) if interaction.guild and interaction.guild.owner else '',
            '{random}': int(random.randint(1, 1000000)),
            '{guild.members}': int(interaction.guild.member_count),
            '{channel.name}': channel.name if channel else interaction.channel.name,
            '{channel.id}': str(channel.id) if channel else str(interaction.channel.id),
            '{channel.mention}': channel.mention if channel else interaction.channel.mention,

        }
               
             

        content = await self.replace_variables(command_data.get('content', ''), replacements)
        if content == "":
            content = ""

        if 'embed' in command_data and command_data['embed']:
            embed_title = await self.replace_variables(command_data['title'], replacements)
            embed_description = await self.replace_variables(command_data['description'], replacements)
            embed_author = await self.replace_variables(command_data['author'], replacements)

            if embed_title in ["None", None]:
                embed_title = ""
            if embed_description in ["None", None]:
                embed_description = ""
            color_value = command_data.get('color', None)
            colors = discord.Colour(int(color_value, 16)) if color_value else discord.Colour.dark_embed()

            embed = discord.Embed(
                title=embed_title,
                description=embed_description, color=colors)

            if embed_author in ["None", None]:
                embed_author = ""
            if 'image' in command_data:
                embed.set_image(url=command_data['image'])
            if 'thumbnail' in command_data:
                embed.set_thumbnail(url=command_data['thumbnail'])
            if 'author' in command_data and 'author_icon' in command_data:
                embed.set_author(name=embed_author, icon_url=command_data['author_icon'])


            try:
                    if content or embed or view:
                        msg = await interaction.response.send_message(content, embed=embed, view=view, ephemeral=True)


                    else:
                        await interaction.response.send_message(f"{no} **{interaction.user.display_name},** This command does not have any content or embed.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                        return
            except discord.Forbidden:
                    await interaction.response.send_message(f"{no} **{interaction.user.display_name},** I do not have permission to send messages in that channel.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                    return

        else:
            if content is None:
                await interaction.response.send_message(f"{no} **{interaction.user.display_name},** That command does not have any content or embeds.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                return

            try:
                    if content or view:
                        msg = await interaction.response.send_message(content, view=view, ephemeral=True)

                    else:
                        await interaction.response.send_message(f"{no} **{interaction.user.display_name},** This command does not have any content or embed.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                        return
            except discord.Forbidden:
                    await interaction.response.send_message(f"{no} **{interaction.user.display_name},** I do not have permission to send messages in that channel.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                    return
        
    @staticmethod
    async def replace_variables(message, replacements):
     for placeholder, value in replacements.items():
        if value is not None:
            message = str(message).replace(placeholder, str(value))
        else:
            message = str(message).replace(placeholder, "")  
     return message
        




async def setup(client: commands.Bot) -> None:
    await client.add_cog(CustomCommands(client))     
