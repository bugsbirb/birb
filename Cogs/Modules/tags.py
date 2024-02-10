import discord
from discord.ext import commands
from discord import app_commands
from emojis import *
import typing
import os
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
tags = db['tags']
modules = db['Modules']
from permissions import has_admin_role, has_staff_role
class Tags(commands.Cog):
    def __init__(self, client):
        self.client = client
 


    async def modulecheck(self, ctx): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Tags'] == True:   
        return True



    async def tag_name_autocompletion(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        filter = {
            'guild_id': interaction.guild_id 
        }

        tag_names = await tags.distinct("name", filter)

        filtered_names = [name for name in tag_names if current.lower() in name.lower()]

        choices = [app_commands.Choice(name=name, value=name) for name in filtered_names]

        return choices


    @commands.hybrid_group()
    async def tags(self, ctx):
        return

    @tags.command(description="Create a tag")    
    async def create(self, ctx, name: str, content: str):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return                 
        if not await has_admin_role(ctx):
         return               

        data = {
            'management': ctx.author.id,
            'name': name,
            'content': content,
            'guild_id': ctx.guild.id
        }
        await tags.insert_one(data)
        await ctx.send(f"{tick} **`{name}`** created.")


    @tags.command(description="List all available tags")
    async def all(self, ctx):
     await ctx.defer()
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return                 
     if not await has_staff_role(ctx):
            return               
     filter = {
        'guild_id': ctx.guild.id
    }

     tag_data = tags.find(filter)

     if tag_data:
        embed = discord.Embed(title="Tags List", color=discord.Color.dark_embed())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")

        async for tag in tag_data:
            name = tag['name']
            content = tag['content']

            embed.add_field(name=name, value=content, inline=False)

        await ctx.send(embed=embed)
     else:
        await ctx.send(f"{no} No tags found.")

    @tags.command(description="Information about a tag")
    @app_commands.autocomplete(name=tag_name_autocompletion)
    async def info(self, ctx, name):
        await ctx.defer()
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return                 
        if not await has_admin_role(ctx):
            return

        filter = {
            'guild_id': ctx.guild.id,
            'name': name
        }

        tag_data = await tags.find_one(filter)

        if tag_data:
            created_by = tag_data['management']
            context = tag_data['content']
            manager = await self.client.fetch_user(created_by)

            embed = discord.Embed(title=f"{name} Information", description=f"* **Created By:** {manager.mention}\n* **Content:** {context}", color=discord.Color.dark_embed())
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{no} Tag with the name `{name}` not found.")

    @tags.command(description="Send a existing tag to this channel.")        
    @app_commands.autocomplete(name=tag_name_autocompletion)
    async def send(self, ctx, name):
        await ctx.defer()
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return                 
        if not await has_staff_role(ctx):
            return        
        filter = {
            'guild_id': ctx.guild.id,
            'name': name
        }

        tag_data = await tags.find_one(filter) 

        if tag_data:
            content = tag_data.get('content')
            channel = ctx.channel
            await ctx.send(f"{tick} tag **sent**", ephemeral=True)
            await channel.send(content)
        else:
            await ctx.send(f"{no} Tag with the name `{name}` not found.")

    @tags.command(description="Delete a existing tag")        
    @app_commands.autocomplete(name=tag_name_autocompletion)
    async def delete(self, ctx, name):
        await ctx.defer()
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return                 
        if not await has_admin_role(ctx):
            return        
        filter = {
            'guild_id': ctx.guild.id,
            'name': name
        }        
        tagsz = await tags.find_one(filter)
        if tagsz is None:
         await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find the tag **`{name}`**.")
         return
        await tags.delete_one(filter)        
        await ctx.send(f"{tick} Tag **`{name}`** has been deleted.")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Tags(client))        