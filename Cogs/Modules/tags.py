import discord
from discord.ext import commands
from discord import app_commands
from emojis import *
import typing
import os

import Paginator
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
tags = db['tags']
modules = db['Modules']
tagslogging = db['Tags Logging']
from permissions import has_admin_role, has_staff_role
class Tags(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def modulecheck(self, ctx: commands.Context): 
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
    async def tags(self, ctx: commands.Context):
        return

    @tags.command(description="Create a tag")    
    @app_commands.describe(name = "The name of the tag", content = "The content of the tag.")
    async def create(self, ctx: commands.Context, name: str, content: str):
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
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

    @tags.command(description="Edit a tag")
    @app_commands.describe(name = "The name of the tag", content = "The content of the tag.")
    async def edit(self, ctx: commands.Context, name: str, content: str):
        await ctx.defer()
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the tags module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return                 
        if not await has_admin_role(ctx):
            return
        filter = {
            'guild_id': ctx.guild.id,
            'name': name
        }

        tag_data = await tags.find_one(filter)

        if tag_data:
            await tags.update_one(filter, {"$set": {"content": content}})
            await ctx.send(f"{tick} **`{name}`** has been updated.")
        else:
            await ctx.send(f"{no} Tag with the name `{name}` not found.")

    @tags.command(description="List all available tags")
    async def all(self, ctx: commands.Context):
        await ctx.defer()
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the tags module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return                 
        if not await has_staff_role(ctx):
            return               
        
        filter = {
            'guild_id': ctx.guild.id
        }

        tag_data = tags.find(filter)
        tag_data = await tag_data.to_list(length=750)
        if tag_data is None:
            await ctx.send(f"{no} No tags found.")
            return

        embeds = []
        embed = discord.Embed(title="Tags List", color=discord.Color.dark_embed())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")

        count = 0
        
        for tag in tag_data:
            name = tag['name']
            content = tag['content']

            embed.add_field(name=name, value=content, inline=False)
            count += 1

            if count % 9 == 0 or count == len(tag_data):
                embeds.append(embed)
                embed = discord.Embed(title="Tags List", color=discord.Color.dark_embed())
                embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
                embed.set_thumbnail(url=ctx.guild.icon)
                embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")
                

        PreviousButton = discord.ui.Button(label="<")
        NextButton = discord.ui.Button(label=">")
        FirstPageButton = discord.ui.Button(label="<<")
        LastPageButton = discord.ui.Button(label=">>")
        if len(embeds) <= 1:
            PreviousButton.disabled = True
            NextButton.disabled = True
            FirstPageButton.disabled = True
            LastPageButton.disabled = True
        InitialPage = 0
        timeout = 42069
        paginator = Paginator.Simple(
            PreviousButton=PreviousButton,
            NextButton=NextButton,
            FirstEmbedButton=FirstPageButton,
            LastEmbedButton=LastPageButton,
            InitialPage=InitialPage,
            timeout=timeout
        )

        await paginator.start(ctx, pages=embeds)


    @tags.command(description="Information about a tag")
    @app_commands.autocomplete(name=tag_name_autocompletion)
    @app_commands.describe(name = "The name of the tag")
    async def info(self, ctx: commands.Context, name: app_commands.Range[str, 1, 50]):
        await ctx.defer()
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the tags module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
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
    @app_commands.describe(name = "The name of the tag")    
    async def send(self, ctx: commands.Context, name: app_commands.Range[str, 1, 50]):
        await ctx.defer(ephemeral=True)
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the tags module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return                 
        if not await has_staff_role(ctx):
            return        
        filter = {
            'guild_id': ctx.guild.id,
            'name': name
        }

        tag_data = await tags.find_one(filter) 
        tagsloggingdata = await tagslogging.find_one({'guild_id': ctx.guild.id})

        if tag_data:
            content = tag_data.get('content')
            channel = ctx.channel
            await ctx.send(f"{tick} tag **sent**", ephemeral=True)
            await channel.send(content)
            if tagsloggingdata:
                channel = self.client.get_channel(tagsloggingdata["channel_id"])
                if channel:
                    embed = discord.Embed(
                        title=f"Tag Usage",
                        description=f"Tag **{name}** was used by {ctx.author.mention} in {ctx.channel.mention}",
                        color=discord.Color.dark_embed(),
                    )
                    embed.set_author(
                        name=ctx.author.display_name, icon_url=ctx.author.display_avatar
                    )
                    try:
                        await channel.send(embed=embed)
                    except discord.Forbidden or discord.HTTPException:
                        return print(
                            f"I could not find the channel to send the tag usage (guild: {ctx.guild.name})"
                        )

                else:
                    return print("Channel not found")

        else:
            await ctx.send(f"{no} Tag with the name `{name}` not found.")

    @tags.command(description="Delete a existing tag")        
    @app_commands.autocomplete(name=tag_name_autocompletion)
    @app_commands.describe(name = "The name of the tag")    
    async def delete(self, ctx: commands.Context, name: app_commands.Range[str, 1, 50]):
        await ctx.defer()
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the tags module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return                 
        if not await has_admin_role(ctx):
            return        
        filter = {
            'guild_id': ctx.guild.id,
            'name': name
        }        
        tagsz = await tags.find_one(filter)
        if tagsz is None:
            await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find the tag **`{name}`**.", allowed_mentions=discord.AllowedMentions.none())
            return
        await tags.delete_one(filter)        
        await ctx.send(f"{tick} Tag **`{name}`** has been deleted.")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Tags(client))        
