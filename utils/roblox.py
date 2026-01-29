import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
import discord
import os
from discord.ext import commands
import time
import logging

logger = logging.getLogger(__name__)

MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["astro"]
infractions = db["infractions"]
Suggestions = db["suggestions"]
loa_collection = db["loa"]
Tokens = db["integrations"]
PendingUsers = db["Pending"]
config = db["Config"]


async def GetValidToken(user: discord.User = None, server: int = None):
    if user:
        user_result = await Tokens.find_one({"discord_id": str(user.id)})
    else:
        user_result = await Tokens.find_one({"server": str(server)})

    if not user_result:
        logger.debug("[GetValidToken] No token found.")
        return None

    token = user_result.get("access_token")
    token_expiration = user_result.get("token_expiration")
    if not token or not token_expiration or time.time() > token_expiration:
        logger.debug("[Oauth Refresh] Token expired, refreshing...")
        if await RefreshToken(user, server) != 0:
            logger.debug("[Oauth Refresh] Token refresh failed.")
            return None

        user_result = (
            await Tokens.find_one({"discord_id": str(user.id)})
            if user
            else await Tokens.find_one({"server": str(server)})
        )
        token = user_result.get("access_token")

    return token


async def Fallback(user: discord.User):
    url = f"https://api.blox.link/v4/public/discord-to-roblox/{user.id}"
    headers = {"Authorization": os.getenv("bloxlink")}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                logger.info("[Fallback] Successfully retrieved Bloxlink data.")
                return data.get("resolved")
    return None


async def GetUser(user: discord.User):
    token = await GetValidToken(user=user)
    user_info = None
    if (token):
        user_info = await GetInfo(token)

    if not user_info:
        logger.info("[Unknown Token] Falling back to Bloxlink.")
        user_info = await Fallback(user)

    return user_info


async def GetInfo(token: str = None):
    if not token:
        return None
    url = "https://apis.roblox.com/oauth/v1/userinfo"
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.json()


async def GetGroup2(group: int, user: discord.User):
    result = await Tokens.find_one({"discord_id": str(user.id)})
    if not result:
        logger.debug("[GetGroup] No token found in DB.")
        return None

    token = await GetValidToken(user=user)
    url = f"https://apis.roblox.com/cloud/v2/groups/{group}"
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                logger.info("[GetGroup2] Successfully retrieved group data.")
                return await response.json()
            else:
                logger.error(
                    f"[GetGroup2] Failed to fetch group data. Status: {response.status}"
                )
                return None


