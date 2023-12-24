import discord
import platform
import sys
sys.dont_write_bytecode = True
import discord.ext
from discord.ext import commands
from urllib.parse import quote_plus
from discord import app_commands
import discord
import datetime
from discord.ext import commands, tasks
from typing import Optional
import Paginator
import sentry_sdk
import asyncio
from Cogs.Modules.loa import *
import os
from dotenv import load_dotenv
from jishaku import Jishaku
import jishaku
from Cogs.Modules.astro import * 
from Cogs.Modules.reports import ReportPanel
from Cogs.Modules.reports import ActionsPanel
from Cogs.Modules.suggestions import *
from motor.motor_asyncio import AsyncIOMotorClient
import time
import axiom
from Cogs.Modules.loa import Confirm
load_dotenv()
axiomkey = os.getenv('AXIOM_KEY')
axiomorg = os.getenv('AXIOM_ORG')
PREFIX = os.getenv('PREFIX')
TOKEN = os.getenv('TOKEN')
STATUS = os.getenv('STATUS')
MONGO_URL = os.getenv('MONGO_URL')
SENTRY_URL = os.getenv('SENTRY_URL')
axiomcl = axiom.Client(axiomkey, axiomorg)

sentry_sdk.init(
    dsn=SENTRY_URL,

    traces_sample_rate=1.0,

   profiles_sample_rate=1.0,
)

class client(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix=commands.when_mentioned_or(PREFIX), intents=intents)
        self.client = client
        self.cogslist = [
        'Cogs.Modules.astro',
        'Cogs.Modules.suggestions',
        'Cogs.Modules.loa',    
        'Cogs.Modules.utility',
        'Cogs.Modules.botinfo',
        'Cogs.Modules.tags',
        'Cogs.Modules.suspension',
        'Cogs.Modules.stafflist',
        'Cogs.Modules.stafffeedback',
        'Cogs.Modules.reports',
        'Cogs.Modules.quota',
        'Cogs.Modules.promotions',
        'Cogs.Modules.infractions',
        'Cogs.Modules.partnerships',
        'Cogs.Modules.modmail',
        'Cogs.Modules.forumutils',
        'Cogs.Modules.consent',
        'Cogs.Modules.applicationresults',
        'Cogs.Modules.adminpanel',
        'Cogs.Configuration.Configuration',
        'Cogs.Events.AstroSupport.aon_thread_create',
        'Cogs.Events.AstroSupport.guilds',
        'Cogs.Events.AstroSupport.webhookguilds',        
        'Cogs.Events.AstroSupport.welcome',
        'Cogs.Events.messagevent',
        'Cogs.Events.modmailevent',
        'Cogs.Events.on_thread_create',
        'Cogs.Events.connectionrolesevent',
        'Cogs.Modules.connectionroles'
        
        ]



    async def load_jishaku(self):
        await self.wait_until_ready()
        await self.load_extension('jishaku')        
        print("Jishaku Loaded")
        axiomcl.ingest_events(
            dataset="logs",
            events=[
                {"type": "log", "event": f"Loaded Jishaku"},
            ])
        print("Sent 1 event to Axiom")


    async def setup_hook(self):
        self.loop.create_task(self.load_jishaku()) 
        self.add_view(Helpdesk())
        self.add_view(SuggestionView())
        self.add_view(ReportPanel())
        self.add_view(Confirm())



        for ext in self.cogslist:
            await self.load_extension(ext)
            print(f"{ext} loaded")
            axiomcl.ingest_events(
                dataset="logs",
                events=[
                    {"type": "log", "event": f"Loaded cog {ext}"},
                ])
            print("Sent 1 event to Axiom")


    async def on_ready(self):
        prfx = (time.strftime("%H:%M:%S GMT", time.gmtime()))
        print(prfx + " Logged in as " + self.user.name)
        print(prfx + " Bot ID " + str(self.user.id))
        print(prfx + " Discord Version " +  discord.__version__)
        print(prfx + " Python Version " + str(platform.python_version()))
        synced = await self.tree.sync()
        print(prfx + " Slash CMDs Synced " + str(len(synced)) + " Commands")
        print(prfx + " Bot is in " + str(len(self.guilds)) + " servers")
        axiomcl.ingest_events(
            dataset="logs",
            events=[
                {"type": "log", "event": "Logged in as: " + self.user.name},
                {"type": "log", "event": "User ID: " + str(self.user.id)},
                {"type": "log", "event": "Discord Version: " + discord.__version__},
                {"type": "log", "event": "Python Version: " + str(platform.python_version())},
                {"type": "log", "event": "Synced " + str(len(synced)) + " commands."},
                {"type": "log", "event": "Found " + str(len(self.guilds)) + " servers."},
                    ])
        print("Sent 6 events to Axiom")
        update_channel_name.start()

    async def on_connect(self):
        activity2 = discord.CustomActivity(name=f"{STATUS}")
        if STATUS:
            await self.change_presence(activity=activity2)
            axiomcl.ingest_events(
                dataset="logs",
                events=[
                    {"type": "log", "event": f"Set status to {STATUS}"},
                ])
            print("Sent 1 event to Axiom")
        else:
            print("STATUS not defined in .env, bot will not set a custom status.")
            axiomcl.ingest_events(
                dataset="logs",
                events=[
                    {"type": "warn", "event": f"No status defined in .env."},
                ])
            print("Sent 1 event to Axiom")
        

    async def on_disconnect(self):
        print("Disconnected from Discord Gateway!")


    async def is_owner(self, user: discord.User):
        if user.id in [
            795743076520820776



        ]:
            return True

        return await super().is_owner(user)


client = client()

@tasks.loop(seconds=300)  
async def update_channel_name():
    guild_count = len(client.guilds)
    channel_id = 1131245978704420964 
    channel = client.get_channel(channel_id)
    if channel:
        await channel.edit(name=f'{guild_count} Guilds | {len(client.users)} Users')
        axiomcl.ingest_events(
            dataset="logs",
            events=[
                {"type": "log","event": f"Found {guild_count} guilds and {len(client.users)} Users."},
            ])
        print("Sent 1 event to Axiom")
    else:
        print(f'Channel with ID {channel_id} not found.')
        axiomcl.ingest_events(
            dataset="logs",
            events=[
                {"type": "warn","event": f"Could not find {channel_id} when starting."},
            ])
        print("Sent 1 event to Axiom")


axiomcl.ingest_events(
    dataset="logs",
    events=[
        {"type": "log", "event": "Starting client"},
    ])
print("Sent 1 event to Axiom")
client.run(TOKEN)