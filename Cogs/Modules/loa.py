import discord
import discord
from discord.ext import commands
from typing import Literal
import datetime
from datetime import timedelta
from discord import app_commands
from discord.ext import commands, tasks

from pymongo import MongoClient
from emojis import * 
import os
from dotenv import load_dotenv
from datetime import datetime
import re
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
loa_collection = db['loa']
loachannel = db['LOA Channel']
scollection = db['staffrole']
arole = db['adminrole']
LOARole = db['LOA Role']
modules = db['Modules']


class LOA(discord.ui.Modal, title='Create Leave Of Absence'):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author



    Duration = discord.ui.TextInput(
        label='Duration',
        placeholder='e.g 1w (m/h/d/w)',
    )

    reason = discord.ui.TextInput(
        label = 'Reason',
        placeholder='Reason for their loa'
    )


    async def on_submit(self, interaction: discord.Interaction):
        duration = self.Duration.value        
        reason = self.reason.value     
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        duration_value = int(duration[:-1])
        duration_unit = duration[-1]
        duration_seconds = duration_value

        if duration_unit == 'm':
            duration_seconds *= 60
        elif duration_unit == 'h':
            duration_seconds *= 3600
        elif duration_unit == 'd':
            duration_seconds *= 86400
        elif duration_unit == 'w':    
            duration_seconds *= 604800

        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)

        data = loachannel.find_one({'guild_id': interaction.guild.id})
        if data:
          channel_id = data['channel_id']
          channel = interaction.guild.get_channel(channel_id)

          if channel:
           embed = discord.Embed(title=f"LOA Created", description=f"* **User:** {self.user.mention}\n* **Start Date**: <t:{int(start_time.timestamp())}:f>\n* **End Date:** <t:{int(end_time.timestamp())}:f>\n* **Reason:** {self.reason}", color=discord.Color.dark_embed())
           embed.set_author(icon_url=self.user.display_avatar, name=self.user.display_name)
           embed.set_thumbnail(url=self.user.display_avatar)
           loadata = {'guild_id': interaction.guild.id,
           'user': self.user.id,
           'start_time': start_time,
           'end_time': end_time,
           'reason': reason,
           'active': True
                  }        
           loarole_data = LOARole.find_one({'guild_id': interaction.guild.id})
           if loarole_data:
             loarole = loarole_data['staffrole']
             if loarole:
              role = discord.utils.get(interaction.guild.roles, id=loarole)
              if role:
                try:
                 await self.user.add_roles(role)                   
                except discord.Forbidden:  
                 await interaction.response.edit_message(content=f"{no} I don't have permission to add roles.")             
                 return     


           await interaction.response.edit_message(content=f"{tick} Created LOA for **@{self.user.display_name}**", embed=embed, view=None)
           loa_collection.insert_one(loadata)                
           try:      
              await channel.send(f"<:Add:1163095623600447558> LOA was created by **@{interaction.user.display_name}**", embed=embed)  
           except discord.Forbidden:  
             await interaction.response.edit_message(content=f"{no} I don't have permission to view that channel.")             
             return                
           try:
                await self.user.send(f"<:Add:1163095623600447558> A LOA was created for you **@{interaction.guild.name}**", embed=embed)
           except discord.Forbidden:    
                pass


