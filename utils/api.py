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
    
    async def POST_google(self, auth: str, Request: Request):
        return Request

    async def get_total_users(self):
        total_members = sum(guild.member_count for guild in self.client.guilds)
        return total_members

    async def GET_infraction(self, auth: str, server: int, id: str):
        if not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Key"
            )

        infraction = await collection.find_one(
            {"random_string": id, "guild_id": server}
        )
        if not infraction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Infraction not found"
            )

        guild = self.client.get_guild(server)
        if not guild:
            return {"error": 1000, "message": "Server not found"}
        if not guild.chunked:
            await guild.chunk()

        staff = guild.get_member(infraction.get("staff"))
        if not staff:
            try:
                staff = await guild.fetch_member(infraction.get("staff"))
            except (discord.Forbidden, discord.NotFound):
                return {"error": 1001, "message": "Staff not found"}

        management = guild.get_member(infraction.get("management"))
        if not management:
            try:
                management = await guild.fetch_member(infraction.get("management"))
            except (discord.Forbidden, discord.NotFound):
                return {
                    "error": 1002,
                    "message": "Management not found",
                }

        return {
            "id": id,
            "created": (
                infraction.get("timestamp") if infraction.get("timestamp") else None
            ),
            "user": {
                "id": str(staff.id),
                "name": staff.name,
                "avatar": (
                    staff.display_avatar.url
                    if hasattr(staff.display_avatar, "url")
                    else None
                ),
            },
            "author": {
                "id": str(management.id),
                "name": management.name,
                "avatar": (
                    management.display_avatar.url
                    if hasattr(management.display_avatar, "url")
                    else None
                ),
            },
            "action": {
                "type": infraction.get("action"),
                "details": infraction.get("reason"),
                "evidence": infraction.get("notes"),
            },
            "status": (
                "active"
                if not infraction.get("expired")
                else ("expired" if not infraction.get("voided") else "")
            ),
        }

    async def GET_permissions(self, auth: str, server: int, user: int):
        if not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Key"
            )

        guild = self.client.get_guild(server)
        if not guild:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
            )
        if not guild.chunked:
            await guild.chunk()
        member = guild.get_member(user)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        perms = await isAdmin(guild, member)
        return {
            "status": "success",
            "isAdmin": perms
            or member.guild_permissions.administrator
            or member.guild_permissions.manage_guild,
            "isStaff": await isStaff(guild, member)
            or member.guild_permissions.administrator
            or member.guild_permissions.manage_guild,
            "isDashboardUser": member.guild_permissions.administrator
            or member.guild_permissions.manage_guild,
        }

    async def DELETE_delinfraction(self, auth: str, server: int, id: str):
        if not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Key"
            )

        if not self.HandleRatelimits(auth):
            return

        await collection.delete_one({"random_string": id, "guild_id": server})
        return {"status": "success"}

    async def GET_infractions(self, auth: str, server: int):
        if not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Key"
            )

        infractions = await collection.find({"guild_id": server}).to_list(length=750)
        if not infractions:
            return []

        guild = self.client.get_guild(server)
        if not guild:
            return []

        Infractions = []
        if not guild.chunked:
            await guild.chunk()
        for infraction in infractions:
            staff = guild.get_member(infraction.get("staff"))
            management = guild.get_member(infraction.get("management"))
            if not staff or not management:
                continue
            Infractions.append(
                {
                    "id": infraction.get("random_string"),
                    "created": (
                        infraction.get("timestamp")
                        if infraction.get("timestamp")
                        else None
                    ),
                    "user": {
                        "id": str(staff.id),
                        "name": staff.name,
                        "avatar": staff.display_avatar.url,
                    },
                    "author": {
                        "id": str(management.id),
                        "name": management.name,
                        "avatar": management.display_avatar.url,
                    },
                    "action": {
                        "type": infraction.get("action"),
                        "details": infraction.get("reason"),
                        "evidence": infraction.get("notes"),
                    },
                    "status": (
                        "active"
                        if not infraction.get("expired")
                        else ("expired" if not infraction.get("voided") else "")
                    ),
                }
            )
        if Infractions:
            Infractions.reverse()
        return Infractions

    async def POST_UpdateInfraction(self, auth: str, server: int, request: Request):
        if not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Key"
            )
        try:
            body = await request.json()
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON"
            )

        guild = self.client.get_guild(server)
        if not guild:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
            )

        update_fields = {}

        if body.get("User") and body.get("User").get("id"):
            update_fields["staff"] = int(body.get("User").get("id"))
        if body.get("Author") and body.get("Author").get("id"):
            update_fields["management"] = int(body.get("Author").get("id"))
        if body.get("action") and body.get("action").get("type"):
            update_fields["action"] = body.get("action").get("type")
        if body.get("action") and body.get("action").get("details"):
            update_fields["reason"] = body.get("action").get("details")
        if body.get("action") and body.get("action").get("evidence"):
            update_fields["notes"] = body.get("action").get("evidence")
        else:
            update_fields["notes"] = "`N/A`"

        update_query = {"random_string": body.get("id"), "guild_id": guild.id}

        result = await collection.update_one(
            update_query,
            {"$set": update_fields},
            upsert=True,
        )
        resulted = await collection.find_one(update_query)
        self.client.dispatch("infraction_edit", resulted)

        if result.modified_count > 0:
            return {"status": "success", "message": "Infraction updated successfully"}
        else:
            return {"status": "success", "message": "No changes made"}

    async def POST_mutual_servers(self, request: Request, auth: str):
        if not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Key"
            )
        try:
            body = await request.json()
        except:
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

        return {"status": "success", "mutual": mutual}

    async def GET_config(self, auth: str, server: int, stringify: bool):
        if not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Key"
            )

        Config = await config.find_one({"_id": server})
        if not Config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
            )

        if stringify:

            def stringify_dict(d):
                if isinstance(d, dict):
                    for key, value in d.items():
                        if isinstance(value, dict):
                            stringify_dict(value)
                        elif isinstance(value, list):
                            d[key] = [
                                (
                                    str(element)
                                    if not isinstance(element, dict)
                                    else stringify_dict(element)
                                )
                                for element in value
                            ]
                        else:
                            d[key] = str(value)
                return d

            Config = stringify_dict(Config)

        return {"status": "success", "config": Config}

    async def POST_config(
        self, auth: str, server: int, request: Request, unstringify: bool
    ):
        if not await Validation(auth, server):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Key"
            )

        if not self.HandleRatelimits(auth):
            return

        try:
            body = await request.json()
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON"
            )

        guild = self.client.get_guild(server)
        if not guild:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
            )
        if unstringify:

            def unstringify_dict(d):
                if isinstance(d, dict):
                    for key, value in d.items():
                        if isinstance(value, str):
                            if value.isdigit():
                                d[key] = int(value)
                            else:
                                try:
                                    d[key] = ast.literal_eval(value)
                                except (ValueError, SyntaxError):
                                    pass
                        elif isinstance(value, list):
                            d[key] = [
                                (
                                    unstringify_dict(item)
                                    if isinstance(item, dict)
                                    else (
                                        int(item)
                                        if isinstance(item, str) and item.isdigit()
                                        else (
                                            ast.literal_eval(item)
                                            if isinstance(item, str)
                                            else item
                                        )
                                    )
                                )
                                for item in value
                            ]
                        elif isinstance(value, dict):
                            unstringify_dict(value)
                return d

            config = unstringify_dict(body)
        await config.update_one({"_id": server}, {"$set": body}, upsert=True)
        return {"status": "success"}

    async def GET_search(self, auth: str, server: int, user: int):
        if not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Key"
            )
        infractions = await collection.find(
            {"staff": user, "guild_id": server}
        ).to_list(length=None)
        if not infractions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No infractions found"
            )

        guild = self.client.get_guild(server)
        if not guild:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
            )

        Infractions = []
        if not guild.chunked:
            await guild.chunk()
        for infraction in infractions:
            staff = guild.get_member(infraction.get("staff"))
            management = guild.get_member(infraction.get("management"))
            if not staff or not management:
                continue
            Infractions.append(
                {
                    "id": infraction.get("random_string"),
                    "created": (
                        infraction.get("timestamp")
                        if infraction.get("timestamp")
                        else None
                    ),
                    "user": {
                        "id": str(staff.id),
                        "name": staff.name,
                        "avatar": staff.display_avatar.url,
                    },
                    "author": {
                        "id": str(management.id),
                        "name": management.name,
                        "avatar": management.display_avatar.url,
                    },
                    "action": {
                        "type": infraction.get("action"),
                        "details": infraction.get("reason"),
                        "evidence": infraction.get("notes"),
                    },
                    "status": (
                        "active"
                        if not infraction.get("expired")
                        else ("expired" if not infraction.get("voided") else "")
                    ),
                }
            )
        if Infractions:
            Infractions.reverse()
        return Infractions

    async def GET_types(self, auth: str, server: int):
        if not await RestrictedValidation(auth):
            raise HTTPException(status_code=400, detail="Invalid Key")

        Config = await config.find_one({"_id": server})
        if not Config:
            raise HTTPException(status_code=404, detail="Server not found")

        Types = Config.get("Infraction", {}).get("types", [])
        return {"status": "success", "types": Types}

    async def POST_infract(self, auth: str, server: int, request: Request):
        if not await RestrictedValidation(auth):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Key"
            )

        if not self.HandleRatelimits(auth):
            return

        try:
            body = await request.json()
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON"
            )

        guild = self.client.get_guild(server)
        if not guild:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
            )

        try:
            user = await guild.fetch_member(body.get("User"))
        except (discord.NotFound, discord.HTTPException):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        reason = body.get("Reason")
        type = body.get("Type")
        Author = body.get("Author")
        TypeActions = await infractiontypeactions.find_one(
            {"guild_id": server, "name": type}
        )
        Config = await config.find_one({"_id": server})

        if Config is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Bot isn't setup",
            )

        if Config.get("Infraction", None) is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Infraction module isn't setup.",
            )

        if not reason or not type or not Author:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing reason, type, or Author",
            )

        if Config.get("Infraction", {}).get("channel") is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Infraction channel not set",
            )

        try:
            channel = await self.client.fetch_channel(
                int(Config.get("Infraction", {}).get("channel"))
            )
        except (discord.Forbidden, discord.NotFound):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Could not find channel"
            )

        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Could not find channel"
            )

        client = await guild.fetch_member(self.client.user.id)
        if (
            channel.permissions_for(client).send_messages is False
            or channel.permissions_for(client).view_channel is None
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bot does not have permissions to send messages in this channel",
            )

        random_string = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=10)
        )

        InfractionResult = await collection.insert_one(
            {
                "guild_id": guild.id,
                "staff": user.id,
                "management": Author,
                "action": type,
                "reason": reason,
                "notes": body.get("notes") if body.get("notes") else "`N/A`",
                "random_string": random_string,
                "timestamp": datetime.now(),
            }
        )

        if not InfractionResult.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not insert infraction",
            )

        self.client.dispatch(
            "infraction", InfractionResult.inserted_id, Config, TypeActions
        )

        return {"status": "success", "infraction": random_string}

    async def GET_TicketQuota(
        self, auth: str, server: int, discord_id: int, time: str = None
    ):
        from utils.format import strtotime

        if not await Validation(auth, server):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Key"
            )

        if time:
            Time: datetime = await strtotime(time, back=True)
            if not Time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timeframe"
                )

            TicketQuota = (
                await self.client.db["Tickets"]
                .find(
                    {
                        "GuildID": server,
                        "claimed.claimer": discord_id,
                        "opened": {"$gte": Time.timestamp()},
                    }
                )
                .to_list(length=None)
            )
        else:
            TicketQuotaVar = await self.client.db["Ticket Quota"].find_one(
                {"GuildID": server, "UserID": discord_id}
            )
            TicketQuota = TicketQuotaVar if TicketQuotaVar else {}

        guild = self.client.get_guild(server)
        if not guild:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
            )

        member = guild.get_member(discord_id)
        if not member:
            try:
                member = await guild.fetch_member(discord_id)
            except (discord.Forbidden, discord.NotFound):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

        if not await check_admin_and_staff(guild, member):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the required permissions",
            )

        ClaimedTickets = (
            len(TicketQuota) if time else TicketQuota.get("ClaimedTickets", 0)
        )

        return {
            "status": "success",
            "ClaimedTickets": ClaimedTickets,
            "OnLOA": bool(
                await self.client.db["loa"].find_one(
                    {"user": member.id, "guild_id": server, "active": True}
                )
            ),
            "user": {
                "id": str(member.id),
                "name": member.name,
                "display_name": member.display_name,
                "avatar": member.display_avatar.url if member.display_avatar else None,
            },
        }

    def HandleRatelimits(self, auth: str):
        if auth in self.ratelimits:
            if time.time() < self.ratelimits[auth]:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limited"
                )
        self.ratelimits[auth] = time.time() + 3
        return True

    async def POST_ResetQuota(self, auth: str, server: int):
        if not await Validation(auth, server):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Key"
            )
        if not self.HandleRatelimits(auth):
            return
        Result1 = await self.client.db["Ticket Quota"].update_many(
            {"GuildID": server}, {"$set": {"ClaimedTickets": 0}}
        )
        Result2 = await self.client.dbq["messages"].update_many(
            {"guild_id": server}, {"$set": {"message_count": 0}}
        )
        if not Result1.modified_count and not Result2.modified_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No quotas found"
            )

        return {
            "status": "success",
            "modified": Result1.modified_count + Result2.modified_count,
        }

    async def GET_TicketLeaderboard(self, auth: str, server: int, time: str = None):
        from utils.format import strtotime

        if not await Validation(auth, server):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Key"
            )

        if not self.HandleRatelimits(auth):
            return

        if time:
            Time: datetime = await strtotime(time, back=True)
            if not Time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timeframe"
                )

            TicketQuotas = (
                await self.client.db["Tickets"]
                .find({"GuildID": server, "opened": {"$gte": Time.timestamp()}})
                .to_list(length=None)
            )
        else:
            TicketQuotas = (
                await self.client.db["Ticket Quota"]
                .find({"GuildID": server})
                .to_list(length=None)
            )

        if not TicketQuotas:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No tickets found"
            )

        guild = self.client.get_guild(server)
        if not guild:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
            )

        leaderboard_data = {}

        for ticket in TicketQuotas:
            if time:
                claimer_id = ticket.get("claimed", {}).get("claimer")
            else:
                claimer_id = ticket.get("UserID")

            if not claimer_id:
                continue

            if claimer_id not in leaderboard_data:
                leaderboard_data[claimer_id] = 0

            leaderboard_data[claimer_id] += (
                ticket.get("ClaimedTickets", 1) if not time else 1
            )

        leaderboard = []

        for user_id, claimed_count in leaderboard_data.items():
            member = guild.get_member(int(user_id))
            if not member:
                try:
                    member = await guild.fetch_member(int(user_id))
                except (discord.Forbidden, discord.NotFound):
                    continue

            if not await check_admin_and_staff(guild, member):
                continue

            leaderboard.append(
                {
                    "username": member.name,
                    "display": member.display_name,
                    "id": member.id,
                    "ClaimedTickets": claimed_count,
                    "OnLOA": bool(
                        await self.client.db["loa"].find_one(
                            {"user": member.id, "guild_id": server, "active": True}
                        )
                    ),
                }
            )

        leaderboard.sort(key=lambda x: x["ClaimedTickets"], reverse=True)

        return {"status": "success", "leaderboard": leaderboard}

    async def GET_leaderboard(self, auth: str, server: int):
        if not await Validation(auth, server):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Key"
            )

        if not self.HandleRatelimits(auth):
            return

        Leaderboard = []
        Users = (
            await Messages.find({"guild_id": server})
            .sort("message_count", pymongo.DESCENDING)
            .to_list(length=250)
        )

        if not await ModuleCheck(server, "Quota"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quota module is disabled",
            )

        if not Users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No users found"
            )

        guild = self.client.get_guild(server)
        if not guild:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
            )

        for user in Users:
            try:
                member = guild.get_member(user.get("user_id"))
                if not member:
                    try:
                        member = await guild.fetch_member(user.get("user_id"))
                    except (discord.Forbidden, discord.NotFound):
                        continue
                if not await check_admin_and_staff(guild, member):
                    continue
                if member is None:
                    continue
                Leaderboard.append(
                    {
                        "username": member.name,
                        "display": member.display_name,
                        "id": member.id,
                        "messages": user.get("message_count"),
                        "OnLOA": bool(
                            await self.client.db["loa"].find_one(
                                {"user": member.id, "guild_id": server, "active": True}
                            )
                        ),
                    }
                )
            except Exception as e:
                print(e)

        return {"status": "success", "leaderboard": Leaderboard}

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
