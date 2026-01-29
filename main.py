from dotenv import load_dotenv

load_dotenv()


import discord
import platform
import sys
import gc
import os
import time
import logging

from discord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient

# import pymongo
from Cogs.Modules.promotions import SyncCommands
from Cogs.Events.on_suggestion import Voting as Voti

from Cogs.Modules.commands import Voting
from Cogs.Tasks.activityauto import ResetLeaderboard
from Cogs.Modules.staff import Staffview
from Cogs.Events.on_infraction_approval import CaseApproval
from Cogs.Events.on_ticket import PTicketControl
from Cogs.Tasks.qotd import *
from Cogs.Events.on_error import Tree
from Cogs.Events.modmail import ModmailClosure, Links
from Cogs.Modules.tickets import ButtonHandler

sys.dont_write_bytecode = True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

gc.enable()


PREFIX = os.getenv("PREFIX")
TOKEN = os.getenv("TOKEN")
STATUS = os.getenv("STATUS")
MONGO_URL = os.getenv("MONGO_URL")
SHARDS = os.getenv("SHARDS")


client = AsyncIOMotorClient(MONGO_URL)
# client = pymongo.AsyncMongoClient(MONGO_URL)
qdb = client["quotadb"]
db = client["astro"]
prefixdb = db["prefixes"]
qotdd = db["qotd"]
Config = db["Config"]
Views = db["Views"]
SupportVariables = db["Support Variables"]
staffdb = db["staff database"]


if not (TOKEN or MONGO_URL, PREFIX):
    print("[❌] Missing .env variables. [TOKEN, MONGO_URL]")
    sys.exit(1)

if os.getenv("REMOVE_EMOJIS", False) == "True" or environment == "custom":
    from branding import ClearEmojis

    ClearEmojis(True, os.getenv("FOLDER_PATH", "/app"))

if os.getenv("SENTRY_URL", None):
    import sentry_sdk
    from sentry_sdk.integrations.aiohttp import AioHttpIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_URL"),
        integrations=[AioHttpIntegration(), LoggingIntegration(level=logging.INFO)],
        traces_sample_rate = 0.2,
        profiles_sample_rate = 0.05
    )

    logger.info("Sentry SDK initialized")