from permissions import has_admin_role, has_staff_role
class loamodule(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.check_loa_status.start()




    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['LOA'] == True:   
        return True



    @commands.hybrid_group()
    async def loa(self, ctx):
        pass



      
    @tasks.loop(minutes=10)
    async def check_loa_status(self):
     current_time = datetime.now()

     filter = {'end_time': {'$lte': current_time}}
    
     loa_requests = loa_collection.find(filter)

     for request in loa_requests:
        end_time = request['end_time']
        user_id = request['user']
        guild_id = request['guild_id']
        guild = self.client.get_guild(guild_id)
        user = await self.client.fetch_user(user_id)
        active = request['active']
        if guild is None:
           loa_collection.delete_one({'guild_id': guild_id, 'user': user_id, 'end_time': end_time})
           return
        if user is None:
           loa_collection.delete_one({'guild_id': guild_id, 'user': user_id, 'end_time': end_time})
           return           
        if active == True:
         if current_time >= end_time:
            if user:
                await user.send(f"{tick} Your LOA **@{guild.name}** has ended.")
                print(f"End Time: {end_time}")
                print(f"Current Time: {current_time}")
                loa_collection.update_many({'guild_id': guild_id, 'user': user_id}, {'$set': {'active': False}})
                loarole_data = LOARole.find_one({'guild_id': guild.id})
                if loarole_data:
                 loarole = loarole_data['staffrole']
                 if loarole:
                  role = discord.utils.get(guild.roles, id=loarole)
                  if role:
                   member = await self.client.fetch_user(user.id)
                   await member.remove_roles(role)       
        else:
            pass


    @loa.command(description="Manage someone leave of Absence")
    async def manage(self, ctx, user: discord.Member):
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return                 
     if not await has_admin_role(ctx):
         return   

     loa = loa_collection.find_one({"user": user.id, "guild_id": ctx.guild.id, 'active': True})
     loainactive = loa_collection.find({"user": user.id, "guild_id": ctx.guild.id, 'active': False})
     view = None

     if loa is None:
            description = []
            for request in loainactive:
                start_time = request['start_time']
                end_time = request['end_time']
                reason = request['reason']
                description.append(f"<:LOA:1164969910238203995> **Previous LOA**\n<:arrow:1166529434493386823><t:{int(start_time.timestamp())}:f> - <t:{int(end_time.timestamp())}:f> • {reason}")

            embed = discord.Embed(title="Leave Of Absense", description=f"\n".join(description), color=discord.Color.dark_embed())
            embed.set_thumbnail(url=user.display_avatar)
            embed.set_author(icon_url=user.display_avatar, name=user.display_name)
            view = LOACreate(user, ctx.guild, ctx.author)

     else:
            start_time = loa['start_time']
            end_time = loa['end_time']
            reason = loa['reason']

            embed = discord.Embed(
                title=f"Leave Of Absence",
                color=discord.Color.dark_embed(),
                description=f"<:LOA:1164969910238203995> **Active LOA**\n<:arrow:1166529434493386823>**Start Date:** <t:{int(start_time.timestamp())}:f>\n<:arrow:1166529434493386823>**End Date:** <t:{int(end_time.timestamp())}:f>\n<:arrow:1166529434493386823>**Reason:** {reason}"
            )
            embed.set_thumbnail(url=user.display_avatar)
            embed.set_author(icon_url=user.display_avatar, name=user.display_name)

            view = LOAPanel(user, ctx.guild, ctx.author)              

     await ctx.send(embed=embed, view=view)





    @loa.command(description="View all Leave Of Absence")
    async def active(self, ctx):
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            
     if not await has_admin_role(ctx):
         return             
         
     current_time = datetime.now()
     filter = {'guild_id': ctx.guild.id, 'end_time': {'$gte': current_time}, 'active': True}

     loa_requests = list(loa_collection.find(filter))

     if len(loa_requests) == 0:
        await ctx.send(f"{no} **{ctx.author.display_name}**, there aren't any active LOAs in this server.")
     else:
        embed = discord.Embed(
            title="Active LOAs",
            color=discord.Color.dark_embed()
        )
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(icon_url=ctx.guild.icon , name=ctx.guild.name)
        for request in loa_requests:
            user = await self.client.fetch_user(request['user'])
            start_time = request['start_time']
            end_time = request['end_time']
            reason = request['reason']

            embed.add_field(
                name=f"<:LOA:1164969910238203995>{user.name.capitalize()}",
                value=f"<:arrow:1166529434493386823>**Start Date:** <t:{int(start_time.timestamp())}:f>\n<:arrow:1166529434493386823>**End Date:** <t:{int(end_time.timestamp())}:f>\n<:arrow:1166529434493386823>**Reason:** {reason}",
                inline=False
            )

        await ctx.send(embed=embed)


    @loa.command(description="Request a Leave Of Absence")
    @app_commands.describe(duration="How long do you want the LOA for? (m/h/d/w)", reason="What is the reasonfor this LOA?")
    async def request(self, ctx, duration: str, reason: str):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            
        if not await has_staff_role(ctx):
         return    
        if not re.match(r'^\d+[mhdw]$', duration):
         await ctx.send(f"{no} **{ctx.author.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.")
         return
        loa_data = loa_collection.find_one({'guild_id': ctx.guild.id, 'user': ctx.author.id, 'active': True})
        if loa_data:
         await ctx.send(f"{no} **{ctx.author.display_name}**, you already have an active LOA.")
         return
        
        duration_value = int(duration[:-1])
        duration_unit = duration[-1]
        duration_seconds = duration_value

        if duration_unit == 'm':
            duration_seconds *= 60
        elif duration_unit == 'h':
            duration_seconds *= 3600
        elif duration_unit == 'd':
            duration_seconds *= 86400
        elif duration_unit == 'w':    
            duration_seconds *= 604800

        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        embed = discord.Embed(title=f"LOA Request - Pending", description=f"* **User:** {ctx.author.mention}\n* **Start Date**: <t:{int(start_time.timestamp())}:f>\n* **End Date:** <t:{int(end_time.timestamp())}:f>\n* **Reason:** {reason}", color=discord.Color.dark_embed())
        embed.set_author(icon_url=ctx.author.display_avatar, name=ctx.author.display_name)
        embed.set_thumbnail(url=ctx.author.display_avatar)
        data = loachannel.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:

  
          view = Confirm()        
          try:
           msg = await channel.send(embed=embed, view=view)
           loadata = {'guild_id': ctx.guild.id,
        'user': ctx.author.id,
        'start_time': start_time,
        'end_time': end_time,
        'reason': reason,
        'messageid': msg.id,
        'active': False}   
           loa_collection.insert_one(loadata)
           await ctx.send(f"{tick} LOA Request sent", ephemeral=True)   
           print(f"LOA Request @{ctx.guild.name} pending")       
          except discord.Forbidden:
                await ctx.send(f"{no} Please contact server admins I can't see the LOA Channel.")            

      
         else:
            await ctx.send(f"{no} {ctx.author.display_name}, I don't have permission to view this channel.")
        else:
          await ctx.send(f"{no} **{ctx.author.display_name}**, the channel is not setup please run `/config`")

class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


    async def has_admin_role(self, interaction):
     filter = {
        'guild_id': interaction.guild.id
    }
     staff_data = arole.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        staff_role = discord.utils.get(interaction.guild.roles, id=staff_role_ids)
        if not isinstance(staff_role_ids, list):
          staff_role_ids = [staff_role_ids]     
        if any(role.id in staff_role_ids for role in interaction.user.roles):
            return True

     return False


    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green, custom_id='persistent_view:confirm', emoji=f"{tick}")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):   
        if not await self.has_admin_role(interaction):
            await interaction.response.edit_message(content=f"{no} **{interaction.user.display_name}**, you don't have permission to accept this LOA.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`", view=None)
            return                
        loa_data = loa_collection.find_one({'messageid': interaction.message.id}) 
        if loa_data:
         self.user = await interaction.guild.fetch_member(loa_data['user'])
        user = self.user
        try:
         await self.user.send(f"{tick} **{self.user.display_name}**, your LOA **@{interaction.guild.name}** has been accepted.")
        except discord.Forbidden:
                pass          
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_green()
        embed.title = f"<:Tick_1:1178749612929069096> LOA Request - Accepted"
        embed.set_footer(text=f"Accepted by {interaction.user.display_name}", icon_url=interaction.user.display_avatar)
        loa_collection.update_one({'messageid': interaction.message.id}, {'$set': {'active': True}}) 
        await interaction.response.edit_message(embed=embed, view=None)
        print(f"LOA Request @{interaction.guild.name} accepted")
        loarole_data = LOARole.find_one({'guild_id': interaction.guild.id})
        if loarole_data:
         loarole = loarole_data['staffrole']
         if loarole:
          role = discord.utils.get(interaction.guild.roles, id=loarole)
          if role:
            await user.add_roles(role)



    @discord.ui.button(label='Deny', style=discord.ButtonStyle.red, custom_id='persistent_view:cancel', emoji=f"{no}")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.has_admin_role(interaction):
            await interaction.response.edit_message(content=f"{no} **{interaction.user.display_name}**, you don't have permission to deny this LOA.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`", view=None)
            return           
        loa_data = loa_collection.find_one({'messageid': interaction.message.id}) 
        if loa_data:
         self.user = await interaction.guild.fetch_member(loa_data['user'])
        try:
         await self.user.send(f"{no} **{self.user.display_name}**, your LOA **@{interaction.guild.name}** has been denied.")        
        except discord.Forbidden:
                pass 
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_red()
        embed.title = f"<:crossX:1140623638207397939> LOA Request - Denied"
        embed.set_footer(text=f"Denied by {interaction.user.display_name}", icon_url=interaction.user.display_avatar)
        loa_collection.delete_one({'messageid': interaction.message.id})
        await interaction.response.edit_message(embed=embed, view=None)    
        print(f"LOA Request @{interaction.guild.name} denied") 


   

