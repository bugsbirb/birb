import aiohttp

import os
import logging
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

ClientID = os.getenv("PatreonClientID")
ClientSecret = os.getenv("PatreonClientSecret")

MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["astro"]
Patreon = db["Patreon"]


import aiohttp


async def RefreshToken(ClientID: str, ClientSecret: str, RefreshTokenValue: str):
    url = "https://www.patreon.com/api/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": RefreshTokenValue,
        "client_id": ClientID,
        "client_secret": ClientSecret,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async with aiohttp.ClientSession() as Session:
        async with Session.post(url, data=data, headers=headers) as Resp:
            if Resp.status != 200:
                return None
            return await Resp.json()


async def GetAccessToken():
    Doc = await Patreon.find_one({"_id": 0})
    if not Doc:
        return None

    AccessToken = Doc.get("access_token")
    RefreshTokenValue = Doc.get("refresh_token")

    url = "https://www.patreon.com/api/oauth2/v2/identity"
    headers = {"Authorization": f"Bearer {AccessToken}"}

    async with aiohttp.ClientSession() as Session:
        async with Session.get(url, headers=headers) as Resp:
            if Resp.status == 401:
                TokenData = await RefreshToken(
                    ClientID, ClientSecret, RefreshTokenValue
                )
                if not TokenData or "access_token" not in TokenData:
                    return None
                AccessToken = TokenData["access_token"]
                NewRefresh = TokenData.get("refresh_token", RefreshTokenValue)
                await Patreon.update_one(
                    {"_id": 0},
                    {
                        "$set": {
                            "access_token": AccessToken,
                            "refresh_token": NewRefresh,
                        }
                    },
                    upsert=True,
                )
            elif Resp.status != 200:
                return None
    return AccessToken


async def SubscriptionUser(UserID: int, Sub: str = "22855340", Tiers: list = None):
    AccessToken = await GetAccessToken()
    if not AccessToken:
        return

    CampaignID = await GetCampaignID(AccessToken)
    if not CampaignID:
        return

    URL = f"https://www.patreon.com/api/oauth2/v2/campaigns/{CampaignID}/members"
    Params = {
        "include": "currently_entitled_tiers,user",
        "fields[member]": "patron_status",
        "fields[user]": "social_connections",
        "page[count]": 100,
    }

    Headers = {
        "Authorization": f"Bearer {AccessToken}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as Session:
        while URL:
            async with Session.get(URL, headers=Headers, params=Params) as Resp:
                if Resp.status != 200:
                    return

                Data = await Resp.json()
                Included = Data.get("included", [])
                Users = {U["id"]: U for U in Included if U.get("type") == "user"}

                for Member in Data.get("data", []):
                    PatronStatus = Member.get("attributes", {}).get("patron_status")
                    if PatronStatus != "active_patron":
                        continue

                    UserRef = (
                        Member.get("relationships", {}).get("user", {}).get("data", {})
                    )
                    UserID_ = UserRef.get("id")
                    User = Users.get(UserID_)
                    if not User:
                        continue

                    SocialConnections = User.get("attributes", {}).get(
                        "social_connections", {}
                    )
                    DiscordInfo = SocialConnections.get("discord")
                    if not DiscordInfo:
                        continue
                    if str(DiscordInfo.get("user_id")) != str(UserID):
                        continue

                    EntitledTiers = (
                        Member.get("relationships", {})
                        .get("currently_entitled_tiers", {})
                        .get("data", [])
                    )
                    TierIDs = [Tier.get("id") for Tier in EntitledTiers]

                    HasPremium = Sub in TierIDs
                    InTiers = False
                    if Tiers:
                        InTiers = any(tier in TierIDs for tier in Tiers)

                    return User, HasPremium, InTiers

                URL = Data.get("links", {}).get("next")
                Params = None

    return None, False, False


async def GetCampaignID(AccessToken: str):
    url = "https://www.patreon.com/api/oauth2/v2/identity?include=campaign"
    headers = {
        "Authorization": f"Bearer {AccessToken}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as Session:
        async with Session.get(url, headers=headers) as Resp:
            if Resp.status != 200:
                return None
            Data = await Resp.json()
            for Item in Data.get("included", []):
                if Item.get("type") == "campaign":
                    return Item.get("id")
    return None


def FindUserByID(included, user_id):
    for item in included:
        if item.get("type") == "user" and item.get("id") == user_id:
            return item
    return None


async def PremiumMembers():
    AccessToken = await GetAccessToken()
    if not AccessToken:
        return []

    CampaignID = await GetCampaignID(AccessToken)
    if not CampaignID:
        return []

    Members = []
    BaseURL = f"https://www.patreon.com/api/oauth2/v2/campaigns/{CampaignID}/members"
    Params = {
        "include": "currently_entitled_tiers,user",
        "fields[member]": "patron_status",
        "fields[user]": "social_connections",
        "page[count]": 100,
    }

    headers = {
        "Authorization": f"Bearer {AccessToken}",
        "Content-Type": "application/json",
    }

    NextURL = BaseURL

    async with aiohttp.ClientSession() as Session:
        while NextURL:
            async with Session.get(NextURL, headers=headers, params=Params) as Resp:
                if Resp.status != 200:
                    logger.error("Failed to get members: " + str(Resp.status))
                    break

                Data = await Resp.json()
                Included = Data.get("included", [])
                Users = {
                    item["id"]: item for item in Included if item.get("type") == "user"
                }

                for Member in Data.get("data", []):
                    PatronStatus = Member.get("attributes", {}).get("patron_status")
                    if PatronStatus != "active_patron":
                        continue

                    UserRef = (
                        Member.get("relationships", {}).get("user", {}).get("data", {})
                    )
                    UserID = UserRef.get("id")
                    User = Users.get(UserID)
                    if not User:
                        continue

                    DiscordInfo = (
                        User.get("attributes", {})
                        .get("social_connections", {})
                        .get("discord")
                    )
                    if not DiscordInfo or not DiscordInfo.get("user_id"):
                        continue

                    TierIDs = [
                        t.get("id")
                        for t in Member.get("relationships", {})
                        .get("currently_entitled_tiers", {})
                        .get("data", [])
                    ]

                    if 22855340 in TierIDs:
                        Members.append(
                            {
                                "discord_id": DiscordInfo["user_id"],
                                "tier_ids": TierIDs,
                                "patron_status": PatronStatus,
                            }
                        )

                NextURL = Data.get("links", {}).get("next")

    return Members
