import discord
from fastapi import FastAPI, APIRouter, HTTPException, Request, status
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import ast
import uvicorn
import pymongo
import random
import string
from utils.emojis import *
import time
from utils.Module import ModuleCheck
from utils.permissions import check_admin_and_staff

import pymongo
from datetime import datetime
from discord.ext import commands

MONGO_URL = os.getenv("MONGO_URL")
KEY = os.getenv("KEY")
client = AsyncIOMotorClient(MONGO_URL)
db = client["astro"]
config = db["Config"]
Keys = db["Keys"]
dbq = client["quotadb"]
Messages = dbq["messages"]
infractiontypeactions = db["infractiontypeactions"]
collection = db["infractions"]
Tickets = db["Tickets"]


async def Validation(key: str, server: int):
    doc = await Keys.find_one({"key": key, "_id": server})
    return bool(doc)


async def isAdmin(guild: discord.Guild, user: discord.Member):
    Config = await config.find_one({"_id": guild.id})
    if not Config or not Config.get("Permissions"):
        return False

    admin_role_ids = Config["Permissions"].get("adminrole", [])
    admin_role_ids = (
        admin_role_ids if isinstance(admin_role_ids, list) else [admin_role_ids]
    )

    if any(role.id in admin_role_ids for role in user.roles):
        return True
    return False


async def isStaff(guild: discord.Guild, user: discord.Member, permissions=None):
    Config = await config.find_one({"_id": guild.id})
    if not Config or not Config.get("Permissions"):
        return False

    staff_role_ids = Config["Permissions"].get("staffrole", [])
    staff_role_ids = (
        staff_role_ids if isinstance(staff_role_ids, list) else [staff_role_ids]
    )

    if any(role.id in staff_role_ids for role in user.roles):
        return True
    return False


async def RestrictedValidation(key: str):
    if key == KEY:
        return True
    else:
        return False


class APIRoutes:
    def __init__(self, client: discord.Client):
        self.client = client
        self.Uptime = datetime.now()
        self.router = APIRouter()
        self.ratelimits = {}
        for i in dir(self):
            if any(
                [i.startswith(a) for a in ("GET_", "POST_", "PATCH_", "DELETE_")]
            ) and not i.startswith("_"):
                x = i.split("_")[0]
                self.router.add_api_route(
                    f"/{i.removeprefix(x+'_')}",
                    getattr(self, i),
                    methods=[i.split("_")[0].upper()],
                )

    async def GET_shards(self):
        shards = []
        for shard_id, shard_instance in self.client.shards.items():
            shard_info = f"{shard_instance.latency * 1000:.0f} ms"
            guild_count = sum(
                1 for guild in self.client.guilds if guild.shard_id == shard_id
            )
            shards.append(
                {"id": shard_id, "latency": shard_info, "guilds": guild_count}
            )
        return shards

    async def GET_stats(self):
        return {
            "guilds": len(self.client.guilds),
            "users": await self.get_total_users(),
        }

    async def get_total_users(self):
        total_members = sum(guild.member_count for guild in self.client.guilds)
        return total_members

    def Bearer(self, request: Request):
        header = request.headers.get("Authorization")
        if header and header.lower().startswith("bearer "):
            return header[7:]
        return None

    async def GET_get_staff(self, request: Request, body: dict):
        auth = self.Bearer(request)
        if not auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )

        self.HandleRatelimits(auth)

        guildId = body.get("guildId")

        guild = self.client.get_guild(guildId)
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")

        if not guild.chunked:
            await guild.chunk()

        config = self.client.db["Config"].find_one({"_id": guild.id})
        if not config:
            return HTTPException(status_code=404, detail="Not configured.")

        staff: list[discord.Member] = set()
        staffRoles = config.get("Permissions").get("staffrole", []) + config.get(
            "Permissions"
        ).get("staffrole", [])
        for roleId in staffRoles:
            role = guild.get_role(roleId)
            if role:
                staff.update(role.members)

        serialized = set()

        for s in staff:
            serialized.add({"Username": s.name, "Avatar": s.avatar, "Id": str(s.id)})

        return {"status": "Ok", "data": serialized}

    def HandleRatelimits(self, auth: str):
        if auth in self.ratelimits:
            if time.time() < self.ratelimits[auth]:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limited"
                )
        self.ratelimits[auth] = time.time() + 3
        return True

    def GET_status(self):
        return {"status": "Connected", "uptime": self.Uptime.timestamp()}


class APICog(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client
        self.app = FastAPI()
        self.app.include_router(APIRoutes(client).router)
        self.server_task = None

    def cog_unload(self):
        if self.server_task and not self.server_task.done():
            self.server_task.cancel()

    async def cog_load(self):
        self.server_task = asyncio.create_task(self.start_server())

    async def start_server(self):
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0" if os.getenv("ENVIRONMENT") == "production" else "127.0.0.1",
            port=8000,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()

    @commands.group()
    async def api(self, ctx):
        pass

    @api.command(description="Create a new API key")
    @commands.is_owner()
    async def generate(
        self, ctx: commands.Context, server: int = None, user: discord.User = None
    ):
        if not user:
            user = ctx.author
        if not server:
            server = ctx.guild.id
        key = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        await Keys.update_one(
            {"_id": server},
            {"$set": {"key": key}},
            upsert=True,
        )
        await user.send(
            embed=discord.Embed(
                title="API Key",
                description=f"```{key}```\nThis key is unique to your server and should be kept secret.  Do not share this key with anyone.",
                color=discord.Color.dark_embed(),
            )
        )
        await ctx.send(
            f"{tick} **{ctx.author.display_name}**, I've sent your API key to your/their DMs.",
            ephemeral=True,
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(APICog(client))
