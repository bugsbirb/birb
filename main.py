import discord
import platform
import sys
sys.dont_write_bytecode = True
from discord.ext import commands, tasks
import sentry_sdk
import os
from dotenv import load_dotenv
from Cogs.Modules.reports import ReportPanel
from Cogs.Modules.suggestions import SuggestionView, SuggestionManageView
import asyncio
import time
from Cogs.Modules.applicationresults import AcceptAndDeny
from Cogs.Modules.loa import Confirm
from Cogs.Modules.customcommands import Voting
from Cogs.Modules.staff import Staffview
from motor.motor_asyncio import AsyncIOMotorClient
load_dotenv()


PREFIX = os.getenv("PREFIX")
TOKEN = os.getenv("TOKEN")
STATUS = os.getenv("STATUS")
MONGO_URL = os.getenv("MONGO_URL")

sentry_sdk.init(
    dsn=os.getenv("SENTRY_URL"),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

client = AsyncIOMotorClient(MONGO_URL)
db = client["astro"]


class client(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(
            command_prefix=commands.when_mentioned_or(PREFIX), intents=intents, shard_count=1
        )
        self.client = client
        self.cogslist = [
            "Cogs.Modules.astro",
            "Cogs.Modules.suggestions",
            "Cogs.Modules.loa",
            "Cogs.Modules.utility",
            "Cogs.Modules.botinfo",
            "Cogs.Modules.tags",
            "Cogs.Modules.suspension",
            "Cogs.Modules.stafffeedback",
            "Cogs.Modules.reports",
            "Cogs.Modules.staff",
            "Cogs.Modules.promotions",
            "Cogs.Modules.infractions",
            "Cogs.Modules.partnerships",
            "Cogs.Modules.modmail",
            "Cogs.Modules.forumutils",
            "Cogs.Modules.consent",
            "Cogs.Modules.applicationresults",
            "Cogs.Modules.adminpanel",
            "Cogs.Modules.customcommands",
            "Cogs.Configuration.Configuration",
            "Cogs.Events.AstroSupport.guilds",
            "Cogs.Events.AstroSupport.webhookguilds",
            "Cogs.Events.AstroSupport.welcome",
            "Cogs.Events.messagevent",
            "Cogs.Events.modmailevent",
            "Cogs.Events.on_thread_create",
            "Cogs.Events.connectionrolesevent",
            "Cogs.Modules.connectionroles",
            "Cogs.Events.AstroSupport.blacklist",
            "Cogs.Events.AstroSupport.topgg",
            "Cogs.Events.AstroSupport.analytics",
            "Cogs.Events.welcome",
            "Cogs.Modules.datamanage",
            "Cogs.Events.on_error"

        ]

    async def load_jishaku(self):
        await self.wait_until_ready()
        await self.load_extension("jishaku")
        print("[🔄] Jishaku Loaded")

    async def setup_hook(self):
        update_channel_name.start()

        self.add_view(SuggestionView())
        self.add_view(SuggestionManageView())
        self.add_view(ReportPanel())
        self.add_view(Confirm())
        self.add_view(Voting())
        self.add_view(Staffview())
        self.add_view(AcceptAndDeny())
        
        self.loop.create_task(self.load_jishaku())

        for ext in self.cogslist:
            await self.load_extension(ext)
            print(f"[✅] {ext} loaded")

    async def on_ready(self):
        prfx = time.strftime("%H:%M:%S GMT", time.gmtime())
        prfx = f"[📖] {prfx}"
        print(prfx + " Logged in as " + self.user.name)
        print(prfx + " Bot ID " + str(self.user.id))
        print(prfx + " Discord Version " + discord.__version__)
        print(prfx + " Python Version " + str(platform.python_version()))
        print(prfx + " Bot is in " + str(len(self.guilds)) + " servers")
        try:
         await db.command("ping")
         print(f"[✅] Successfully connected to MongoDB")
        except Exception as e:
         print(f"[❌] Failed to connect to MongoDB: {e}") 



    async def on_connect(self):
        activity2 = discord.CustomActivity(name=f"{STATUS}")
        if STATUS:
            await self.change_presence(activity=activity2)

        else:
            print("[⚠️] STATUS not defined in .env, bot will not set a custom status.")

    async def on_disconnect(self):
        print("[⚠️] Disconnected from Discord Gateway!")

    async def is_owner(self, user: discord.User):
        if user.id in [795743076520820776]:
            return True

        return await super().is_owner(user)


client = client()



@tasks.loop(minutes=10)
async def update_channel_name():
    guild_count = len(client.guilds)
    channel_id = 1131245978704420964
    channel = client.get_channel(channel_id)
    if channel:
        try:
            await channel.edit(name=f"{guild_count} Guilds | {len(client.users)} Users")
        except discord.HTTPException:
            print("[⚠️] Failed to update channel name.")

    else:
        print(f"[⚠️] Channel with ID {channel_id} not found.")

if __name__ == "__main__": 
    client.run(TOKEN)
    