async def GetGroup(server):
    logger.debug(f"[GetGroup] Fetching token for server {server}")

    result = await Tokens.find_one({"server": str(server)})
    if not result:
        logger.debug("[GetGroup] No token found in DB.")
        return None

    token = await GetValidToken(server=server)

    if not token:
        logger.debug("[GetGroup] Failed to retrieve valid token.")
        return None

    group = result.get("group")
    if not group:
        logger.debug("[GetGroup] No group ID found.")
        return None

    url = f"https://apis.roblox.com/cloud/v2/groups/{group}"
    headers = {"Authorization": f"Bearer {token}"}

    logger.debug(f"[GetGroup] Making request to {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                logger.info("[GetGroup] Successfully retrieved group data.")
                return await response.json()
            else:
                logger.error(
                    f"[GetGroup] Failed to fetch group data. Status: {response.status}"
                )
                return None


async def RefreshToken(user: discord.User = None, server=None):
    result = (
        await Tokens.find_one({"discord_id": str(user.id)})
        if user
        else await Tokens.find_one({"server": str(server)})
    )

    if not result:
        logger.debug("[RefreshToken] No token found in DB.")
        return 1

    refresh_token = result.get("refresh_token")
    if not refresh_token:
        logger.debug("[RefreshToken] No refresh token available.")
        return 2

    token_expiration = result.get("token_expiration")

    if token_expiration and time.time() < token_expiration:
        return 0

    url = "https://apis.roblox.com/oauth/v1/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            if response.status != 200:
                logger.error(
                    f"[RefreshToken] Refresh failed: {response.status} {await response.json()}"
                )
                return 3

            New = await response.json()
            expires_in = New.get("expires_in", 899)

            logger.info(
                f"[RefreshToken] Token refreshed. New Expiration: {time.time() + expires_in}"
            )

            await Tokens.update_one(
                {"discord_id": str(user.id)} if user else {"server": str(server)},
                {
                    "$set": {
                        "access_token": New.get("access_token"),
                        "refresh_token": New.get("refresh_token"),
                        "token_expiration": time.time() + expires_in,
                    }
                },
            )
            return 0


# GET /cloud/v2/groups/{group_id}/join-requests filter="user == 'users/{roblox_id}'"
async def GetRequest(group_id: int, roblox_id: int, user: discord.User):
    token = await GetValidToken(user=user)
    if not token:
        logger.debug("[GetRequest] No valid token found.")
        return None

    url = f"https://apis.roblox.com/cloud/v2/groups/{group_id}/join-requests?filter=user == 'users/{roblox_id}'"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                logger.info("[GetRequest] Successfully retrieved join request data.")
                return await response.json()
            else:
                logger.error(
                    f"[GetRequest] Failed to fetch join request data. Status: {response.status}"
                )
                return None


async def GetRequests(interaction: discord.Interaction):
    token = await GetValidToken(user=interaction.user)
    if not token:
        logger.debug("[GetRequests] No valid token found.")
        return None
    result = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not result.get("groups"):
        return 2

    group = result.get("groups", {}).get("id", None) if result else None
    if not group:
        return 2
    url = f"https://apis.roblox.com/cloud/v2/groups/{group}/join-requests"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                logger.info("[GetRequests] Successfully retrieved join requests.")
                resp = await response.json()

                return resp.get("groupJoinRequests", None)
            else:
                logger.error(await response.json())
                logger.error(
                    f"[GetRequests] Failed to fetch join requests. Status: {response.status}"
                )
                return response.status


# POST /cloud/v2/groups/{group_id}/join-requests/{join_request_id}:decline
async def RejectRequest(group_id: int, join_request_id: int, user: discord.User):
    token = await GetValidToken(user=user)
    if not token:
        logger.debug("[RejectRequest] No valid token found.")
        return None

    url = f"https://apis.roblox.com/cloud/v2/groups/{str(group_id)}/join-requests/{str(join_request_id)}:decline"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data='{}') as response:
            if response.status == 200:
                logger.info("[AcceptRequest] Successfully accepted join request.")
                return True
            else:
                logger.error(f"[AcceptRequest] Failed to accept join request. Status: {response.status}")
                logger.error(await response.json())  
                return None


# POST /cloud/v2/groups/{group_id}/join-requests/{join_request_id}:accept
async def AcceptRequest(group_id: int, join_request_id: int, user: discord.User):
    token = await GetValidToken(user=user)
    if not token:
        logger.debug("[AcceptRequest] No valid token found.")
        return None
    logger.debug(join_request_id)
    logger.debug(group_id)

    url = f"https://apis.roblox.com/cloud/v2/groups/{str(group_id)}/join-requests/{str(join_request_id)}:accept"
    logger.debug(url)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data='{}') as response:
            if response.status == 200:
                logger.info("[AcceptRequest] Successfully accepted join request.")
                return True
            else:
                logger.error(f"[AcceptRequest] Failed to accept join request. Status: {response.status}")
                logger.error(await response.json())  
                return None



