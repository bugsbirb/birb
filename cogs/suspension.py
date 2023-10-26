import discord
import sqlite3
from discord.ext import commands
from typing import Literal
import datetime 
from datetime import timedelta
import asyncio
from discord import app_commands
from discord.ext import commands, tasks
import pytz
from pymongo import MongoClient
from emojis import *
import time
import os
from dotenv import load_dotenv
from cogs.infractions import *
from datetime import datetime

MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
suspensions = db['Suspensions']


class Suspensions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.check_suspensions.start()
        print("Suspension loop started")

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

    @commands.hybrid_command(description="Suspend a staff member")
    @app_commands.describe(staff="What user are you suspending?",length="e.g 1w (m/h/d/w)", reason="What is the reason for this suspension?")
    async def suspend(self, ctx, staff: discord.Member, length: str, reason: str):
        if not await self.has_admin_role(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
            return


        if ctx.author == staff:
         await ctx.send(f"{no} You can't suspend yourself.")
         return

        if ctx.author.top_role <= staff.top_role:
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have authority to suspend this user they are higher then you in the hierarchy.", ephemeral=True)
            return
 
        filter = {'guild_id': ctx.guild.id, 'staff': staff.id, 'active': True}
        existing_suspensions = suspensions.find_one(filter)

        if existing_suspensions:
         await ctx.send(f"{no} **{staff.display_name}** is already suspended.", ephemeral=True)
         return

        duration_value = int(length[:-1])
        duration_unit = length[-1]
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
        embed = discord.Embed(title="", description="<:Tip:1167083259444875264> **TIP:** Make sure the bot has permissions to send messages to the channel & to removes roles.", color=discord.Color.light_embed())
        view = RoleTakeAwayYesOrNo(staff, ctx.author, reason, end_time, start_time)
        await ctx.send("<:Role:1162074735803387944> Would you like to **remove roles** from this person? Don't worry the roles will be **returned** after suspension.", view=view, embed=embed)

    @commands.hybrid_group()    
    async def suspension(self, ctx):
        pass

    @suspension.command(description="View all active suspension")
    async def active(self, ctx):
     if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return             

     filter = {'guild_id': ctx.guild.id, 'active': True}

     loa_requests = list(suspensions.find(filter))

     if len(loa_requests) == 0:
        await ctx.send(f"{no} **{ctx.author.display_name}**, there aren't any active suspensions on this server.")
     else:
        embed = discord.Embed(
            title="Active Suspensions",
            color=discord.Color.dark_embed()
        )
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(icon_url=ctx.guild.icon , name=ctx.guild.name)
        for request in loa_requests:
            user = self.client.get_user(request['staff'])
            start_time = request['start_time']
            end_time = request['end_time']
            start_time = request['start_time']
            reason = request['reason']

            embed.add_field(
                name=f"<:Infraction:1162134605885870180>{user.name.capitalize()}",
                value=f"<:arrow:1166529434493386823>**Start Date:** <t:{int(start_time.timestamp())}:f>\n<:arrow:1166529434493386823>**End Date:** <t:{int(end_time.timestamp())}:f>\n<:arrow:1166529434493386823>**Reason:** {reason}",
                inline=False
            )

        await ctx.send(embed=embed)    

    @suspension.command(description="Manage suspensions on a user")

    async def manage(self, ctx, staff: discord.Member):
     if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return   
     filter = {'guild_id': ctx.guild.id, 'staff': staff.id}
     suspension_requests = suspensions.find(filter)

     suspension_records = []

     for request in suspension_requests:
        end_time = request['end_time']
        start_time = request['start_time']
        user_id = request['staff']
        guild_id = request['guild_id']
        user = self.client.get_user(user_id)
        reason = request['reason']

        suspension_records.append({
            'user': user,
            'start_time': start_time,
            'end_time': end_time,
            'reason': reason,
        })

     if suspension_records:
        embed = discord.Embed(
            title="Suspensions",
            color=discord.Color.dark_embed()
        )

        for record in suspension_records:
            user = record['user']
            start_time = record['start_time']
            end_time = record['end_time']
            reason = record['reason']

            embed.add_field(
                name=f"<:Infraction:1162134605885870180>{user.name.capitalize()}",
                value=f"<:arrow:1166529434493386823>**Start Date:** <t:{int(start_time.timestamp())}:f>\n<:arrow:1166529434493386823>**End Date:** <t:{int(end_time.timestamp())}:f>\n<:arrow:1166529434493386823>**Reason:** {reason}",
                inline=False
            )

        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(icon_url=ctx.guild.icon, name=ctx.guild.name)

        view = SuspensionPanel(staff, ctx.author)
        await ctx.send(embed=embed, view=view)
     else:
        await ctx.send(f"{no} No suspensions found for this user.")

    


    @tasks.loop(seconds=10)
    async def check_suspensions(self):
     current_time = datetime.now()
     filter = {'end_time': {'$lte': current_time}, 'action': 'Suspension'}

     suspension_requests = suspensions.find(filter)

     for request in suspension_requests:
        end_time = request['end_time']
        user_id = request['staff']
        guild_id = request['guild_id']
        guild = self.client.get_guild(guild_id)
        user = self.client.get_user(user_id)
        if current_time >= end_time:
                if user:
                 await user.send(f"{tick} Your suspension in **@{guild.name}** has ended.")
                 delete_filter = {'guild_id': guild_id, 'staff': user_id, 'action': 'Suspension'}
                 suspensions.delete_one(delete_filter)

                try:
                    roles_removed = request['roles_removed']
                    roles_to_return = [discord.utils.get(guild.roles, id=role_id) for role_id in roles_removed if guild.get_member(user_id)]
                    
                    if roles_to_return:
                        member = guild.get_member(user_id)
                        await member.add_roles(*roles_to_return)
                except KeyError:
                    pass



class Suspension(discord.ui.RoleSelect):
    def __init__(self, user, author, reason, end_time, start_time):
        super().__init__(placeholder='Removed Roles', max_values=10)
        self.user = user
        self.author = author
        self.reason = reason
        self.end_time = end_time
        self.start_time = start_time

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.global_name},** this is not your view",
                color=discord.Colour.dark_embed()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        selected_role_ids = [role.id for role in self.values]

        infract_data = {
            'guild_id': interaction.guild.id,
            'management': interaction.user.id,
            'staff': self.user.id,
            'action': "Suspension",
            'start_time': self.start_time,
            'end_time': self.end_time,
            'roles_removed': selected_role_ids,
            'reason': self.reason,
            'active': True,
            'notes': "`N/A`"
        }

        embed = discord.Embed(
            title="Staff Consequences & Discipline",
            description=f"* **Staff Member:** {self.user.mention}\n* **Action:** Suspension\n* **Reason:** {self.reason}\n* **Duration:** <t:{int(self.start_time.timestamp())}:f> - <t:{int(self.end_time.timestamp())}:f>",
            color=discord.Color.dark_embed()
        )
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.set_author(name=f"Signed, {self.author.display_name}", icon_url=self.author.display_avatar)

        data = infchannel.find_one({'guild_id': interaction.guild.id})
        if data:
            channel_id = data['channel_id']
            channel = interaction.guild.get_channel(channel_id)

            if channel:
                roles_to_remove = []

                for role_id in selected_role_ids:
                    role = discord.utils.get(interaction.guild.roles, id=role_id)
                    if role:
                        roles_to_remove.append(role)

                try:
                    await channel.send(f"{self.user.mention}", embed=embed)
                except discord.Forbidden:
                    await interaction.response.edit_message(content=f"{no} I don't have permission to view that channel.", view=None, embed=None)
                    return

                try:
                    await self.user.remove_roles(*roles_to_remove, reason=self.reason)
                except discord.Forbidden:
                    await interaction.response.edit_message(
                        content=f"{no} {interaction.user.display_name}, I don't have permission to add roles.",
                        view=None,
                        embed=None
                    )
                    return
  
                try:
                 await self.user.send(f"<:SmallArrow:1140288951861649418> From **{interaction.guild.name}**", embed=embed, view=None)
                except discord.Forbidden:
                 pass


                suspensions.insert_one(infract_data)
                await interaction.response.edit_message(
                    content=f"{tick} **{interaction.user.display_name}**, I've suspended **@{self.user.display_name}**",
                    view=None,
                    embed=None
                )
            else:
                await interaction.response.edit_message(content=f"{no} **{interaction.user.display_name}**, the channel is not set up. Please run `/config`.", view=None, embed=None)


