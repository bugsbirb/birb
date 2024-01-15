import discord
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from emojis import * 
import typing
import Paginator
MONGO_URL = os.getenv('MONGO_URL')
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo['astro']
connectionroles = db['connectionroles']
modules = db['Modules']




            



class ConnectionRoles(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client


    @commands.hybrid_group()
    async def connectionrole(self, ctx):
        pass

    async def modulecheck(self, ctx): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    

     if modulesdata is None:
        return False
     elif modulesdata.get('Connection', False) == True: 
        return True
     else:   
        return False

    async def tag_name_autocompletion(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        filter = {
            'guild_id': interaction.guild_id 
        }

        tag_names = connectionroles.distinct("name", filter)

        filtered_names = [name for name in tag_names if current.lower() in name.lower()]

        choices = [app_commands.Choice(name=name, value=name) for name in filtered_names]

        return choices

    @connectionrole.command(name="add", description="Add a connection role to your server")
    @commands.has_guild_permissions(manage_roles=True)
    @app_commands.describe(parent="Once the role is given it will give the child role", child="Child is the role given after the parent role is given")
    async def connectionrole_add(self, ctx, parent: discord.Role, child: discord.Role):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            
        if parent == child:
           await ctx.send(f"{no} **{ctx.author.display_name}**, The parent and child roles cannot be the same.")
           return
        
        
        await connectionroles.insert_one({"guild": ctx.guild.id, "parent": parent.id, "child": child.id, "name": parent.name})
        await ctx.send(f"{tick} **{ctx.author.display_name}**, The connection role has been added.")


    @connectionrole.command(name="remove", description="Remove a connection role from your server")
    @app_commands.autocomplete(name=tag_name_autocompletion)
    @commands.has_guild_permissions(manage_roles=True)
    @app_commands.describe(name="The name of the connection role")
    async def connectionrole_remove(self, ctx, name):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            
        roleresult = await connectionroles.find_one({"guild": ctx.guild.id, "name": name})
        if roleresult is None:
            await ctx.send(f"{no} **{ctx.author.display_name}**, The connection role does not exist.")
            return
        
        await connectionroles.delete_many({
            "guild": ctx.guild.id,
            "name": name
        })
        await ctx.send(f"{tick} **{ctx.author.display_name}**, The connection role has been removed.")

    @connectionrole.command(name="list", description="List all connection roles in your server")
    @commands.has_guild_permissions(manage_roles=True)
    async def connectionrole_list(self, ctx):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return

        roleresult = await connectionroles.find({"guild": ctx.guild.id}).to_list(length=100000)
        if len(roleresult) == 0:
            await ctx.send(f"{no} **{ctx.author.display_name}**, There are no connection roles.")
            return

        MAX_FIELDS_PER_PAGE = 9
        embeds = []
        current_embed = None
        MAX_FIELDS_PER_PAGE = 9
        embeds = []
        current_embed = None

        for idx, role in enumerate(roleresult):
            if idx % MAX_FIELDS_PER_PAGE == 0:
                if current_embed:
                    embeds.append(current_embed)

                current_embed = discord.Embed(title="Connection Roles", color=discord.Color.dark_embed())
                current_embed.set_thumbnail(url=ctx.guild.icon)
                current_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)

            current_embed.add_field(
                name=f"{role['name']}",
                value=f"**Parent:** <@&{role['parent']}>\n**Child:** <@&{role['child']}>",
                inline=False
            )

        if current_embed:
            embeds.append(current_embed)

        PreviousButton = discord.ui.Button(label="<")
        NextButton = discord.ui.Button(label=">")
        FirstPageButton = discord.ui.Button(label="<<")
        LastPageButton = discord.ui.Button(label=">>")
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

        


    
    @connectionrole_add.error
    @connectionrole_remove.error
    @connectionrole_list.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to configure connection roles.\n<:Arrow:1115743130461933599>**Required:** ``Manage Roles``")              

async def setup(client: commands.Bot) -> None:
    await client.add_cog(ConnectionRoles(client))     