async def UpdateMembership(
    role,
    author: discord.User,
    config: dict,
    user: discord.User = None,
    roblox_id: int = None,
):
    result = await Tokens.find_one({"discord_id": str(author.id)})
    if not result:
        logger.debug("[UpdateMembership] No token found for author.")
        return 0

    token = await GetValidToken(user=author)
    if not token:
        logger.debug("[UpdateMembership] No access token found.")
        return 2

    if user:
        roblox_result = await GetUser(user)
        if not roblox_result:
            logger.debug("[UpdateMembership] No Roblox user info found.")
            return
        roblox_id = (
            roblox_result.get("roblox", {}).get("id")
            if roblox_result.get("roblox")
            else roblox_result.get("sub")
        )
        name = (
            roblox_result.get("roblox", {}).get("name")
            if roblox_result.get("roblox")
            else roblox_result.get("preferred_username")
        )
    else:
        name = "Unknown"

    if not roblox_id:
        logger.debug("[UpdateMembership] No Roblox ID provided.")
        return None

    if not config.get("groups"):
        logger.debug("[UpdateMembership] No group config found.")
        return None
    if not config.get("groups", {}).get("id", None):
        logger.debug("[UpdateMembership] No group ID found in config.")
        return None

    url = f"https://apis.roblox.com/cloud/v2/groups/{config.get('groups', {}).get('id', None)}/memberships/{str(roblox_id)}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"role": role}

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=data) as response:
            response_data = await response.json()
            logger.debug(f"[UpdateMembership] Response: {response_data}")
            if response.ok:
                logger.info(
                    f"[Updated Membership] {name} role has successfully been changed."
                )
                return 200
            else:
                logger.error(
                    f"[UpdateMembership] Failed to update role. Status: {response.status}"
                )
                return response.status


# /v1/users
async def FetchUsersByID(ids):
    url = "https://users.roblox.com/v1/users"
    headers = {"Content-Type": "application/json"}
    data = {"userIds": ids if isinstance(ids, list) else [ids]}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()
                if response_data.get("data"):
                    return response_data["data"]
                else:
                    logger.warning("[FetchRobloxUser] No user data found.")
                    return None
            else:
                logger.error(
                    f"[FetchRobloxUser] Failed to fetch user data. Status: {response.status}"
                )
                return None


# /v1/usernames/users
async def FetchRobloxUser(roblox):
    url = "https://users.roblox.com/v1/usernames/users"
    headers = {"Content-Type": "application/json"}
    data = {"usernames": roblox if isinstance(roblox, list) else [roblox]}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()
                if response_data.get("data"):
                    return response_data["data"]
                else:
                    logger.warning("[FetchRobloxUser] No user data found.")
                    return None
            else:
                logger.error(
                    f"[FetchRobloxUser] Failed to fetch user data. Status: {response.status}"
                )
                return None


# 'https://apis.roblox.com/cloud/v2/groups/{group_id}/memberships?maxPageSize=10&pageToken={string}&filter={string}' filter = filter="user == 'users/{id}'"
async def GetGroupMembership(
    author: discord.Member, roblox: int = None, user: discord.User = None
):
    token = await GetValidToken(user=author)
    if not token:
        logger.debug("[GetGroupMembership] No valid token found.")
        return None

    group_id = config.get("groups", {}).get("id", None)
    if not group_id:
        logger.debug("[GetGroupMembership] No group ID found in config.")
        return None

    url = f"https://apis.roblox.com/cloud/v2/groups/{group_id}/memberships?filter=user == 'users/{roblox}'"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                logger.info("[GetGroupMembership] Successfully retrieved membership data.")
                return await response.json()
            else:
                logger.error(
                    f"[GetGroupMembership] Failed to fetch membership data. Status: {response.status}"
                )
                return None


async def GroupRoles(interaction: discord.Interaction):
    if isinstance(interaction, commands.Context):
        author = interaction.author
        guild = interaction.guild
        send = interaction.send
    else:
        author = interaction.user
        guild = interaction.guild
        send = interaction.response.send_message

    token = await GetValidToken(user=author)
    if not token:
        return 0

    result = await interaction.client.config.find_one({"_id": guild.id})
    if not result.get("groups"):
        return 2

    group = result.get("groups", {}).get("id", None) if result else None
    if not group:
        return 2

    url = f"https://apis.roblox.com/cloud/v2/groups/{group}/roles?maxPageSize=50"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 401:
                return 1
            return await response.json()