class RoleTakeAwayYesOrNo(discord.ui.View):
    def __init__(self, user, author, reason, end_time, start_time):
        super().__init__(timeout=None)
        self.user = user
        self.author = author        
        self.reason = reason
        self.end_time = end_time
        self.start_time = start_time

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def Yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)   
        view = RoleTakeAwayView(self.user, self.author, self.reason, self.end_time, self.start_time)
        await interaction.response.edit_message(content=f"<:Role:1162074735803387944> Select the **roles** that will be removed & then given back after the suspension is over.", embed=None, view=view)

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def No(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)   
        infract_data = {'guild_id': interaction.guild.id,
        'management': interaction.user.id,
        'staff': self.user.id,
        'action': "Suspension",
        'start_time': self.start_time,
        'end_time': self.end_time,
        'reason': self.reason,
        'active': True,
        'notes': "`N/A`"
        }     

        embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {self.user.mention}\n* **Action:** Suspension\n* **Reason:** {self.reason}\n* **Duration:** <t:{int(self.start_time.timestamp())}:f> - <t:{int(self.end_time.timestamp())}:f>", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=self.user.display_avatar)
        embed.set_author(name=f"Signed, {self.author.display_name}", icon_url=self.author.display_avatar)


        appeal_data = appealable.find_one({'guild_id': str(interaction.guild.id)})

        if appeal_data is not None:
         appeal_enabled = appeal_data.get('enabled', False)
        else:
          appeal_enabled = False

        data = infchannel.find_one({'guild_id': interaction.guild.id})       
        if data:
         channel_id = data['channel_id']
         channel = interaction.guild.get_channel(channel_id)

         if channel:

            
            
            try:
             await channel.send(f"{self.user.mention}", embed=embed)
            except discord.Forbidden: 
             await interaction.response.edit_message(content=f"{no} I don't have permission to view that channel.", view=None, embed=None)             
             return

            try:
                await self.user.send(f"<:SmallArrow:1140288951861649418> From **{interaction.guild.name}**", embed=embed, view=None)
            except discord.Forbidden:
                pass
            suspensions.insert_one(infract_data)
            await interaction.response.edit_message(content=f"{tick} **{interaction.user.display_name}**, I've suspended **@{self.user.display_name}**", view=None, embed=None)            
         else:
            await interaction.response.edit_message(content=f"{no} {interaction.user.display_name}, I don't have permission to view this channel.", view=None, embed=None)
        else:
          await interaction.response.edit_message(content=f"{no} **{interaction.user.display_name}**, the channel is not setup please run `/config`", view=None, embed=None)

