import discord
from discord.ext import commands, tasks
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import pytz
from discord import app_commands
from pymongo import MongoClient
from emojis import *
import typing
import Paginator
client = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = client['astro']
scollection = db['staffrole']
ticketconfig = db['Tickets Configuration']
tickets = db['Tickets']


class Tickets(commands.Cog):
    def __init__(self, client):
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

    @commands.hybrid_group()
    async def tickets(self, ctx):
        return
            

    @tickets.command(name="config", description="Config the tickets module.")
    async def ticketsconfig(self, ctx, panel: discord.TextChannel, category: discord.CategoryChannel):
        config_data = ticketconfig.find_one({'guild_id': int(ctx.guild.id)}) 
        title = config_data.get('title', f"{ctx.guild.name} Support") if config_data else f"{ctx.guild.name} Support"
        description = config_data.get('description', "Open a ticket for support") if config_data else "Open a ticket for support"

        embed = discord.Embed(title=title, description=description, color=discord.Color.dark_embed())

        view = TicketConfig(int(ctx.guild.id), embed, panel)  
        await ctx.send(embed=embed, view=view)
        filter = {'guild_id': int(ctx.guild.id)}  
        update = {'$set': {'category': int(category.id)}}
        ticketconfig.update_one(filter, update, upsert=True)

    @tickets.command(name='close', description="Close a ticket")
    async def ticket_close(self, ctx):
        if not await self.has_staff_role(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")

        channel_id = ctx.channel.id
        ticket_data = tickets.find_one({'channel_id': channel_id})
        if not ticket_data:
            await ctx.send(f"{no} Ticket not found.")
            return

        user_id = ticket_data['user_id']
        user = self.client.get_user(user_id)

        if user:
            await user.send(f"{tick} Your ticket has been closed at **@{ctx.guild.name}**.")
            tickets.delete_one({'channel_id': channel_id})
            await ctx.send(f"{tick} Ticket closed successfully.")
            await ctx.channel.delete()            
        else:
            await ctx.send(f"{no} User not found.")
  
    @tickets.command(name='claim', description="Claim a ticket")
    async def ticket_claim(self, ctx):
        if not await self.has_staff_role(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")        
        channel_id = ctx.channel.id
        ticket_data = tickets.find_one({'channel_id': channel_id})
        if not ticket_data:
            await ctx.send(f"{no} Ticket not found.")
            return

        user_id = ticket_data['user_id']
        user = self.client.get_user(user_id)

        if user:
            new_name = f'claimed-{user}'
            await ctx.channel.edit(name=new_name)
            await ctx.send(f"{tick} Ticket claimed by **@{user.display_name}**.")
        else:
            await ctx.send(f"{no} User not found.")




class TicketOpen(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @discord.ui.button(label='Open', style=discord.ButtonStyle.grey, custom_id='open_ticket')
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        category_data = ticketconfig.find_one({'guild_id': int(interaction.guild.id)})
        category_id = category_data.get('category')

        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=int(category_id))  
        user = interaction.user

        if category:
            category_overwrites = category.overwrites
            overwrites = {
                
                **category_overwrites,
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await category.create_text_channel(f'ticket-{user.display_name}', overwrites=overwrites)
            embed = discord.Embed(title=f"Support Ticket", description=f"* **Profile**\n> **User:** {user.mention}\n> **Display:** {user.display_name}\n> **ID:** {user.id}\n> **Join:** <t:{int(user.joined_at.timestamp())}:F>\n> **Created:** <t:{int(user.created_at.timestamp())}:F>", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=user, icon_url=user.display_avatar)
            view = TicketHelp()
            await channel.send(embed=embed, view=view)

            ticket_data = {
                'channel_id': channel.id,
                'user_id': user.id
            }
            tickets.insert_one(ticket_data)

            await interaction.response.send_message(f"{channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message(f"{Warning} Category not found. Please check the server's category settings or contact the server administrator.", ephemeral=True)
class TicketConfig(discord.ui.View):
    def __init__(self, guild_id, embed, panel):
        super().__init__(timeout=None)
        self.value = None
        self.guild_id = guild_id
        self.embed = embed
 
        self.panel = panel

    @discord.ui.button(label='Send Panel', style=discord.ButtonStyle.green)
    async def Save(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TicketOpen()
        await self.panel.send(embed=self.embed, view=view)
        await interaction.response.edit_message(content=f"{tick} Ticket panel **sent**", embed=None, view=None)

        
    @discord.ui.button(label='Change Title', style=discord.ButtonStyle.grey)
    async def Title(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChangeTitle(self.guild_id, self.embed,  self.panel))
        
    @discord.ui.button(label='Change Description', style=discord.ButtonStyle.grey)
    async def Description(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChangeDescription(self.guild_id, self.embed,  self.panel))
        

class TicketHelp(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)



    @discord.ui.button(label='Commands', style=discord.ButtonStyle.grey, emoji="<:Commands:1162424769875021956>", custom_id='persitent:TicketsCommands')
    async def TicketCommands(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="<:Commands:1162424769875021956> Ticket Commands", description="* /tickets close\n> Closes tickets.\n\n* /tickets claim\n> Claim a ticket so you have priority support over it.", color=discord.Color.dark_embed())
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        embed.set_thumbnail(url=interaction.guild.icon)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
class ChangeTitle(discord.ui.Modal, title='Tickets Config'):
    def __init__(self, guild_id, embed,  panel):
        super().__init__()
        self.guild_id = guild_id
        self.embed = embed
        self.panel = panel

    Why1 = discord.ui.TextInput(
        label='Embed Title',
        placeholder='')

    async def on_submit(self, interaction: discord.Interaction):
        new_title = self.Why1.value 
        self.embed.title = new_title 
        await interaction.response.edit_message(embed=self.embed)  
        filter = {'guild_id': str(interaction.guild_id)}
        update = {'$set': {'title': new_title}}
        ticketconfig.update_one(filter, update, upsert=True) 
        
class ChangeDescription(discord.ui.Modal, title='Tickets Config'):
    def __init__(self, guild_id, embed,  panel):
        super().__init__()
        self.guild_id = guild_id
        self.embed = embed
        self.panel = panel


    Why1 = discord.ui.TextInput(
        label='Embed Description',
        placeholder='',)


    async def on_submit(self, interaction: discord.Interaction):
        new_description = self.Why1.value
        self.embed.description = new_description 
        await interaction.response.edit_message(embed=self.embed)
        filter = {'guild_id': interaction.guild_id}
        update = {'$set': {'description': new_description}}
        ticketconfig.update_one(filter, update, upsert=True)
      

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Tickets(client))        
