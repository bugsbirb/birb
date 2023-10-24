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


scollection = db['staffrole']
arole = db['adminrole']
promochannel = db['promo channel']




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
                view=None,
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
                        view=None)
                 return               
            await interaction.response.edit_message(content=f"{tick} **{self.author.display_name}**, I've demoted **@{self.user.display_name}**", embed=None, view=None)
            try:
             await channel.send(f"{self.user.mention}", embed=embed)
            except discord.Forbidden: 
             await interaction.response.edit_message(content=f"{no} I don't have permission to view that channel.", view=None, embed=None)             
            collection.insert_one(infract_data)
            try:
                await self.user.send(f"<:SmallArrow:1140288951861649418> From **{interaction.guild.name}**", embed=embed, view=view)
            except discord.Forbidden:
                pass
        else:
          await interaction.response.edit_message(content=f"{Warning} **{self.author.display_name}**, the channel is not setup please run `/config`", embed=None, view=None)
















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
                view=None,
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
                        view=None)
                 return       

                try:
                    await channel.send(f"{interaction.user.mention}", embed=embed)
                except discord.Forbidden:
                    await interaction.response.edit_message(
                        content=f"{no} I don't have permission to view that channel.",
                        embed=None,
                        view=None
                    )
                    return   

                await interaction.response.edit_message(
                    content=f"{tick} **{self.author.display_name}**, I've promoted **@{self.user.display_name}**",
                    embed=None,
                    view=None
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
            
            await interaction.response.edit_message(content=f"{tick} **{self.author.display_name}**, I've infracted **@{self.user.display_name}**", embed=None, view=None)
            try:
             await channel.send(f"{self.user.mention}", embed=embed)
            except discord.Forbidden: 
             await interaction.response.edit_message(content=f"{no} I don't have permission to view that channel.", view=None, embed=None)             
            collection.insert_one(infract_data)
            try:
                await self.user.send(f"<:SmallArrow:1140288951861649418> From **{interaction.guild.name}**", embed=embed, view=view)
            except discord.Forbidden:
                pass
        else:
          await interaction.response.edit_message(content=f"{Warning} **{self.author.display_name}**, the channel is not setup please run `/config`", embed=None, view=None)

class InfractionOption(discord.ui.Select):
    def __init__(self, user, guild, author):
        self.user = user
        self.guild = guild
        self.author = author        
        options = [
            discord.SelectOption(label='Activity Notice'),
            discord.SelectOption(label='Verbal Warning'),                
            discord.SelectOption(label='Warning'),            
            discord.SelectOption(label='Strike')                
 

        
            
        ]
        super().__init__(placeholder='Infraction Types', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        option = self.values[0]

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
        embed = discord.Embed(title=f"Admin Panel - {staff.name}", description=f"**Mention:** {staff.mention}\n**ID:** *{staff.id}* ",timestamp=datetime.datetime.now(), color=discord.Color.dark_embed())
        embed.set_author(name=staff.name, icon_url=staff.display_avatar)
        embed.set_footer(text="Staff Management Panel")
        embed.set_thumbnail(url=staff.display_avatar)
        view = AdminPanel(staff, ctx.guild, ctx.author)
        await ctx.send(embed=embed, view=view)



class AdminPanel(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(label='Promote', style=discord.ButtonStyle.grey)
    async def Promote(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)               

        view = PromotionRoleView(self.user, self.guild, self.author)
        await interaction.response.edit_message(view=view)

    @discord.ui.button(label='Demotion', style=discord.ButtonStyle.grey)
    async def Demotion(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
        view = DemotionRoleView(self.user, self.guild, self.author)
        await interaction.response.edit_message(view=view)
    @discord.ui.button(label='Infract', style=discord.ButtonStyle.grey)
    async def Infract(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          
        view = InfractionOptionView(self.user, self.guild, self.author)
        await interaction.response.edit_message(view=view)
        




async def setup(client: commands.Bot) -> None:
    await client.add_cog(AdminPanelCog(client))                
