import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *
import re
MONGO_URL = os.getenv('MONGO_URL')

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo['astro']
modules = db['Modules']
welcome = db['welcome settings']
custom_commands = db['Custom Commands']
from datetime import datetime

import random

class welcome2(commands.Cog):
    def __init__(self, client):
        self.client = client

    @staticmethod
    async def replace_variables(message, replacements):
     for placeholder, value in replacements.items():
        if value is not None:
            message = str(message).replace(placeholder, str(value))
        else:
            message = str(message).replace(placeholder, "")  
     return message

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        modulesresult = await modules.find_one({'guild_id': member.guild.id})
        if modulesresult is None:
            return
        if modulesresult.get('welcome', False) is False:
            return
        result = await welcome.find_one({'guild_id': member.guild.id})
        if result.get('welcome_channel', None) is None:
            return
        
        if result is None:
            return

        target_guild_id = member.guild.id
        guild_on_join = self.client.get_guild(target_guild_id)

        if guild_on_join and member.guild.id == target_guild_id:
            channel_id = result['welcome_channel']
            if channel_id is None:
                return
            channel = guild_on_join.get_channel(channel_id)
            if channel is None:
                return

            if channel:
                replacements = {
                    '{user}': member.name,
                    '{user.id}': str(member.id),
                    '{user.mention}': member.mention,
                    '{timestamp}': str(member.joined_at),
                    '{guild.name}': guild.name,
                    '{guild.id}': str(guild.id),
                    '{guild.owner.name}': guild.owner.name,
                    '{guild.owner.id}': str(guild.owner.id),
                    '{guild.owner.mention}': guild.owner.mention,
                    '{membercount}': int(guild.member_count)
                }
                command_data = result
                if 'buttons' in command_data and command_data['buttons'] == "Link Button":
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

                     emoji = member.guild.get_emoji(emoji_id)
                     if emoji:
                      view.button_callback.emoji = command_data.get('emoji', None)
                    
                     
                else:
                    view = None                                   
                if 'embed' in result and result['embed']:
                    embed_title = await self.replace_variables(result['title'], replacements)
                    embed_description = await self.replace_variables(result['description'], replacements)
                    embed_author = await self.replace_variables(result['author'], replacements)

                    if embed_title in ["None", None]:
                        embed_title = ""
                    if embed_description in ["None", None]:
                        embed_description = ""
                    color_value = result.get('color', None)
                    colors = discord.Colour(int(color_value, 16)) if color_value else discord.Colour.dark_embed()

                    embed = discord.Embed(
                        title=embed_title,
                        description=embed_description, color=colors)

                    if embed_author in ["None", None]:
                        embed_author = ""
                    if 'image' in result:
                        embed.set_image(url=result['image'])
                    if 'thumbnail' in result:
                        embed.set_thumbnail(url=result['thumbnail'])
                    if 'author' in result and 'author_icon' in result:
                        embed.set_author(name=embed_author, icon_url=result['author_icon'])    
                    contentresult = await self.replace_variables(result.get('content', ""), replacements)
                    if contentresult in ["None", None]:
                        contentresult = ""
                    try:
                     await channel.send(embed=embed, content=contentresult, view=view) 
                    except: 
                        print('I couldn\'t send it to the welcome channel')
                        return 
                else:
                    contentresult = await self.replace_variables(result.get('content', ""), replacements)
                    if contentresult in ["None", None]:
                        return
                    try:
                     await channel.send(contentresult, view=view) 
                    except: 
                        print('I couldn\'t send it to the welcome channel')
                        return 

class URL(discord.ui.View):
    def __init__(self, url, buttonname):
        super().__init__()
        self.add_item(discord.ui.Button(label=buttonname, url=url, style=discord.ButtonStyle.blurple))
        
class ButtonEmbed(discord.ui.View):
    def __init__(self, name):
        super().__init__()    
        self.name = name

    @staticmethod
    async def replace_variables(message, replacements):
     for placeholder, value in replacements.items():
        if value is not None:
            message = str(message).replace(placeholder, str(value))
        else:
            message = str(message).replace(placeholder, "")  
     return message
    
    @discord.ui.button()
    async def button_callback(self, interaction: discord.Interaction, button):

        command = self.name
        command_data  = await custom_commands.find_one({'name': command, 'guild_id': interaction.guild.id})
        if command_data is None:
            return await interaction.response.send_message(f'{no} **{interaction.user.display_name},** That command does not exist.', allowed_mentions=discord.AllowedMentions.none())
        

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
                        await interaction.response.send_message(content, embed=embed, view=view, ephemeral=True)


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
                        await interaction.response.send_message(content, view=view, ephemeral=True)

                    else:
                        await interaction.response.send_message(f"{no} **{interaction.user.display_name},** This command does not have any content or embed.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                        return
            except discord.Forbidden:
                    await interaction.response.send_message(f"{no} **{interaction.user.display_name},** I do not have permission to send messages in that channel.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                    return
        

        
    
                    




async def setup(client: commands.Bot) -> None:
    await client.add_cog(welcome2(client))                  