class LOAPanel(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author


    @discord.ui.button(label='Void LOA', style=discord.ButtonStyle.grey, custom_id='persistent_view:cancel', emoji="<:Exterminate:1164970632262451231>")
    async def End(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.user
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        loa = loa_collection.find_one({"user": self.user.id, "guild_id": interaction.guild.id, 'active': True})
        loarole_data = LOARole.find_one({'guild_id': interaction.guild.id})
        if loarole_data:
         loarole = loarole_data['staffrole']
         if loarole:
          role = discord.utils.get(interaction.guild.roles, id=loarole)
          if role:
            try:
             await user.remove_roles(role)         
            except discord.Forbidden: 
                await interaction.response.edit_message(content=f"{no} I don't have permission to remove roles.")
                return
          
            

        loa_collection.update_many({'guild_id': interaction.guild.id, 'user': user.id}, {'$set': {'active': False}})

        await interaction.response.edit_message(embed=None, content=f"{tick} Succesfully ended **@{user.display_name}'s** LOA", view=None)
        try:    
         await user.send(f"<:bin:1160543529542635520> Your LOA **@{self.guild.name}** has been voided.")  
        except discord.Forbidden:
                pass    
        
class LOACreate(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(label='Create Leave Of Absence', style=discord.ButtonStyle.grey, custom_id='persistent_view:cancel', emoji="<:Add:1163095623600447558>")
    async def CreateLOA(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.send_modal(LOA(self.user, self.guild, self.author))

async def setup(client: commands.Bot) -> None:
    await client.add_cog(loamodule(client))             