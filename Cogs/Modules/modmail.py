
import discord
from discord.ext import commands, tasks
from pymongo import MongoClient
from emojis import *
from typing import Literal
import os
from dotenv import load_dotenv
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
modmail = db['modmail']
modmailcategory = db['modmailcategory']
from permissions import has_admin_role, has_staff_role
class Modmail(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def has_staff_role(self, ctx):
     filter = {
        'guild_id': ctx.guild.id
    }
     staff_data = scollection.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_ids)
        if not isinstance(staff_role_ids, list):
          staff_role_ids = [staff_role_ids]   
        if any(role.id in staff_role_ids for role in ctx.author.roles):
            return True

     return False


    async def has_admin_role(self, ctx):
     filter = {
        'guild_id': ctx.guild.id
    }
     staff_data = arole.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_ids)
        if not isinstance(staff_role_ids, list):
          staff_role_ids = [staff_role_ids]     
        if any(role.id in staff_role_ids for role in ctx.author.roles):
            return True

     return False

    @commands.hybrid_group()
    async def modmail(self, ctx):
        return
    




    @modmail.command(description="Reply to a modmail")
    async def reply(self, ctx, *, content):
     if not await has_staff_role(ctx):
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
     if not await has_staff_role(ctx):
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
                    user = await self.client.fetch_user(user_id)
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