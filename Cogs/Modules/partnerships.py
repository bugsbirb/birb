import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal
from typing import Optional
from pymongo import MongoClient
from emojis import *
import typing
import os
from dotenv import load_dotenv
import Paginator
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
partnerships = db['Partnerships']
partnershipsch = db['Partnerships Channel']
modules = db['Modules']
from permissions import has_admin_role, has_staff_role



class Partnerships(commands.Cog):
    def __init__(self, client):
        self.client = client



    async def servers_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        filter = {
            'guild_id': interaction.guild_id 
        }

        tag_names = partnerships.distinct("server", filter)

        filtered_names = [name for name in tag_names if current.lower() in name.lower()]

        choices = [app_commands.Choice(name=name, value=name) for name in filtered_names]

        return choices

    @commands.hybrid_group()
    async def partnership(self, ctx):
        pass

    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Partnerships'] == True:   
        return True

    @partnership.command(description="Log a partnership")
    async def log(self, ctx, owner: discord.Member, server: str, invite: str):

        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            

        if not await has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`")
         return      
        try:
         invited = await self.client.fetch_invite(url=invite)
        except discord.NotFound:
          await ctx.send(f"{no} {ctx.author.mention}, that invite is invalid.")
          return

        data = partnershipsch.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
          
          partnershipdata = {
            'guild_id': ctx.guild.id,
            'owner': owner.id,
            'admin': ctx.author.id,
            'invite': invite,
            'server': server
        }

          guild = invited.guild
          guild_name = server
          guild_id = "Unknown" if guild is None or guild.id is None else guild.id
          icon_url = "https://cdn.discordapp.com/attachments/1104358043598200882/1185555135544426618/error-404-page-found-vector-concept-icon-internet-website-down-simple-flat-design_570429-4168.png?ex=65900942&is=657d9442&hm=fc312fddae78ea4347315f4af2893893b684bb9b97686c2859272aa16c81a5b0&h=256&w=256" if guild is None or guild.icon is None else guild.icon
          invite = "Unknown" if guild is None or invited.url is None else invited.url
          embed = discord.Embed(title=f"<:Partner:1162135285031772300> Partnership Logged", description=f"\n**Logged By:** {ctx.author.mention}\n**Owner:** {owner.mention}\n**Server:** {guild_name}\n**Server ID:** {guild_id}\n**Invite:** {invite}", color=discord.Color.dark_embed())
          embed.set_author(name=guild_name, icon_url=icon_url)
          embed.set_thumbnail(url=guild.icon.url)
          try:
           await channel.send(embed=embed)
           await ctx.send(f"{tick} **Partnership** logged.")  
           partnerships.insert_one(partnershipdata)
          except discord.Forbidden: 
            await ctx.send(f"{no} I don't have permission to view that channel.")
        else:  
         await ctx.send(f"{no} **{ctx.author.display_name}**, the channel is not setup please run `/config`")

    @partnership.command(description="Terminate a server partnership")     
    @app_commands.autocomplete(server=servers_autocomplete)    
    async def terminate(self, ctx, server, reason: str):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            

        if not await has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`")
         return              


        partnership_data = partnerships.find_one({'guild_id': ctx.guild.id, 'server': server})
        if partnership_data is None:   
            await ctx.send(f"{no} **{ctx.author.display_name}**, I could not find that partnership.")
            return
        if partnership_data:
            server = partnership_data['server']
            ownerid = partnership_data['owner']
            adminid = partnership_data['admin']
            invite = partnership_data['invite']            
            owner = await self.client.fetch_user(ownerid)
            admin = await self.client.fetch_user(adminid)
        data = partnershipsch.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
          await ctx.send(f"{tick} **Partnership** terminiated.")
          invite = await self.client.fetch_invite(url=invite)
          guild = invite.guild
          guild_name = server if guild is None or guild.name is None else guild.name
          guild_id = "Unknown" if guild is None or guild.id is None else guild.id
          icon_url = "https://cdn.discordapp.com/attachments/1104358043598200882/1185555135544426618/error-404-page-found-vector-concept-icon-internet-website-down-simple-flat-design_570429-4168.png?ex=65900942&is=657d9442&hm=fc312fddae78ea4347315f4af2893893b684bb9b97686c2859272aa16c81a5b0&h=256&w=256" if guild is None or guild.icon is None else guild.icon
          invite = "Unknown" if guild is None or invite.url is None else invite.url
          embed = discord.Embed(title=f"<:Partner:1162135285031772300> Partnership Terminated", description=f"\n**Logged By:** {admin.mention}\n**Owner:** {owner.mention}\n**Server:** {guild_name}\n**Server ID:** {guild_id}\n**Invite:** {invite}\n**Reason:** {reason}", color=discord.Color.dark_embed())
          embed.set_author(name=guild_name, icon_url=icon_url)
          embed.set_thumbnail(url=guild.icon.url)
          try:
           await channel.send(embed=embed)
          except discord.Forbidden: 
            await ctx.send(f"{no} I don't have permission to view that channel.")     
            return      
          partnerships.delete_one({'guild_id': ctx.guild.id, 'server': server})
        else:  
         await ctx.send(f"{no} **{ctx.author.display_name}**, the channel is not setup please run `/config`")        

    @partnership.command(description="View all Partnerships in this server.")
    async def all(self, ctx):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            

        if not await has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`")
         return              
        partnership_data = partnerships.find({'guild_id': ctx.guild.id})
        if not partnership_data:
            await ctx.send(f"{no} **{ctx.author.display_name}**, there are no active partnerships on this server.")
            return

        embeds = []

        for partnership in partnership_data:
         server = partnership['server']
         owner_id = partnership['owner']
         invite = partnership['invite']
         admin_id = partnership['admin']
         admin = await self.client.fetch_user(admin_id)
         owner = await self.client.fetch_user(owner_id)

         try:
            invite = await self.client.fetch_invite(url=invite)
            guild = invite.guild  
         except discord.NotFound:
            invite = None
            guild = None


         guild_name = server
         guild_id = "Unknown" if guild is None or guild.id is None else guild.id
         icon_url = "https://cdn.discordapp.com/attachments/1104358043598200882/1185555135544426618/error-404-page-found-vector-concept-icon-internet-website-down-simple-flat-design_570429-4168.png?ex=65900942&is=657d9442&hm=fc312fddae78ea4347315f4af2893893b684bb9b97686c2859272aa16c81a5b0&h=256&w=256" if guild is None or guild.icon is None else guild.icon
         admin_mention = "Unknown" if admin is None or admin.mention is None else admin.mention
         owner_mention = "Unknown" if owner is None or owner.mention is None else owner.mention
         embed = discord.Embed(
            title=f"<:Partner:1162135285031772300> Partnership Logged",
            description=f"\n**Logged By:** {admin_mention}\n"
                        f"**Owner:** {owner_mention}\n"
                        f"**Server:** {guild_name}\n"
                        f"**Server ID:** {guild_id}\n"
                        f"**Invite:** {invite if invite else 'Unknown'}",
            color=discord.Color.dark_embed()
        )
         embed.set_author(name=guild_name, icon_url=icon_url)
         embed.set_thumbnail(url=icon_url)
         embeds.append(embed)



        if not embeds:
            await ctx.send(f"No active partnerships on this server.")
            return

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




async def setup(client: commands.Bot) -> None:
    await client.add_cog(Partnerships(client))      