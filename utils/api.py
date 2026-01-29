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

    async def GET_transcript(self, id: str, auth: str):
        if not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Key"
            )
        Result = await db["Tickets"].find_one({"_id": id})
        if not Result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
            )

        return {
            "status": "success",
            "transcript": Result.get("transcript"),
            "GuildID": str(Result.get("GuildID")),
        }

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

    async def POST_mutual_servers(self, request: Request):
        auth = self.Bearer(request)
        if not auth or not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Key"
            )
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON"
            )

        guilds = body.get("guilds")
        user = body.get("user")

        if not guilds or not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Missing guilds or user"
            )

        async def Process(GuilID):
            guild = self.client.get_guild(int(GuilID))
            if not guild:
                return None
            if not guild.chunked:
                await guild.chunk()
            member = guild.get_member(int(user))
            if not member:
                return None
            Admin = member.guild_permissions.administrator
            Manager = member.guild_permissions.manage_guild
            if not Admin and not Manager:
                return None

            return {
                "name": guild.name,
                "icon": guild.icon.url if guild.icon else None,
                "id": str(guild.id),
                "membercount": guild.member_count,
                "roles": [
                    {
                        "id": str(role.id),
                        "name": role.name,
                    }
                    for role in guild.roles
                ],
                "channels": [
                    {
                        "id": str(channel.id),
                        "name": channel.name,
                    }
                    for channel in guild.channels
                ],
                "isAdmin": member.guild_permissions.administrator,
                "isManager": (
                    guild.owner_id is not None and guild.owner_id == member.id
                )
                or await isStaff(guild, member)
                or member.guild_permissions.administrator,
            }

        tasks = [Process(GuilID) for GuilID in guilds]
        results = await asyncio.gather(*tasks)

        mutual = [result for result in results if result is not None]

        return {"status": "success", "mutuals": mutual}


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
        
    def safe_literal_eval(self, item):
        try:
            return ast.literal_eval(item)
        except (ValueError, SyntaxError):
            return item  

    def unstringify_dict(self, d):
        for key, value in d.items():
            if isinstance(value, dict):
                d[key] = self.unstringify_dict(value)
            elif isinstance(value, list):
                d[key] = [self.safe_literal_eval(v) if isinstance(v, str) else v for v in value]
            elif isinstance(value, str):
                d[key] = self.safe_literal_eval(value)
        return d

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