class Client(commands.AutoShardedBot):
    def __init__(self):
        self._initialize_databases()
        self.maintenance = False
        self.maintenanceReason = ""
        self.cached_commands = {}
        intents = self._initialize_intents()
        self._initialize_super(intents)
        self.client = client
        self.cogslist = self._initialize_cogslist()
        self.Tasks = set()
        if environment != "custom":
            self.cogslist.extend(["utils.api", "utils.dokploy"])
        if os.getenv("STAFF"):
            self.cogslist.append("Cogs.Modules.Developer.admin")

    def _initialize_databases(self):
        self.db = db
        self.qdb = qdb
        self.config = Config
        self.customcommands = db["customcommands"]


    def _initialize_intents(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        return intents

    def _initialize_super(self, intents):
        if environment == "custom":
            print("Custom Branding Loaded")
            super().__init__(
                command_prefix=commands.when_mentioned_or(self.get_prefix),
                intents=intents,
                shard_count=None,
                chunk_guilds_at_startup=False,
                allowed_mentions=discord.AllowedMentions(
                    replied_user=False, everyone=False, roles=False
                ),
                tree_cls=Tree,
            )
        elif environment == "development":
            print("Development Loaded")
            super().__init__(
                command_prefix=commands.when_mentioned_or(PREFIX),
                intents=intents,
                shard_count=None,
                chunk_guilds_at_startup=os.getenv("CACHE", True),
                allowed_mentions=discord.AllowedMentions(
                    replied_user=False, everyone=False, roles=False
                ),
                tree_cls=Tree,
            )
        else:
            print("Production Loaded")
            super().__init__(
                command_prefix=commands.when_mentioned_or(PREFIX),
                intents=intents,
                chunk_guilds_at_startup=os.getenv("CACHE", False),
                allowed_mentions=discord.AllowedMentions(
                    replied_user=False, everyone=False, roles=False
                ),
                tree_cls=Tree,
            )

    def _initialize_cogslist(self):
        return [
            # Modules
            "Cogs.Modules.suggestions",
            "Cogs.Modules.leaves",
            "Cogs.Modules.suspension",
            "Cogs.Modules.feedback",
            "Cogs.Modules.connection-roles",
            "Cogs.Modules.staff",
            "Cogs.Modules.promotions",
            "Cogs.Modules.infractions",
            "Cogs.Modules.modmail",
            "Cogs.Modules.commands",
            "Cogs.Modules.data",
            "Cogs.Modules.integrations",
            "Cogs.Modules.tickets",
            # Utilities
            "Cogs.Modules.Utilities.extras",
            "Cogs.Modules.Utilities.ping",
            "Cogs.Modules.Utilities.info",
            "Cogs.Modules.Utilities.premium",
            "Cogs.Modules.Utilities.memberships",
            "Cogs.Modules.Developer.astro",
            # Configuration
            "Cogs.Configuration.Configuration",
            # Events
            "Cogs.Events.Dev.on_guild",
            "Cogs.Events.Dev.welcome",
            "Cogs.Events.quota",
            "Cogs.Events.modmail",
            "Cogs.Events.on_thread_create",
            "Cogs.Events.Dev.topgg",
            "Cogs.Events.Dev.analytics",
            "Cogs.Events.on_error",
            "Cogs.Events.autoresponse",
            "Cogs.Events.on_infraction",
            "Cogs.Events.ConnectionRoles",
            "Cogs.Events.on_promotion",
            "Cogs.Events.on_infraction_edit",
            "Cogs.Events.on_feedback",
            "Cogs.Events.on_suggestion",
            "Cogs.Events.on_suggest_update",
            "Cogs.Events.on_infraction_approval",
            "Cogs.Events.on_ticket",
            "Cogs.Events.on_infraction_log",
            "Cogs.Events.on_infraction_void",
            "Cogs.Events.on_promotion_log",
            "Cogs.Events.on_promotion_void",
            "Cogs.Events.on_leave",
            "Cogs.Events.Dev.on_shard",
            # Tasks
            "Cogs.Tasks.expiration",
            "Cogs.Tasks.leave",
            "Cogs.Tasks.staff-list",
            "Cogs.Tasks.suspension",
            "Cogs.Tasks.activityauto",
            "Cogs.Tasks.UpdateChannel",
            "Cogs.Tasks.qotd",
        ]

    async def load_jishaku(self):
        await self.wait_until_ready()
        await self.load_extension("jishaku")
        print("[🔄] Jishaku Loaded")

    async def get_prefix(self, message: discord.Message) -> tasks.List[str] | str:
        if message.guild is None:
            return "!!"
        if message.author.bot:
            return None
        prefixdb = db["prefixes"]
        prefixresult = await prefixdb.find_one({"guild_id": message.guild.id})
        if prefixresult:
            prefix = prefixresult.get("prefix", "!!")
        else:
            prefix = PREFIX
        return commands.when_mentioned_or(prefix)(self, message)

    async def setup_hook(self):
        await self._load_views()
        await self._load_cogs()
        await self.CacheCommands()

    async def _load_views(self):
        filter = {}
        if environment == "custom":
            filter["guild"] = int(guildid)
        TicketViews = await self.db["Panels"].find(filter).to_list(length=None)
        V = await Views.find(filter).to_list(length=None)
        print("[Views] Loading Any Views")
        for view in V:
            if not view:
                continue
            if view.get("type") == "staff":
                await self._load_staff_view(view)
        print("[Views] Loading Ticket Views")
        for view in TicketViews:
            await self._load_ticket_view(view)
        del TicketViews
        del V

    async def _load_staff_view(self, view):
        DbResults = await staffdb.find({"guild_id": view.get("guild")}).to_list(
            length=None
        )
        if not DbResults:
            return
        options = []
        guild = self.get_guild(int(view.get("guild")))
        if not guild:
            return
        if not guild.chunked:
            try:
                await guild.chunk()
            except (discord.HTTPException, discord.Forbidden):
                return
        for staff in DbResults:
            member = guild.get_member(staff.get("staff_id"))
            if not member:
                continue
            options.append(
                discord.SelectOption(
                    label=member.display_name,
                    value=str(member.id),
                    description=member.get("rolename"),
                    emoji="<:staff:1206248655359840326>",
                )
            )
            if len(options) >= 24:
                options.append(
                    discord.SelectOption(
                        label="View More",
                        value="more",
                        description="View more staff members",
                        emoji="<:List:1223063187063308328>",
                    )
                )
                break

        view = Staffview(options=options[:25])
        try:
            self.add_view(view, msg_id=int(view.get("MsgID")))
        except:
            return

    async def _load_ticket_view(self, view):
        view_handler = ButtonHandler()
        if view.get("type") == "multi":
            buttons = []
            if not view.get("Panels"):
                return
            for panel_name in view.get("Panels"):

                sub = await self.db["Panels"].find_one(
                    {
                        "guild": view.get("guild"),
                        "name": panel_name,
                        "type": "single",
                    }
                )
                if not sub:
                    continue
                sub_button = sub.get("Button")
                if not sub_button:
                    continue
                buttons.append(
                    {
                        "label": sub_button.get("label"),
                        "style": sub_button.get("style"),
                        "emoji": sub_button.get("emoji"),
                        "custom_id": sub_button.get("custom_id"),
                    }
                )

            if buttons:
                view_handler.add_buttons(buttons)
        else:
            single_button = view.get("Button")
            if not single_button:
                return
            view_handler.add_buttons(
                [
                    {
                        "label": single_button.get("label"),
                        "style": single_button.get("style"),
                        "emoji": single_button.get("emoji"),
                        "custom_id": single_button.get("custom_id"),
                    }
                ]
            )

        msg_id = view.get("MsgID")
        self.add_view(view_handler, message_id=int(msg_id) if msg_id else 0)

    async def _load_cogs(self):
        self.add_view(Voting())
        self.add_view(Voti())
        self.add_view(Staffview())
        self.add_view(ResetLeaderboard())
        self.add_view(ModmailClosure())
        self.add_view(Links())
        self.add_view(CaseApproval())
        self.add_view(PTicketControl())

        self.loop.create_task(self.load_jishaku())
        DoNotLoad = os.getenv("DoNotLoad", "").replace(" ", "").split(",")
        self.cogslist = [cog for cog in self.cogslist if cog and cog not in DoNotLoad]
        for ext in self.cogslist:
            try:
                await self.load_extension(ext)
                print(f"[✅] Loaded cog: {ext}")
            except Exception as e:
                print(f"[❌] Failed to load cog {ext}: {e}")

    async def GetVersion(self):
        V = await SupportVariables.find_one({"_id": 1})
        if not V:
            return "N/A"
        return V.get("version")

    async def CacheCommands(self):
        self.cached_commands = []
    

        def recursive_cache(command, parent=""):
            full_name = f"{parent} {command.name}".strip()
            self.cached_commands.append(full_name)
            if isinstance(command, discord.app_commands.Group):
                for subcommand in command.commands:
                    recursive_cache(subcommand, full_name)

        for command in self.tree.get_commands():
            recursive_cache(command)

    async def on_ready(self):
        if environment == "custom":
            await self._handle_custom_environment()
        await SyncCommands(self)
        await self._print_startup_info()
        await self._set_custom_status()
        await self._cache_enabled_servers()

    async def _handle_custom_environment(self):
        if not guildid:
            print("[❌] CUSTOM_GUILD not defined in .env")
            sys.exit(1)
        guild = None
        try:
            guild = await self.fetch_guild(guildid)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            print(f"[❌] Failed to fetch guild {guildid}")
        if guild:
            try:
                await guild.chunk(cache=False)
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                print(f"[❌] Failed to chunk guild {guild.name} ({guild.id})")
            print(f"[✅] Connected to guild {guild.name} ({guild.id})")
            try:
                await self.tree.sync()
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                print(f"[❌] Failed to sync commands")

    async def _print_startup_info(self):
        prfx = time.strftime("%H:%M:%S GMT", time.gmtime())
        prfx = f"[📖] {prfx}"
        print(prfx + " Logged in as " + self.user.name)
        print(prfx + " Bot ID " + str(self.user.id))
        print(prfx + " Discord Version " + discord.__version__)
        print(prfx + " Python Version " + str(platform.python_version()))
        print(prfx + " Bot is in " + str(len(self.guilds)) + " servers")
        try:
            await db.command("ping")
            print("[✅] successfully connected to MongoDB")
        except Exception as e:
            print(f"[❌] Failed to connect to MongoDB: {e}")
        T = "\n".join(f"- {task}" for task in self.Tasks)
        if len(self.Tasks) > 0:
            print(f"[📝] Tasks Loaded:\n{T}")

    async def _set_custom_status(self):
        activity2 = discord.CustomActivity(name=f"{STATUS}")
        if STATUS:
            await self.change_presence(activity=activity2)
        else:
            print("[⚠️] STATUS not defined in .env, bot will not set a custom status.")

    async def _cache_enabled_servers(self):
        prfx = time.strftime("%H:%M:%S GMT", time.gmtime())
        prfx = f"[📖] {prfx}"

        query = {"Modules.Modmail": True}
        if environment == "custom":
            query["_id"] = int(guildid)

        Modmail = await self.db["Config"].find(query).to_list(length=None) or []
        Enabled = (
            await self.db["Config"]
            .find({"features": {"$in": ["CACHED"]}})
            .to_list(length=None)
        ) or []

        Guilds = {int(server["_id"]) for server in Modmail + Enabled if "_id" in server}
        Guilds.update([1092976553752789054])

        cached = 0
        for ID in Guilds:
            try:
                guild = self.get_guild(ID)
                if guild:
                    await guild.chunk()
                    cached += 1
            except:
                continue

        print(prfx + f" Successfully cached {cached} servers.")

        del Modmail, Enabled, ID

    async def on_disconnect(self):
        print("[⚠️] Disconnected from Discord Gateway!")

    async def on_resumed(self):
        print("[✅] Resumed connection to Discord Gateway!")

    async def is_owner(self, user: discord.User):
        if (
            user.id in [795743076520820776]
            if not os.getenv("OWNER")
            else os.getenv("OWNER").split(",")
        ):
            return True
        return await super().is_owner(user)

    async def on_shard_ready(self, shard_id):
        print(f"[✅] Shard {shard_id} is ready.")

    async def on_shard_connect(self, shard_id):
        print(f"[✅] Shard {shard_id} connected.")

    async def on_shard_disconnect(self, shard_id):
        print(f"[⚠️] Shard {shard_id} disconnected.")


client = Client()


if __name__ == "__main__":
    client.run(TOKEN)
