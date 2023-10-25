import sqlite3
import discord
from discord.ext import commands
from typing import Literal
import random
import string
import asyncio
from typing import Union, Optional
import sqlite3
from discord.ext import commands
import datetime
from discord import app_commands
import Paginator
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from emojis import *
from cogs.infractions import *
from datetime import timedelta

MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
db = client['astro']
collection = db['infractions']
scollection = db['staffrole']
arole = db['adminrole']
infchannel = db['infraction channel']
appealable = db['Appeal Toggle']
appealschannel = db['Appeals Channel']
loa_collection = db['loa']
loachannel = db['LOA Channel']
scollection = db['staffrole']
arole = db['adminrole']
promochannel = db['promo channel']
LOARole = db['LOA Role']

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

        start_time = datetime.datetime.now()
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
           'reason': reason
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
                 await interaction.response.edit_message(content=f"{no} I don't have permission to add roles.", view=Return(self.user, self.guild, self.author), embed=None)             
                 return     

           await interaction.response.edit_message(content=f"{tick} Created LOA for **@{self.user.display_name}**", view=Return(self.user, self.guild, self.author), embed=None)
           loa_collection.insert_one(loadata)                
           try:      
              await channel.send(f"<:Add:1163095623600447558> LOA was created by **@{interaction.user.display_name}**", embed=embed)  
           except discord.Forbidden:  
             await interaction.response.edit_message(content=f"{no} I don't have permission to view that channel.", view=Return(self.user, self.guild, self.author), embed=None)             
             return                
           try:
                await self.user.send(f"<:Add:1163095623600447558> A LOA was created for you **@{interaction.guild.name}**", embed=embed)
           except discord.Forbidden:    
                pass