class RoleTakeAwayView(discord.ui.View):
    def __init__(self, user, author, reason, end_time, start_time):
        super().__init__()
        self.user = user
        self.author = author        
        self.reason = reason
        self.end_time = end_time
        self.start_time = start_time      
        self.add_item(Suspension(self.user, self.author, self.reason, self.end_time, self.start_time))


class SuspensionPanel(discord.ui.View):
    def __init__(self, user, author):
        super().__init__(timeout=None)
        self.user = user
        self.author = author        


    @discord.ui.button(label='Suspension Void', style=discord.ButtonStyle.grey, emoji='<:Exterminate:1164970632262451231>')
    async def SuspensionVoid(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.mention},** this is not your view.", color=discord.Colour.dark_grey())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        suspension_record = suspensions.find_one({'guild_id': interaction.guild.id, 'staff': self.user.id})
        if suspension_record:
         roles_removed = suspension_record.get('roles_removed', [])
         if roles_removed:
            roles_to_return = [discord.utils.get(interaction.guild.roles, id=role_id) for role_id in roles_removed]
            member = interaction.guild.get_member(self.user.id)

            print(f"roles_removed: {roles_removed}")
            print(f"roles_to_return: {roles_to_return}")

            if roles_to_return and member:
                await interaction.response.defer()
                await interaction.edit_original_response(content=f"<a:Loading:1167074303905386587> Loading...", embed=None, view=None)                
                try:
                    await member.add_roles(*roles_to_return)
                    await interaction.edit_original_response(content=f"{tick} Suspension has been voided. Roles have been restored.", view=None, embed=None)
                    suspensions.delete_one({'guild_id': interaction.guild.id, 'staff': self.user.id})                    
                    await member.send(f"<:bin:1160543529542635520> Your suspension has been voided **@{interaction.guild.name}**")
                except discord.Forbidden:
                    await interaction.edit_original_response(content=f"{no} Failed to restore roles due to insufficient permissions.", ephemeral=True)

         else:
            member = interaction.guild.get_member(self.user.id)
            suspensions.delete_one({'guild_id': interaction.guild.id, 'staff': self.user.id})
            await interaction.response.edit_message(content=f"{tick} Suspension has been voided.", embed=None, view=None)
            try:
             await member.send(f"<:bin:1160543529542635520> Your suspension has been voided **@{interaction.guild.name}**")
            except discord.Forbidden: 
                pass
        else:
          await interaction.response.send_message(f"{no} No suspension found.", ephemeral=True)





async def setup(client: commands.Bot) -> None:
    await client.add_cog(Suspensions(client))     
