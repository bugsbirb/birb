import discord
from discord.ext import commands
import sqlite3
from discord import app_commands
from typing import Optional
import Paginator
from pymongo import MongoClient
from emojis import *
mongo = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = mongo['astro']
scollection = db['staffrole']
arole = db['adminrole']
infchannel = db['infraction channel']
repchannel = db['report channel']
loachannel = db['loa channel']
promochannel = db['promo channel']

partnershipch = db['partnership channel']

class PartnershipLogging(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db_connection = sqlite3.connect('partnerships.db')
        self.db_cursor = self.db_connection.cursor()
        self.db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS partnerships (
                guild_id INTEGER,                
                invite TEXT,
                server_name TEXT,
                owner_id INTEGER
            )
        """)
        self.db_connection.commit()        


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

    def get_partnership_channel(self, guild_id):
        data = partnershipch.find_one({'guild_id': guild_id})
        if data:
            channel_id = data['channel_id']
            return self.client.get_channel(channel_id)
        return None    


    @commands.Cog.listener()
    async def on_member_remove(self, member):
     self.db_cursor.execute("SELECT invite, server_name, owner_id FROM partnerships WHERE owner_id = ?", (member.id,))
     partnership = self.db_cursor.fetchone()

     if partnership:
        invite, server_name, owner_id = partnership

        guild = member.guild


        embed = discord.Embed(
            title=f"{server_name} - Terminiated",
            description=f"* **Owner:** {member.mention}\n* **Invite:** {invite}\n* **Reason:** `@{member.display_name}` left the **server**.",
            color=0x2b2d31)
        embed.set_thumbnail(url=member.avatar.url)
        guild_id = member.guild.id
        data = partnershipch.find_one({'guild_id': guild_id})
        self.db_cursor.execute("DELETE FROM partnerships WHERE owner_id = ?", (owner_id,))
        self.db_connection.commit()
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
            await channel.send(embed=embed)
            await member.send(f"<:Arrow:1115743130461933599> Your partnership at **{guild.name}** has been **terminated** due to the representative leaving the server.")



    @commands.hybrid_group(name="partnership", invoke_without_command=True)
    async def partnership(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a subcommand.")    

    @partnership.command(name="log", description="Log a partnership which automatically logs once the partnership owner leaves.")

    @app_commands.describe(
        invite='What invite is the partnered server?',
        server_name='What is the server\'s name?',
        owner='Who is the partner representative?')
    async def partner(self, ctx, invite: str, server_name: str, owner: discord.Member):
        guild_id = ctx.guild.id
        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return  
        self.db_cursor.execute("INSERT INTO partnerships (guild_id, invite, server_name, owner_id) VALUES (?, ?, ?, ?)",
                           (guild_id, invite, server_name, owner.id))
        self.db_connection.commit()

        channel = self.get_partnership_channel(guild_id)

        if channel:
            embed = discord.Embed(
                title=f"{server_name} - Partnership Log",
                description=f"* **Owner:** {owner.mention}\n* **Invite:** {invite}",
                color=0x2b2d31)
            embed.set_thumbnail(url=owner.avatar.url)
            await channel.send(embed=embed)

            await ctx.send(f"<:Tick:1140286044114268242> **{ctx.author.display_name}**, I've logged the partnership.\n<:Arrow:1115743130461933599>**Invite:** `{invite}`\n<:Arrow:1115743130461933599>**Server:** {server_name}\n<:Arrow:1115743130461933599>**Owner:** {owner.mention}")
        else:
            await ctx.send(f"{Warning} {ctx.author.display_name}, I don't have permission to view this channel or the channel is not set up. Please run `/config`")



    @partnership.command(name="view", description="View all active partnerships")

    async def partnerships(self, ctx):
        guild_id = ctx.guild.id
        self.db_cursor.execute("SELECT invite, server_name, owner_id FROM partnerships WHERE guild_id = ?",
                           (guild_id,))
        partnerships = self.db_cursor.fetchall()
        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return  
        if not partnerships:
            await ctx.send(f"{no} **{ctx.author.display_name}**, no partnerships found.")
            return

        embeds = []
        for partnership in partnerships:
            invite, server_name, owner_id = partnership
            owner = self.client.get_user(owner_id)
            embed = discord.Embed(
                title=f"Active Partnerships",
                color=0x2b2d31,
                description=f"* **Server:** {server_name}\n* **Owner:** {owner.mention}\n* **Invite:** {invite}"
            )
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

    @partnership.command(name="terminate", description="Terminate active partnerships")

    async def revoke(self, ctx, member: discord.Member, reason: Optional[str] = None):
        if not await self.has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return          
        guild_id = ctx.guild.id

        self.db_cursor.execute("SELECT invite, server_name FROM partnerships WHERE owner_id = ? AND guild_id = ?", (member.id, guild_id))
        partnership = self.db_cursor.fetchone()

        if partnership:
            invite, server_name = partnership

            if reason:
                embed = discord.Embed(
                    title=f"{server_name} - Terminated",
                    description=f"* **Owner:** {member.mention}\n* **Invite:** {invite}\n* **Reason:** {reason}.",
                    color=0x2b2d31)
                embed.set_thumbnail(url=member.avatar.url)


                data = partnershipch.find_one({'guild_id': guild_id})
                if data:
                    channel_id = data['channel_id']
                    channel = self.client.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)
                self.db_cursor.execute("DELETE FROM partnerships WHERE owner_id = ? AND guild_id = ?", (member.id, guild_id))
                self.db_connection.commit()

                await ctx.send(f"<:Tick:1140286044114268242>**{ctx.author.display_name}**, I've terminated the partnership.")
                await member.send(f"<:SmallArrow:1140288951861649418> **{member.display_name}**, your partnership at **{ctx.guild.name}** has been terminated/revoked for **{reason}**.")
            else:
                embed = discord.Embed(
                    title=f"{server_name} - Terminated",
                    description=f"* **Owner:** {member.mention}\n* **Invite:** {invite}\n* **Reason:** N/A.",
                    color=0x2b2d31)
                embed.set_thumbnail(url=member.avatar.url)


                data = partnershipch.find_one({'guild_id': guild_id})
                if data:
                    channel_id = data['channel_id']
                    channel = self.client.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)

                self.db_cursor.execute("DELETE FROM partnerships WHERE owner_id = ? AND guild_id = ?", (member.id, guild_id))
                self.db_connection.commit()

                await ctx.send(f"<:Tick:1140286044114268242>**{ctx.author.display_name}**, I've terminated the partnership.")
                await member.send(f"<:SmallArrow:1140288951861649418> **{member.display_name}**, your partnership at **{ctx.guild.name}** has been terminated for N/A.")
        else:
            await ctx.send(f"<:X_:1140286086883586150> **{ctx.author.display_name}**, this user does not have a partnership with this guild.")




    @revoke.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, you don't have permission to terminate partnerships.\n<:Arrow:1115743130461933599>**Required:** ``manage_channels``")      

    @partner.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, you don't have permission to create partnerships.\n<:Arrow:1115743130461933599>**Required:** ``manage_channels``")                 

    @partnerships.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, you don't have permission to view partnerships.\n<:Arrow:1115743130461933599>**Required:** ``manage_channels``")                 


async def setup(client: commands.Bot) -> None:
    await client.add_cog(PartnershipLogging(client))            