import discord
import platform
import sys
import discord.ext
from discord.ext import commands
from urllib.parse import quote_plus
from discord import app_commands
import discord
import datetime
from discord.ext import commands, tasks

from typing import Optional
import Paginator
from cogs.infractions import *
import sentry_sdk
import asyncio
from cogs.loa import *
import os
from dotenv import load_dotenv

from cogs.astro import * 

load_dotenv()
PREFIX = os.getenv('PREFIX')
TOKEN = os.getenv('TOKEN')
MONGO_URL = os.getenv('MONGO_URL')
SENTRY_URL = os.getenv('SENTRY_URL')
sentry_sdk.init(
    dsn=SENTRY_URL,

    traces_sample_rate=1.0,

    profiles_sample_rate=1.0,
)

client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
ticketconfig = db['Tickets Configuration']
tickets = db['Tickets']


class client(commands.Bot):
    def __init__(self):
        intents = discord.Intents().all()
        super().__init__(command_prefix=commands.when_mentioned_or(PREFIX), intents=intents)
        self.client = client
        self.cogslist = ["cogs.suspension", "cogs.adminpanel","cogs.partnerships","cogs.stafffeedback","cogs.loa", "cogs.moderations","cogs.astro", "cogs.modmail", "cogs.forumutils", "cogs.tags" ,"cogs.botinfo", "cogs.infractions", "cogs.configuration", "cogs.utility", "cogs.reports",  "cogs.promotions"]

    async def is_owner(self, user: discord.User):
        if user.id in [
            795743076520820776



        ]:
            return True

        return await super().is_owner(user)
        
    async def load_jishaku(self):
        await self.wait_until_ready()
        await self.load_extension('jishaku')

    async def setup_hook(self):
        self.loop.create_task(self.load_jishaku()) 
        self.add_view(Helpdesk())


        for ext in self.cogslist:
            await self.load_extension(ext)
            print(f"Cog {ext} loaded")
            
    async def on_ready(self):
        prfx = (time.strftime("%H:%M:%S GMT", time.gmtime()))
        print(prfx + " Logged in as " + self.user.name)
        print(prfx + " Bot ID " + str(self.user.id))
        print(prfx + " Discord Version " +  discord.__version__)
        print(prfx + " Python Version " + str(platform.python_version()))
        synced = await self.tree.sync()
        print(prfx + " Slash CMDs Synced " + str(len(synced)) + " Commands")
        print(prfx + " Bot is in " + str(len(self.guilds)) + " servers")
        update_channel_name.start()
        
        



    
    async def on_connect(self):
        activity2 = discord.CustomActivity(emoji="<:pending:1140623442962546699>", name = f"V2.60 | {len(client.guilds)} guilds")

        print("Connected to Discord Gateway!")
        await self.change_presence(activity=activity2)

    async def on_disconnect(self):
        print("Disconnected from Discord Gateway!")

client = client()


@client.event
async def on_guild_join(guild):
    embed = discord.Embed(title=f"Astro Birb - {guild.name}",description=f"<:Arrow:1115743130461933599>**Owner:** {guild.owner.mention}\n<:Arrow:1115743130461933599>**Guild:** {guild.name}\n<:Arrow:1115743130461933599>**Guild ID** {guild.id}\n <:Arrow:1115743130461933599>**Members:** {guild.member_count}\n<:Arrow:1115743130461933599>**Created:** <t:{guild.created_at.timestamp():.0f}:F>", color=discord.Color.blurple())
    embed.set_thumbnail(url=guild.icon)
    channel = client.get_channel(1118944466980581376)
    await channel.send(embed=embed)

@client.event
async def on_guild_remove(guild):
    embed = discord.Embed(title=f"Astro Birb - {guild.name}",description=f"<:Arrow:1115743130461933599>**Owner:** {guild.owner.mention}\n<:Arrow:1115743130461933599>**Guild:** {guild.name}\n<:Arrow:1115743130461933599>**Guild ID** {guild.id}\n <:Arrow:1115743130461933599>**Members:** {guild.member_count}\n<:Arrow:1115743130461933599>**Created:** <t:{guild.created_at.timestamp():.0f}:F>", color=discord.Color.blurple())
    embed.set_thumbnail(url=guild.icon)
    channel = client.get_channel(1150816700489535508)

    await channel.send(embed=embed)

@client.event
async def on_member_join(member):
    guild_on_join = client.get_guild(1092976553752789054)    
    if guild_on_join:
     channel = client.get_channel(1092976554541326372)
     guild = member.guild

     member_count = guild_on_join.member_count
     message = f"Welcome {member.mention} to **Astro Systems**! 👋"
     view = Welcome(member_count)
     await channel.send(message, view=view)      

@client.command()
@commands.is_owner()
async def servers(ctx):
    """Displays the name and invite of every server the bot is in"""

    embeds = []

    chunk_size = 20
    guild_chunks = [client.guilds[i:i + chunk_size] for i in range(0, len(client.guilds), chunk_size)]

    for chunk_index, guild_chunk in enumerate(guild_chunks):
        embed = discord.Embed(
            title=f"Servers List - Page {chunk_index + 1}/{len(guild_chunks)}",
            description=f"<:Arrow:1115743130461933599>**Global Users:** {len(client.users)}\n<:Arrow:1115743130461933599>**Server Count:** {len(client.guilds)}",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1116038076020563988/1118955032537219194/904101097189281892.png")

        for guild in guild_chunk:
            embed.add_field(
                name=guild.name,
                value=f"<:Arrow:1115743130461933599>**Owner:** {guild.owner.mention}\n<:Arrow:1115743130461933599>**Membercount:** {guild.member_count}",
                inline=False
            )

        embeds.append(embed)

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


@tasks.loop(seconds=300)  
async def update_channel_name():
    guild_count = len(client.guilds)
    channel_id = 1131245978704420964 

    channel = client.get_channel(channel_id)
    if channel:
        await channel.edit(name=f'| Astro Birb: {guild_count}')
    else:
        print(f'Channel with ID {channel_id} not found.')



class Welcome(discord.ui.View):
    def __init__(self, member_count):
        super().__init__()
        self.gray_button.label = member_count

    @discord.ui.button(style=discord.ButtonStyle.gray, disabled=True)
    async def gray_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Hallo")

#main MTExMzI0NTU2OTQ5MDYxNjQwMA.GV8KM5.6mdY5QBSJjXrNylBvM32mtvl-aiLmshNODo-vs
#beta MTExNzkxMDM0Mjc1MjgwMDc5OA.G63j3t.xHu-FfHNAAVSreeQlZqGYJZdwCyswxeoLi9e5g 

client.run(TOKEN)    
