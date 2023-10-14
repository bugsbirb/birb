import discord
import sqlite3
import discord
from discord.ext import commands
from typing import Literal
import datetime
from datetime import timedelta
import asyncio
from discord import app_commands
from discord.ext import commands, tasks
import pytz
import Paginator
from pymongo import MongoClient
from emojis import *
import re

mongo = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = mongo['astro']
loachannel = db['loa channel']
scollection = db['staffrole']
arole = db['adminrole']



class LOA(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.connection = sqlite3.connect("loa.db")
        self.pizza = self.connection.cursor()
        self.pizza.execute("""
            CREATE TABLE IF NOT EXISTS loa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                reason TEXT
            )
        """)
        self.connection.commit()
        self.check_loa_status.start()

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

    @commands.hybrid_group(name="loa", invoke_without_command=True)
    async def loa(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a subcommand.")


    @loa.command(
        name="view",
        description="View active LOAs"
    )
    async def loa_view(self, ctx):
        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return             
        guild_id = ctx.guild.id
        self.pizza.execute("SELECT * FROM loa WHERE guild_id=?", (guild_id,))
        loas = self.pizza.fetchall()

        if not loas:
            await ctx.send(f"<:Allonswarning:1123286604849631355>**{ctx.author.display_name}**, no LOAs to be found.")
            return

        embeds = []
        for loa in loas:
            id, guild_id, user_id, start_time, end_time, reason = loa
            user = await self.client.fetch_user(user_id)

            start = datetime.datetime.fromisoformat(start_time).astimezone(pytz.timezone('Europe/London'))
            end = datetime.datetime.fromisoformat(end_time).astimezone(pytz.timezone('Europe/London'))
            duration = end - start

            embed = discord.Embed(
                title="Active LOAs",
                color=0x2b2d31,
                description=f"* **User:** {user.mention}\n* **Start Date**: <t:{int(start.timestamp())}:F>\n* **End Date:** <t:{int(end.timestamp())}:F>\n* **Reason:** {reason}"
            )
            embed.set_thumbnail(url=ctx.guild.icon)
            embeds.append(embed)

        PreviousButton = discord.ui.Button(label=f"<")
        NextButton = discord.ui.Button(label=f">")
        FirstPageButton = discord.ui.Button(label=f"<<")
        LastPageButton = discord.ui.Button(label=f">>")
        InitialPage = 0
        timeout = 42069

        paginator = Paginator.Simple(
        PreviousButton=PreviousButton,
        NextButton=NextButton,
        FirstEmbedButton=FirstPageButton,
        LastEmbedButton=LastPageButton,
        InitialPage=InitialPage,
        )

        await paginator.start(ctx, pages=embeds)



    @loa.command(name="request", description="Request a leave of absence")
    @app_commands.describe(
        duration='How long do you want the LOA for? (m/h/d)',
        reason='What is the reason for this LOA?')         
    async def loa_request(self, ctx, duration: str, reason: str):
        if not await self.has_staff_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return     

        if not re.match(r'^\d+[mhd]$', duration):
         await ctx.send(f"{no} **{ctx.author.display_name}**, please use the correct duration format (e.g., '5d', '3h', '30m').")
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

        start_time = datetime.datetime.utcnow().astimezone(pytz.timezone('Europe/London'))
        end_time = start_time + datetime.timedelta(seconds=duration_seconds)



        embed = discord.Embed(
            title=f"**{ctx.author.display_name}**, LOA Request",
            description=f"* **Start Date**: <t:{int(start_time.timestamp())}:F>\n* **End Date:** <t:{int(end_time.timestamp())}:F>\n* **Reason:** {reason}",
            color=0x2b2d31)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        await ctx.send(f"**<:Tick:1140286044114268242> {ctx.author.display_name}**, I've sent the LOA request.", ephemeral=True)
        view = Confirm()
        data = loachannel.find_one({'guild_id': ctx.guild.id})
        if data:
            channel_id = data['channel_id']
            channel = self.client.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed, view=view)
                print(f"LOA Request in {ctx.guild.name}")
            else:
                await ctx.send(f"{ctx.author.display_name}, I don't have permission to view this channel.")
        else:
            await ctx.author.send(f"{Warning} {ctx.author.display_name}, the LOA channel is not set up. `/config`")        
        await view.wait()
        if view.value:
            self.pizza.execute(
            "INSERT INTO loa (guild_id, user_id, start_time, end_time, reason) VALUES (?, ?, ?, ?, ?)",
            (ctx.guild.id, ctx.author.id, start_time, end_time, reason))

            self.connection.commit()            
            await ctx.author.send(f"<:Arrow:1115743130461933599>Your LOA Request at **{ctx.guild.name}** has been accepted.")
            print(f"LOA Request Accepted in {ctx.guild.name}")
    



        elif view.cancel:
            await ctx.author.send(f"<:Arrow:1115743130461933599>Your LOA at {ctx.guild.name} has been denied.")




   
    @loa.command(name="manage", description="Manage a users LOA")
    async def manage_loa(self, ctx, user: discord.Member):
        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return             
        guild_id = ctx.guild.id
        self.pizza.execute("SELECT * FROM loa WHERE guild_id=? AND user_id=?", (guild_id, user.id))
        loa = self.pizza.fetchone()

        if not loa:
            await ctx.send(f"<:X_:1140286086883586150> **{ctx.author.display_name}**, this user isn't on LOA.")
            return        

        id, guild_id, user_id, start_time, end_time, reason = loa
        user = await self.client.fetch_user(user_id)
            
        start = datetime.datetime.fromisoformat(start_time).astimezone(pytz.timezone('Europe/London'))
        end = datetime.datetime.fromisoformat(end_time).astimezone(pytz.timezone('Europe/London'))
        duration = end - start
        view = Manage(ctx.author.id)
        embed = discord.Embed(title=f"**{user.display_name}**", color=0x2b2d31, description=f"* **User:** {user.mention}\n* **Start Date**: <t:{int(start.timestamp())}:F>\n* **End Date:** <t:{int(end.timestamp())}:F>\n* **Reason:** {reason}")   
        embed.set_thumbnail(url=user.avatar.url)

        await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.value:        
          self.pizza.execute("DELETE FROM loa WHERE id = ?", (loa[0],))
          self.connection.commit()          
          await user.send(f"<:Arrow:1115743130461933599>**{user.display_name}**, your LOA has been force ended.")
          guild = ctx.guild  
    






    @tasks.loop(seconds=10)
    async def check_loa_status(self):
     current_time = datetime.datetime.now(datetime.timezone.utc)  
     self.pizza.execute("SELECT id, user_id, end_time FROM loa")
     loa_requests = self.pizza.fetchall()

     for request in loa_requests:
        request_id, user_id, end_time_str = request
        end_time = datetime.datetime.fromisoformat(end_time_str)

        if current_time >= end_time:
            user = self.client.get_user(user_id)
            if user:
                await user.send(f"<:Arrow:1115743130461933599>Your **LOA** has ended.")
            self.pizza.execute("DELETE FROM loa WHERE id = ?", (request_id,))
            self.connection.commit()



    @check_loa_status.before_loop
    async def before_check_loa_status(self):
        await self.client.wait_until_ready()

    @check_loa_status.before_loop
    async def before_check_loa_status(self):
        await self.client.wait_until_ready()


    @loa_view.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, you don't have permission to view loa's.\n<:Arrow:1115743130461933599>**Required:** ``Manage Messages``") 

    @loa_request.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, you don't have permission to request loa's.\n<:Arrow:1115743130461933599>**Required:** ``Manage Messages``")             

    @manage_loa.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, you don't have permission to manage loa's.\n<:Arrow:1115743130461933599>**Required:** ``Manage Roles``")              



class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green, custom_id='persistent_view:confirm', emoji="<:Tick:1140286044114268242>")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        self.value = True
        await interaction.response.edit_message(content=f"<:Tick:1140286044114268242> **{interaction.user.display_name}**, I've accepted the LOA", view=None)
        self.stop()


    @discord.ui.button(label='Deny', style=discord.ButtonStyle.red, custom_id='persistent_view:cancel', emoji="<:X_:1140286086883586150>")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"<:Tick:1140286044114268242> **{interaction.user.display_name}** I've denied the LOA.", view=None)    
        self.value = False
        self.stop()                

class Manage(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.value = None

    @discord.ui.button(label='End', style=discord.ButtonStyle.blurple, custom_id='persistent_view:confirm')
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            embed = discord.Embed(description=f"**{interaction.user.display_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.value = True
        await interaction.response.edit_message(content=f"<:Tick:1140286044114268242> **{interaction.user.display_name}**, I've ended the LOA", view=None)
        self.stop()



async def setup(client: commands.Bot) -> None:
    await client.add_cog(LOA(client))        