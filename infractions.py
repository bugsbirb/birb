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
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
collection = db['infractions']
scollection = db['staffrole']
arole = db['adminrole']
infchannel = db['infraction channel']
appealable = db['Appeal Toggle']
appealschannel = db['Appeals Channel']
consent = db['consent']




class AppealButtonView(discord.ui.View):
    def __init__(self, guild_id, random_string, action, reason):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.random_string = random_string
        self.action = action
        self.reason = reason

    @discord.ui.button(label='Appeal', style=discord.ButtonStyle.grey, custom_id='persistent:appealing')
    async def appealing(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BanAppeal(self.guild_id, self.random_string, self.action, self.reason))
        

class AcceptOrdeny(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.Accepted = False
        self.Denied = False
    @discord.ui.button(label='Accept', style=discord.ButtonStyle.grey, custom_id='persistent:Accept')
    async def Accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"{tick} Appeal **`Accepted`** by **{interaction.user.display_name}**", view=None)
        self.Accepted = True        
        self.stop()

    @discord.ui.button(label='Deny', style=discord.ButtonStyle.grey, custom_id='persistent:Deny')
    async def Deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"{no} Appeal **`Denied`** by **{interaction.user.display_name}**", view=None)        
        self.Denied = True
        self.stop()
class Infractions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def has_staff_role(self, ctx):
        filter = {
            'guild_id': ctx.guild.id
        }
        staff_data = scollection.find_one(filter)

        if staff_data and 'staffrole' in staff_data:
            staff_role_id = staff_data['staffrole']
            staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_id)

            if staff_role and staff_role in ctx.author.roles:
                return True

        return False


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

    @commands.hybrid_command(description="Infract staff members")
    async def infract(self, ctx, staff: discord.Member, reason: str, action: Literal['Activity Notice', 'Verbal Warning', 'Warning', 'Strike', 'Demotion', 'Termination'], notes: Optional[str]):
        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return           

        random_string = ''.join(random.choices(string.digits, k=8))
        if notes:
         embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Notes:** {notes}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
        else:
         embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=staff.display_avatar)
        embed.set_author(name=f"Signed, {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
        embed.set_footer(text=f"Infraction ID | {random_string}")
        infract_data = {
            'management': ctx.author.id,
            'staff': staff.id,
            'action': action,
            'reason': reason,
            'notes': notes,
            'random_string': random_string,
            'guild_id': ctx.guild.id
        }

        guild_id = ctx.guild.id
        data = infchannel.find_one({'guild_id': guild_id})
        appeal_data = appealable.find_one({'guild_id': str(ctx.guild.id)})
        consent_data = consent.find_one({"user_id": staff.id})
        if consent_data is None:
            consent.insert_one({"user_id": staff.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled"})            
            consent_data = {"user_id": staff.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled"}

        if appeal_data is not None:
         appeal_enabled = appeal_data.get('enabled', False)
        else:
          appeal_enabled = False
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
            view = AppealButtonView(ctx.guild.id, random_string, action, reason) if appeal_enabled else None
            
            await ctx.send(f"{tick} **{ctx.author.display_name}**, I've infracted **@{staff.display_name}**")
            try:
             await channel.send(f"{staff.mention}", embed=embed)
            except discord.Forbidden: 
             await ctx.send(f"{no} I don't have permission to view that channel.")             
            collection.insert_one(infract_data)
            if consent_data['infractionalert'] == "Enabled":
             try:
                await staff.send(f"<:SmallArrow:1140288951861649418> From **{ctx.guild.name}**", embed=embed, view=view)
             except discord.Forbidden:
                pass
            else:
                pass
         else:
            await ctx.send(f"{Warning} {ctx.author.display_name}, I don't have permission to view this channel.")
        else:
          await ctx.send(f"{Warning} **{ctx.author.display_name}**, the channel is not setup please run `/config`")

    @commands.hybrid_command(description="View a staff members infractions")
    async def infractions(self, ctx, staff: discord.Member):
     if not await self.has_staff_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return               

     print(f"Searching infractions for staff ID: {staff.id} in guild ID: {ctx.guild.id}")

     filter = {
        'guild_id': ctx.guild.id,
        'staff': staff.id,
    }

     infractions = collection.find(filter)

     infraction_list = []

     for infraction in infractions:
        infraction_info = {
            'id': infraction['random_string'],
            'action': infraction['action'],
            'reason': infraction['reason'],
            'notes': infraction['notes'],
            'management': infraction['management']
        }
        infraction_list.append(infraction_info)

     if not infraction_list:
        await ctx.send(f"{no} **{ctx.author.display_name}**, there is no infractions found for **@{staff.display_name}**.")
        return

     print(f"Found {len(infraction_list)} infractions for {staff.display_name}")

     embed = discord.Embed(
        title=f"{staff.name}'s Infractions",
        description=f"* **User:** {staff.mention}\n* **User ID:** {staff.id}",
        color=discord.Color.dark_embed()
    )
     embed.set_thumbnail(url=staff.display_avatar)
     embed.set_author(icon_url=staff.display_avatar, name=staff.display_name)
     for infraction_info in infraction_list:
        management = self.client.get_user(infraction_info['management'])        
        embed.add_field(
            name=f"<:Document:1166803559422107699> Infraction | {infraction_info['id']}",
            value=f"<:arrow:1166529434493386823>**Infracted By:** {management.mention}\n<:arrow:1166529434493386823>**Action:** {infraction_info['action']}\n<:arrow:1166529434493386823>**Reason:** {infraction_info['reason']}\n<:arrow:1166529434493386823>**Notes:** {infraction_info['notes']}",
            inline=False
        )

     await ctx.send(embed=embed)

    @commands.hybrid_group()
    async def infraction(self, ctx):
        return

    @infraction.command(description="Void a staff member's infraction")
    async def void(self, ctx, id: str):
     if not await self.has_admin_role(ctx):
        await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
        return

     filter = {
        'guild_id': ctx.guild.id,
        'random_string': id
    }

     infraction = collection.find_one(filter)

     if infraction is None:
        await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find the infraction with ID `{id}` in this guild.")
        return

     collection.delete_one(filter)
 
     await ctx.send(f"{tick} **{ctx.author.display_name}**, I've voided the infraction with ID `{id}` in this guild.")
     


class BanAppeal(discord.ui.Modal, title='Infraction Appeal'):
    def __init__(self, guild_id, random_string, action, reason):
        super().__init__()
        self.guild_id = guild_id
        self.random_string = random_string
        self.action = action
        self.reason = reason


    Why1 = discord.ui.TextInput(
        label='Why were you infracted?',
        placeholder='',
    )
    Why2 = discord.ui.TextInput(
        label='Why should your infraction get revoked??',
        placeholder='',
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.client.get_guild(self.guild_id)
        guild_id = self.guild_id
        data = appealschannel.find_one({'guild_id': guild_id})

        if data:
                channel_id = data['channel_id']
                channel = interaction.client.get_channel(channel_id)

                if channel:
                    embed = discord.Embed(
                        title="Infraction Appeal Submission",
                        description=f"**Why were you infracted?**\n{self.Why1.value}\n\n**Why should you be uninfracted?**\n{self.Why2.value}",
                        color=0x2b2d31
                    )
                    embed.add_field(
            name=f"Infraction ID: {self.random_string}",
            value=f"* **Action:** {self.action}\n* **Reason:** {self.reason}",
            inline=False
        )                    
                    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)     
                    response_embed2 = discord.Embed(
                        title="Success!",
                        description="Your infraction appeal has been submitted successfully.",
                        color=0x2b2d31
                    )
                    response_embed2.set_author(name=guild.name, icon_url=guild.icon)

                    await interaction.response.send_message(embed=response_embed2)   
                    print(f"Infraction Appeal at {guild.name}")
                    view = AcceptOrdeny()
                    await channel.send(embed=embed, view=view)
                    await view.wait()
           
                    if view.Accepted:
                     collection.delete_one({'random_string': self.random_string})
                     embed = discord.Embed(
                        title="Infraction Appeal Update",
                        description=f"{tick} Your appeal has been **accepted!**",

                        color=discord.Color.dark_embed())
                     print(f"Infraction Appeal Accepted at {guild.name}")
                    
                     embed.set_author(name=guild.name, icon_url=guild.icon)
                     await interaction.user.send(embed=embed)                      

                    elif view.Denied:
                     embed = discord.Embed(
                        title="Infraction Appeal Update",
                        description=f"{no} Your appeal has been **denied.**",
                        color=discord.Color.dark_embed())
                     embed.set_author(name=guild.name, icon_url=guild.icon)                    
                     print(f"Infraction Appeal Denied at {guild.name}")                     
                     await interaction.user.send(embed=embed)  


                              

                else:
                    await interaction.response.send_message("The appeal channel does not exist or the bot does not have access to it.")

       

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Infractions(client))       