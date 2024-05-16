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
partnerships = db['Partnerships']
partnershipsch = db['Partnerships Channel']
modules = db['Modules']
from permissions import has_admin_role



class Partnerships(commands.Cog):
    def __init__(self, client):
        self.client = client




    async def servers_autocomplete(
        ctx: commands.Context,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        filter = {
            'guild_id': interaction.guild_id 
        }

        tag_names = await partnerships.distinct("server", filter)

        filtered_names = [name for name in tag_names if current.lower() in name.lower()]

        choices = [app_commands.Choice(name=name, value=name) for name in filtered_names]

        return choices

    @commands.hybrid_group()
    async def partnership(self, ctx: commands.Context):
        pass

    @staticmethod
    async def modulecheck(ctx: commands.Context): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Partnerships'] is True:   
        return True

    @partnership.command(description="Log a partnership affiliation")
    @app_commands.describe(respresentive="The partnership respresentive of the server", server="The name of the server", invite="The invite link to the server")
    async def log(self, ctx: commands.Context, respresentive: discord.User, server:  discord.ext.commands.Range[str, 1, 400],  invite: discord.ext.commands.Range[str, 1, 100]):
        await ctx.defer()
        if respresentive is None:
          await ctx.send(f"{no} **{ctx.author.display_name}**, this user can not be found.", allowed_mentions=discord.AllowedMentions.none())
          return
        result = await partnerships.find_one({'guild_id': ctx.guild.id, 'server': server})
        if result:
            await ctx.send(f"{no} **{ctx.author.display_name}**, that server is already in the partnerships database.", allowed_mentions=discord.AllowedMentions.none())
            return
       
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the partnership module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return            

        if not await has_admin_role(ctx):
         return      
        try:
         invited = await self.client.fetch_invite(url=invite)
        except discord.NotFound:
          await ctx.send(f"{no} **{ctx.author.display_name}**, that invite is invalid.", allowed_mentions=discord.AllowedMentions.none())
          return
        
        if invited and invited.guild is None:
          await ctx.send(f"{no} **{ctx.author.display_name}**, that invite is invalid.", allowed_mentions=discord.AllowedMentions.none())
          return          


        if invited.expires_at is not None:
          await ctx.send(f"{no} **{ctx.author.display_name}**, the invite has to be unlimited.", allowed_mentions=discord.AllowedMentions.none)
          return

         
        data = await partnershipsch.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data.get('channel_id', None)
         if channel_id is None:
           await ctx.send(f"{no} **{ctx.author.display_name}**, the channel is not setup please run `/config`", allowed_mentions=discord.AllowedMentions.none())
           return
         channel = self.client.get_channel(channel_id)

         if channel:
          
          partnershipdata = {
            'guild_id': ctx.guild.id,
            'owner': respresentive.id,
            'admin': ctx.author.id,
            'invite': invite,
            'server': server,
            'since': discord.utils.utcnow()
        }

          guild = invited.guild
          guild_name = server
        
          description = f"<:crown:1226668264260894832> **Representive:** <@{respresentive.id}>\n<:ID:1226671706022740058> **Guild ID:** {guild.id}\n<:Member:1226674150463111299> **Logged By:** <@{ctx.author.id}>\n<:link:1226672596284866631> **Invite:** {invite}" 
          embed = discord.Embed(title="<:Partner:1235001453861535825> Partnership Logged", description=description, color=discord.Color.dark_embed())
          embed.set_author(name=guild_name, icon_url=guild.icon)
          embed.set_thumbnail(url=guild.icon)
          try:
           await channel.send(embed=embed)
           await ctx.send(f"{tick} {ctx.author.display_name}, I've succesfully logged the partnership.", allowed_mentions=discord.AllowedMentions.none())  
           await partnerships.insert_one(partnershipdata)
          except discord.Forbidden: 
            await ctx.send(f"{no} {ctx.author.display_name}, I don't have permission to view that channel.", allowed_mentions=discord.AllowedMentions.none())
            return
         else:
           await ctx.send(f"{no} **{ctx.author.display_name}**, the channel can not be found please resetup the channel in `/config`", allowed_mentions=discord.AllowedMentions.none())   
           return                        
        else:  
         await ctx.send(f"{no} **{ctx.author.display_name}**, the channel is not setup please run `/config`", allowed_mentions=discord.AllowedMentions.none())
         
    @partnership.command(description="Close an ongoing partnership")    
    @app_commands.autocomplete(server=servers_autocomplete)    
    async def terminate(self, ctx: commands.Context, server, *,reason:  discord.ext.commands.Range[str, 1, 2000]):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the partnership module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return            

        if not await has_admin_role(ctx):
         return              


        result = await partnerships.find_one({'guild_id': ctx.guild.id, 'server': server})
        if result is None:   
            await ctx.send(f"{no} **{ctx.author.display_name}**, I could not find that partnership.", allowed_mentions=discord.AllowedMentions.none())
            return
        server = result.get('server')
        ownerid = result.get('owner')
        adminid = result.get('admin')
        inviteurl = result.get('invite')
        guildid = result.get('guild_id')   
        since = result.get('since', None)
         
        data = await partnershipsch.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data.get('channel_id', None)
         if channel_id is None:
           channel = None
         else:  
          channel = self.client.get_channel(channel_id)

         if channel:
          alert = ""
          await ctx.send(f"{tick} {ctx.author.display_name}, I've succesfully terminated this partnership.")
          try:
           invite = await self.client.fetch_invite(url=invite)
           guild = invite.guild
           guildicon = guild.icon
          except discord.NotFound:
           invite = f"Expired ||{inviteurl}||"
           guild = None
           guildicon = None
           alert = ""


          description = f"{alert}\n<:crown:1226668264260894832> **Representive:** <@{ownerid}>\n<:ID:1226671706022740058> **Guild ID:** {guildid}\n<:Member:1226674150463111299> **Logged By:** <@{adminid}>\n<:link:1226672596284866631> **Invite:** {invite}\n<:messageforward1:1230919023361921165> **Reason:** {reason}"
          embed = discord.Embed(title="<:Partner:1235001453861535825> Partnership Terminated", description=description, color=discord.Color.dark_embed(), timestamp=since)
          embed.set_author(name=server, icon_url=guildicon)
          if guild:
           embed.set_thumbnail(url=guildicon)
          else:
            embed.set_footer(text="The invite has expired, the guild information is limited.")
          try:
           await channel.send(embed=embed)
          except discord.Forbidden: 
            await ctx.send(f"{no} I don't have permission to view that channel.")     
            return      
          await partnerships.delete_one({'guild_id': ctx.guild.id, 'server': server})
         else:
           await ctx.send(f"{no} **{ctx.author.display_name}**, the channel can not be found please resetup the channel in `/config`", allowed_mentions=discord.AllowedMentions.none())   
           return                           
        else:  
         await ctx.send(f"{no} **{ctx.author.display_name}**, the channel is not setup please run `/config`", allowed_mentions=discord.AllowedMentions.none())        
         return
        
    @partnership.command(description="Retrieve detailed information about a specific partnership")
    @app_commands.autocomplete(server=servers_autocomplete)
    async def view(self, ctx: commands.Context, *,server: str):
      await ctx.defer()
      if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the partnership module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return
      if not await has_admin_role(ctx):
         return              
      result = await partnerships.find_one({'guild_id': ctx.guild.id, 'server': server})
      if result is None:
        await ctx.send(f"{no} {ctx.author.display_name}, this isn't a valid partnership.", allowed_mentions=discord.AllowedMentions.none())
        return
      server = result.get('server')
      ownerid = result.get('owner')
      adminid = result.get('admin')
      inviteurl = result.get('invite')
      guildid = result.get('guild_id')
      since = result.get('since', None)
      
      alert = ""
      try:
            invite = await self.client.fetch_invite(url=invite)
            guild = invite.guild  
            guildicon = guild.icon
      except discord.NotFound:
            invite = f"Expired ||{inviteurl}||"
            guild = None
            guildicon = None
            alert = "## <:bell:1191903691750514708> Invite Expired\n\n"
      
    
      description = f"{alert}\n<:crown:1226668264260894832> **Representive:** <@{ownerid}>\n<:ID:1226671706022740058> **Guild ID:** {guildid}\n<:Member:1226674150463111299> **Logged By:** <@{adminid}>\n<:link:1226672596284866631> **Invite:** {invite}"
      embed = discord.Embed(title="", description=description, color=discord.Color.dark_embed(), timestamp=since)
      embed.set_author(name=server, icon_url=guildicon)
      embed.set_thumbnail(url=guildicon)
      if guild is None:
        embed.set_footer(text="The invite has expired, the guild information is limited.")
      await ctx.send(embed=embed)

     
        

      
      
     


    @partnership.command(description="View all Partnerships in this server.")
    async def all(self, ctx: commands.Context):
        await ctx.defer()
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the partnership module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return            

        if not await has_admin_role(ctx):
         return              
        result = partnerships.find({'guild_id': ctx.guild.id})
        if not result:
            await ctx.send(f"{no} **{ctx.author.display_name}**, there are no active partnerships on this server.", allowed_mentions=discord.AllowedMentions.none())
            return

        embeds = []

        async for partnership in result:
         server = partnership.get('server')
         ownerid = partnership.get('owner')
         adminid = partnership.get('admin')
         inviteurl = partnership.get('invite')
         guildid = partnership.get('guild_id')
         since = partnership.get('since', None)
         alert = ""

         try:
            invite = await self.client.fetch_invite(url=inviteurl)
            guild = invite.guild  
            guildicon = guild.icon
         except discord.NotFound:
            invite = f"Expired ||{inviteurl}||"
            guild = None
            alert = "## <:bell:1191903691750514708> Invite Expired\n"
            guildicon = None




         guild_name = server
         description = f"{alert}\n<:crown:1226668264260894832> **Representive:** <@{ownerid}>\n<:ID:1226671706022740058> **Guild ID:** {guildid}\n<:Member:1226674150463111299> **Logged By:** <@{adminid}>\n<:link:1226672596284866631> **Invite:** {invite}"
         embed = discord.Embed(
            title="<:Partner:1235001453861535825> Partnership Logged",
            description=description,
            color=discord.Color.dark_embed(), 
            timestamp=since
        )
         embed.set_author(name=guild_name, icon_url=guildicon)
         embed.set_thumbnail(url=guildicon)
         embeds.append(embed)
         if guild is None:
            embed.set_footer(text="The invite has expired, the guild information is limited.")
           

        PreviousButton = discord.ui.Button(emoji="<:chevronleft:1220806425140531321>")
        NextButton = discord.ui.Button(emoji="<:chevronright:1220806430010118175>")
        FirstPageButton = discord.ui.Button(emoji="<:chevronsleft:1220806428726661130>")
        LastPageButton = discord.ui.Button(emoji="<:chevronsright:1220806426583371866>")
        InitialPage = 0
        timeout = 92069

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