class DemotedToRole(discord.ui.RoleSelect):
    def __init__(self, user, guild, author):
        super().__init__(placeholder='Removed Rank')
        self.user = user
        self.guild = guild
        self.author = author        

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        selected_role_id = self.values[0].id 
        role = discord.utils.get(interaction.guild.roles, id=selected_role_id)
        
        if role is None:
            embed = discord.Embed(description=f"Role with ID {selected_role_id} not found.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if interaction.user.top_role <= role:
            await interaction.response.edit_message(
                content=f"{no} **{interaction.user.display_name}**, you are below the role `{role.name}` and do not have the authority to promote this member.",
                view=Return(self.user, self.guild, self.author),
                embed=None
            )
            return

        await interaction.response.send_modal(DemotionReason(self.user, self.guild, self.author, selected_role_id)) 


class DemotionReason(discord.ui.Modal, title='Reason'):
    def __init__(self, user, guild, author, role):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author
        self.role = role



    Reason = discord.ui.TextInput(
        label='reason?',
        placeholder='Demotion reason?',
    )


    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          

        reason = self.Reason.value
        role = discord.utils.get(interaction.guild.roles, id=self.role)


        random_string = ''.join(random.choices(string.digits, k=8))
        reason = self.Reason.value 
        embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {self.user.mention}\n* **Action:** Demotion\n* **Reason:** {reason}", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.set_author(name=f"Signed, {self.author.display_name}", icon_url=self.author.display_avatar)
        embed.set_footer(text=f"Infraction ID | {random_string}")
        infract_data = {
            'management': self.author.id,
            'staff': self.user.id,
            'action': "Demotion",
            'reason': reason,
            'notes': "`N/A`",
            'random_string': random_string,
            'guild_id': interaction.guild.id
        }

        guild_id = interaction.guild.id
        data = infchannel.find_one({'guild_id': guild_id})
        appeal_data = appealable.find_one({'guild_id': str(interaction.guild.id)})

        if appeal_data is not None:
         appeal_enabled = appeal_data.get('enabled', False)
        else:
          appeal_enabled = False
        if data:
         channel_id = data['channel_id']
         channel = interaction.guild.get_channel(channel_id)

         if channel:
            view = AppealButtonView(interaction.guild.id, random_string, "Demotion", self.Reason) if appeal_enabled else None
            try:
                 await self.user.remove_roles(role)
            except discord.Forbidden:
                 await interaction.response.edit_message(content=f"<:Allonswarning:1123286604849631355> **{interaction.user.display_name}**, I don't have permission to remove roles.",                         embed=None,
                        view=Return(self.user, self.guild, self.author))
                 return               
            
            try:
             await channel.send(f"{self.user.mention}", embed=embed)
            except discord.Forbidden: 
             await interaction.response.edit_message(content=f"{no} I don't have permission to view that channel.", view=Return(self.user, self.guild, self.author), embed=None)             
             return
            await interaction.response.edit_message(content=f"{tick} **{self.author.display_name}**, I've demoted **@{self.user.display_name}**", embed=None, view=Return(self.user, self.guild, self.author))
            collection.insert_one(infract_data)
            try:
                await self.user.send(f"<:SmallArrow:1140288951861649418> From **{interaction.guild.name}**", embed=embed, view=view)
            except discord.Forbidden:
                pass
        else:
          await interaction.response.edit_message(content=f"{Warning} **{self.author.display_name}**, the channel is not setup please run `/config`", embed=None, view=Return(self.user, self.guild, self.author))
















class PromotionRole(discord.ui.RoleSelect):
    def __init__(self, user, guild, author):
        super().__init__(placeholder='Updated Rank')
        self.user = user
        self.guild = guild
        self.author = author        

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        selected_role_id = self.values[0].id 
        role = discord.utils.get(interaction.guild.roles, id=selected_role_id)
        
        if role is None:
            embed = discord.Embed(description=f"Role with ID {selected_role_id} not found.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if interaction.user.top_role <= role:
            await interaction.response.edit_message(
                content=f"{no} **{interaction.user.display_name}**, you are below the role `{role.name}` and do not have the authority to promote this member.",
                view=Return(self.user, self.guild, self.author),
                embed=None
            )
            return

        await interaction.response.send_modal(PromotionReason(self.user, self.guild, self.author, selected_role_id)) 


class PromotionReason(discord.ui.Modal, title='Reason'):
    def __init__(self, user, guild, author, role):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author
        self.role = role



    Reason = discord.ui.TextInput(
        label='reason?',
        placeholder='Promotion reason?',
    )


    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          

        reason = self.Reason.value
        role = discord.utils.get(interaction.guild.roles, id=self.role)
        user_mention = self.user.mention if self.user is not None else "Unknown User"

        embed = discord.Embed(
            title="Staff Promotion",
            color=0x2b2d31,
            description=f"* **User:** {user_mention}\n* **Updated Rank:** {role.mention}\n* **Reason:** {reason}"
        )
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.set_author(name=f"Signed, {self.author.display_name}", icon_url=self.author.display_avatar.url)

        guild_id = interaction.guild.id
        data = promochannel.find_one({'guild_id': guild_id})

        if data:
            channel_id = data['channel_id']
            channel = interaction.guild.get_channel(channel_id)

            if channel:


                try:
                 await self.user.add_roles(role)
                except discord.Forbidden:
                 await interaction.response.edit_message(content=f"<:Allonswarning:1123286604849631355> **{interaction.user.display_name}**, I don't have permission to add roles.",                         embed=None,
                        view=Return(self.user, self.guild, self.author))
                 return       

                try:
                    await channel.send(f"{self.user.mention}", embed=embed)
                except discord.Forbidden:
                    await interaction.response.edit_message(
                        content=f"{no} I don't have permission to view that channel.",
                        embed=None,
                        view=Return(self.user, self.guild, self.author)
                    )
                    return   

                await interaction.response.edit_message(
                    content=f"{tick} **{self.author.display_name}**, I've promoted **@{self.user.display_name}**",
                    embed=None,
                    view=Return(self.user, self.guild, self.author)
                )





        else:
            await interaction.response.edit_message(
                content=f"{Warning} **{interaction.user.display_name}**, the channel is not set up. Please run `/config`",
                embed=None,
                view=None
            )

class Reason(discord.ui.Modal, title='Reason'):
    def __init__(self, user, guild, author, option):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author
        self.option = option



    Reason = discord.ui.TextInput(
        label='reason?',
        placeholder='Infraction reason?',
    )


    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          
        random_string = ''.join(random.choices(string.digits, k=8))
        reason = self.Reason.value 
        embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {self.user.mention}\n* **Action:** {self.option}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.set_author(name=f"Signed, {self.author.display_name}", icon_url=self.author.display_avatar)
        embed.set_footer(text=f"Infraction ID | {random_string}")
        infract_data = {
            'management': self.author.id,
            'staff': self.user.id,
            'action': self.option,
            'reason': reason,
            'notes': "`N/A`",
            'random_string': random_string,
            'guild_id': interaction.guild.id
        }

        guild_id = interaction.guild.id
        data = infchannel.find_one({'guild_id': guild_id})
        appeal_data = appealable.find_one({'guild_id': str(interaction.guild.id)})

        if appeal_data is not None:
         appeal_enabled = appeal_data.get('enabled', False)
        else:
          appeal_enabled = False
        if data:
         channel_id = data['channel_id']
         channel = interaction.guild.get_channel(channel_id)

         if channel:
            view = AppealButtonView(interaction.guild.id, random_string, self.option, self.Reason) if appeal_enabled else None
            
            
            try:
             await channel.send(f"{self.user.mention}", embed=embed)
            except discord.Forbidden: 
             await interaction.response.edit_message(content=f"{no} I don't have permission to view that channel.", view=Return(self.user, self.guild, self.author), embed=None)             
             return
            await interaction.response.edit_message(content=f"{tick} **{self.author.display_name}**, I've infracted **@{self.user.display_name}**", embed=None, view=Return(self.user, self.guild, self.author))
            collection.insert_one(infract_data)
            try:
                await self.user.send(f"<:SmallArrow:1140288951861649418> From **{interaction.guild.name}**", embed=embed, view=view)
            except discord.Forbidden:
                pass
        else:
          await interaction.response.edit_message(content=f"{Warning} **{self.author.display_name}**, the channel is not setup please run `/config`", embed=None, view=Return(self.user, self.guild, self.author))

class InfractionOption(discord.ui.Select):
    def __init__(self, user, guild, author):
        self.user = user
        self.guild = guild
        self.author = author        
        options = [
            discord.SelectOption(label='Activity Notice'),
            discord.SelectOption(label='Verbal Warning'),                
            discord.SelectOption(label='Warning'),            
            discord.SelectOption(label='Strike'),                
            discord.SelectOption(label='Demotion'), 
            discord.SelectOption(label='Termination'),            

        
            
        ]
        super().__init__(placeholder='Action', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        option = self.values[0]
        if option == 'Demotion':

         view = DemotionRoleView(self.user, self.guild, self.author)
         await interaction.response.edit_message(view=view)

        else:
         await interaction.response.send_modal(Reason(self.user, self.guild, self.author, option))

class InfractionOptionView(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author        
        self.add_item(InfractionOption(self.user, self.guild, self.author))

class PromotionRoleView(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author        
        self.add_item(PromotionRole(self.user, self.guild, self.author))
class LOACreation(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author        
        self.add_item(LOA(self.user, self.guild, self.author))

class DemotionRoleView(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author        
        self.add_item(DemotedToRole(self.user, self.guild, self.author))

class AdminPanelCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_group(name="admin")    
    async def admin(self, ctx):
        pass        

    async def has_admin_role(self, ctx):
        filter = {
            'guild_id': ctx.guild.id
        }
        admin_data = arole.find_one(filter)

        if admin_data and 'adminrole' in admin_data:
            admin_role_id = admin_data['adminrole']
            admin_role = discord.utils.get(ctx.guild.roles, id=admin_role_id)
            if admin_role in ctx.author.roles:
                return True

        return False    
    

    @admin.command(description="Manage a staff member.")
    async def panel(self, ctx, staff: discord.Member):
        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return            


        infractions = collection.count_documents({"staff": staff.id, "guild_id": ctx.guild.id, "action": {"$ne": "Demotion"}})
        demotions = collection.count_documents({"staff": staff.id, "guild_id": ctx.guild.id, "action": "Demotion"})
        loa = loa_collection.find_one({"user": staff.id, "guild_id": ctx.guild.id})
        loasmg = ""
        if loa is None:
            loamsg = "False"
        else:
            loamsg = "True"

        embed = discord.Embed(title=f"Admin Panel - {staff.name}", description=f"**Mention:** {staff.mention}\n**ID:** *{staff.id}* ",timestamp=datetime.datetime.now(), color=discord.Color.dark_embed())
        embed.add_field(name="<:data:1166529224094523422> Staff Data", value=f"<:arrow:1166529434493386823>**Infractions:** {infractions}\n<:arrow:1166529434493386823>**Demotions:** {demotions}\n<:arrow:1166529434493386823>**Leave Of Absence:** {loamsg}")
        embed.set_author(name=staff.name, icon_url=staff.display_avatar)
        embed.set_footer(text="Staff Management Panel", icon_url="https://media.discordapp.net/ephemeral-attachments/1140411707953520681/1165221940722675722/1035353776460152892.png?ex=6546107f&is=65339b7f&hm=8d73392705483a84a47d09a7cd4838cd2e1235caa1022f10777ea1fec4a91f13&=")
        embed.set_thumbnail(url=staff.display_avatar)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")
        view = AdminPanel(staff, ctx.guild, ctx.author)
        await ctx.send(embed=embed, view=view)



class AdminPanel(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(label='Promote', style=discord.ButtonStyle.grey, emoji='<:Promotion:1162134864594735315>')
    async def Promote(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)               
        if self.author == self.user:
         await interaction.response.send_message(f"{no} You can't promote yourself.", ephemeral=True)
         return

        view = PromotionRoleView(self.user, self.guild, self.author)
        await interaction.response.edit_message(view=view)

    @discord.ui.button(label='Infract', style=discord.ButtonStyle.grey, emoji='<:Infraction:1162134605885870180>')
    async def Infract(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          


        if self.author == self.user:
         await interaction.response.send_message(f"{no} You can't infract yourself.", ephemeral=True)
         return

        view = InfractionOptionView(self.user, self.guild, self.author)
        await interaction.response.edit_message(view=view)
        

    @discord.ui.button(label='Search', style=discord.ButtonStyle.grey, emoji='<:Search:1166509265951932546>')
    async def Search(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        print(f"Searching infractions for staff ID: {self.user.id} in guild ID: {self.user.guild.id}")

        filter = {
            'guild_id': interaction.guild.id,
            'staff': self.user.id,
        }

        infractions = collection.find(filter)

        infraction_list = []

        for infraction in infractions:
            infraction_info = {
                'id': infraction['random_string'],
                'action': infraction['action'],
                'reason': infraction['reason'],
                'notes': infraction['notes']
            }
            infraction_list.append(infraction_info)

        if not infraction_list:
            await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, there are no infractions found for **@{self.user.display_name}**.", ephemeral=True)
            return

        print(f"Found {len(infraction_list)} infractions for {self.user.display_name}")

        embed = discord.Embed(
            title=f"{self.user.display_name}'s Infractions",
            description=f"* **User:** {self.user.mention}\n* **User ID:** {self.user.id}",
            color=discord.Color.dark_embed()
        )
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.set_author(icon_url=self.user.display_avatar, name=self.user.display_name)
        management = interaction.guild.get_member(infraction['management'])
        for infraction_info in infraction_list:
            embed.add_field(
                name=f"Infraction ID: {infraction_info['id']}",
                value=f"* **Infracted By:** {management.mention}\n* **Action:** {infraction_info['action']}\n* **Reason:** {infraction_info['reason']}\n* **Notes:** {infraction_info['notes']}",
                inline=False
            )
        view = Return(self.user, interaction.guild, self.author)
        await interaction.response.edit_message(embed=embed, view=view, content=None)

    @discord.ui.button(label='LOA', style=discord.ButtonStyle.grey, emoji='<:LOA:1164969910238203995>')
    async def LOA(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        filter = {'guild_id': interaction.guild.id, 'user': self.user.id} 
        loa_requests = list(loa_collection.find(filter))            
        loa = loa_collection.find_one({"user": self.user.id, "guild_id": interaction.guild.id})
        view = None
        if loa is None:
            embed = discord.Embed(title="Leave Of Absense", description=f"", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=self.user.display_avatar)
            embed.set_author(icon_url=self.user.display_avatar, name=self.user.display_name)            
            view = LOACreate(self.user, self.guild, self.author)
        else:
         for request in loa_requests:
            start_time = request['start_time']
            end_time = request['end_time']
            reason = request['reason']
            
            embed = discord.Embed(
                title=f"Leave Of Absence",
                color=discord.Color.dark_embed(),
                description=f"* **Start Date:** <t:{int(start_time.timestamp())}:f>\n* **End Date:** <t:{int(end_time.timestamp())}:f>\n* **Reason:** {reason}"
            )
            embed.set_thumbnail(url=self.user.display_avatar)
            embed.set_author(icon_url=self.user.display_avatar, name=self.user.display_name)


            view= LOAPanel(self.user, self.guild, self.author)
        await interaction.response.edit_message(embed=embed, view=view, content=None)



class Return(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(label='Return', style=discord.ButtonStyle.grey, emoji='<:Return:1166514220960063568>')
    async def Return(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        infractions = collection.count_documents({"staff": self.user.id, "guild_id": interaction.guild.id, "action": {"$ne": "Demotion"}})
        demotions = collection.count_documents({"staff": self.user.id, "guild_id": interaction.guild.id, "action": "Demotion"})
        loa = loa_collection.find_one({"user": self.user.id, "guild_id": interaction.guild.id})
        loasmg = ""
        if loa:
            loamsg = "True"
        else:
            loamsg = "False"
        embed = discord.Embed(title=f"Admin Panel - {self.user.name}", description=f"**Mention:** {self.user.mention}\n**ID:** *{self.user.id}* ",timestamp=datetime.datetime.now(), color=discord.Color.dark_embed())
        embed.set_author(name=self.user.name, icon_url=self.user.display_avatar)
        embed.set_footer(text="Staff Management Panel", icon_url="https://media.discordapp.net/ephemeral-attachments/1140411707953520681/1165221940722675722/1035353776460152892.png?ex=6546107f&is=65339b7f&hm=8d73392705483a84a47d09a7cd4838cd2e1235caa1022f10777ea1fec4a91f13&=")
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.add_field(name="<:data:1166529224094523422> Staff Data", value=f"<:arrow:1166529434493386823>**Infractions:** {infractions}\n<:arrow:1166529434493386823>**Demotions:** {demotions}\n<:arrow:1166529434493386823>**Leave Of Absence:** {loamsg}")        
        view = AdminPanel(self.user, interaction.guild, self.author)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")        
        await interaction.response.edit_message(embed=embed, view=view, content=None)


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
        loadata = {'user': user.id, 'guild_id': interaction.guild.id}    
        loarole_data = LOARole.find_one({'guild_id': interaction.guild.id})
        if loarole_data:
         loarole = loarole_data['staffrole']
         if loarole:
          role = discord.utils.get(interaction.guild.roles, id=loarole)
          if role:
            try:
             await user.remove_roles(role)         
            except discord.Forbidden: 
                await interaction.response.edit_message(content=f"{no} I don't have permission to remove roles.", view=Return(self.user, self.guild, self.author), embed=None)
                return
        try:    
         await user.send(f"<:bin:1160543529542635520> Your LOA **@{self.guild.name}** has been voided.")  
        except discord.Forbidden:
                pass              
        loa_collection.delete_one(loadata)
        await interaction.response.edit_message(embed=None, content=f"{tick} Succesfully ended **@{user.display_name}'s** LOA", view=Return(self.user, self.guild, self.author))

    @discord.ui.button(label='Return', style=discord.ButtonStyle.grey, emoji='<:Return:1166514220960063568>')
    async def Return2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        infractions = collection.count_documents({"staff": self.user.id, "guild_id": interaction.guild.id, "action": {"$ne": "Demotion"}})
        demotions = collection.count_documents({"staff": self.user.id, "guild_id": interaction.guild.id, "action": "Demotion"})
        loa = loa_collection.find_one({"user": self.user.id, "guild_id": interaction.guild.id})
        loasmg = ""
        if loa:
            loamsg = "True"
        else:
            loamsg = "False"
        embed = discord.Embed(title=f"Admin Panel - {self.user.name}", description=f"**Mention:** {self.user.mention}\n**ID:** *{self.user.id}* ",timestamp=datetime.datetime.now(), color=discord.Color.dark_embed())
        embed.set_author(name=self.user.name, icon_url=self.user.display_avatar)
        embed.set_footer(text="Staff Management Panel", icon_url="https://media.discordapp.net/ephemeral-attachments/1140411707953520681/1165221940722675722/1035353776460152892.png?ex=6546107f&is=65339b7f&hm=8d73392705483a84a47d09a7cd4838cd2e1235caa1022f10777ea1fec4a91f13&=")
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.add_field(name="<:data:1166529224094523422> Staff Data", value=f"<:arrow:1166529434493386823>**Infractions:** {infractions}\n<:arrow:1166529434493386823>**Demotions:** {demotions}\n<:arrow:1166529434493386823>**Leave Of Absence:** {loamsg}")        
        view = AdminPanel(self.user, interaction.guild, self.author)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")        
        await interaction.response.edit_message(embed=embed, view=view, content=None)


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

    @discord.ui.button(label='Return', style=discord.ButtonStyle.grey, emoji='<:Return:1166514220960063568>')
    async def Return3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        infractions = collection.count_documents({"staff": self.user.id, "guild_id": interaction.guild.id, "action": {"$ne": "Demotion"}})
        demotions = collection.count_documents({"staff": self.user.id, "guild_id": interaction.guild.id, "action": "Demotion"})
        loa = loa_collection.find_one({"user": self.user.id, "guild_id": interaction.guild.id})
        loasmg = ""
        if loa:
            loamsg = "True"
        else:
            loamsg = "False"
        embed = discord.Embed(title=f"Admin Panel - {self.user.name}", description=f"**Mention:** {self.user.mention}\n**ID:** *{self.user.id}* ",timestamp=datetime.datetime.now(), color=discord.Color.dark_embed())
        embed.set_author(name=self.user.name, icon_url=self.user.display_avatar)
        embed.set_footer(text="Staff Management Panel", icon_url="https://media.discordapp.net/ephemeral-attachments/1140411707953520681/1165221940722675722/1035353776460152892.png?ex=6546107f&is=65339b7f&hm=8d73392705483a84a47d09a7cd4838cd2e1235caa1022f10777ea1fec4a91f13&=")
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.add_field(name="<:data:1166529224094523422> Staff Data", value=f"<:arrow:1166529434493386823>**Infractions:** {infractions}\n<:arrow:1166529434493386823>**Demotions:** {demotions}\n<:arrow:1166529434493386823>**Leave Of Absence:** {loamsg}")        
        view = AdminPanel(self.user, interaction.guild, self.author)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")        
        await interaction.response.edit_message(embed=embed, view=view, content=None)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(AdminPanelCog(client))                
