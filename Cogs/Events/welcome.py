import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo['astro']
modules = db['Modules']
welcome = db['welcome settings']


class welcome2(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        modulesresult = await modules.find_one({'guild_id': member.guild.id})
        if modulesresult is None:
            return
        if modulesresult.get('welcome', False) == False:
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
                    '{user}': member.display_name,
                    '{user.id}': str(member.id),
                    '{user.mention}': member.mention,
                    '{timestamp}': str(member.joined_at),
                    '{guild.name}': guild.name,
                    '{guild.id}': str(guild.id),
                    '{guild.owner.name}': guild.owner.display_name,
                    '{guild.owner.id}': str(guild.owner.id),
                    '{guild.owner.mention}': guild.owner.mention
                }                
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
                    contentresult = await self.replace_variables(result['content'], replacements)
                    if contentresult in ["None", None]:
                        contentresult = ""
                    try:
                     await channel.send(embed=embed, content=contentresult) 
                    except: 
                        print('I couldn\'t send it to the welcome channel')
                        return 
                else:
                    contentresult = await self.replace_variables(result['content'], replacements)
                    if contentresult in ["None", None]:
                        return
                    try:
                     await channel.send(contentresult) 
                    except: 
                        print('I couldn\'t send it to the welcome channel')
                        return 


    
                    

    async def replace_variables(self, message, replacements):
     for placeholder, value in replacements.items():
        if value is not None:
            message = str(message).replace(placeholder, str(value))
        else:
            message = str(message).replace(placeholder, "")  
     return message


async def setup(client: commands.Bot) -> None:
    await client.add_cog(welcome2(client))                  