import discord
from discord.ext import commands, tasks
from core.bot.emojis import *
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
import re
import logging

from core.integrations.dokploy import premium, GetProjects, StopApplication
from core.integrations.patreon import SubscriptionUser
from core.format import IsSeperateBot
from datetime import datetime
from core.bot.HelpEmbeds import NotYourPanel

logger = logging.getLogger(__name__)


environment = os.getenv("ENVIRONMENT")


class CheckSubscription(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.SubscriptionStatus.start()
        self.SubscriptionRoles.start()

    @tasks.loop(hours=12)
    async def SubscriptionRoles(self):
        await self.client.wait_until_ready()
        if IsSeperateBot():
            return
        if os.getenv("ENVIRONMENT") in ["custom", "development"]:
            return
        Guild = self.client.get_guild(1092976553752789054)
        PremiumRole = Guild.get_role(1233945875680596010)
        BrandingRole = Guild.get_role(1182022232407543981)
        if not PremiumRole or not BrandingRole:
            return
        PremiumMembers = set()
        BrandingMembers = set()
        for member in Guild.members:
            if PremiumRole in member.roles:
                PremiumMembers.add(member.id)
            if BrandingRole in member.roles:
                BrandingMembers.add(member.id)

        for B in BrandingMembers:
            U = await SubscriptionUser(UserID=B, Sub="22733636")
            if U:
                _, has_branding, _ = U
                if not has_branding:
                    member = Guild.get_member(B)
                    if member and BrandingRole in member.roles:
                        try:
                            await member.remove_roles(
                                BrandingRole, reason="Custom branding expired"
                            )
                        except (discord.Forbidden, discord.HTTPException):
                            pass
        for P in PremiumMembers:
            U = await SubscriptionUser(UserID=P, Tiers=["22733636", "22855340"])
            if U:
                _, _, HAs = U
                if not HAs:
                    member = Guild.get_member(P)
                    if member and PremiumRole in member.roles:
                        try:
                            await member.remove_roles(
                                PremiumRole, reason="Premium expired"
                            )
                        except (discord.Forbidden, discord.HTTPException):
                            pass

    @tasks.loop(hours=6)
    async def SubscriptionStatus(self):
        await self.client.wait_until_ready()
        if IsSeperateBot():
            return
        if os.getenv("ENVIRONMENT") in ["custom", "development"]:
            return
        Bots = await self.client.db["bots"].find({}).to_list(length=None)
        Sub = await self.client.db["Subscriptions"].find({}).to_list(length=None)
        guild = self.client.get_guild(1092976553752789054)
        for P in Sub:
            Z = await SubscriptionUser(
                UserID=P.get("user"), Tiers=["22733636", "22855340"]
            )
            if Z is None:
                continue
            _, _, HasPremium = Z
            if not HasPremium:
                logger.info(f"Premium expired for user {P.get('user')}")
                for guild_id in P.get("guilds", []):
                    config = await self.client.db["Config"].find_one({"_id": guild_id})
                    if config is not None:
                        features = config.get("Features", [])
                        if "PREMIUM" in features:
                            features.remove("PREMIUM")
                            await self.client.db["Config"].update_one(
                                {"_id": guild_id},
                                {"$set": {"Features": features}},
                            )
                await premium.delete_one({"user": P.get("user")})

                if guild:
                    member = guild.get_member(P.get("user"))
                    if member:
                        role = guild.get_role(1233945875680596010)
                        if role and role in member.roles:
                            try:
                                await member.remove_roles(
                                    role, reason="Premium expired"
                                )
                            except Exception as e:
                                pass

                try:
                    Owner = await self.client.fetch_user(1092976553752789054)
                    await Owner.send(
                        f"Premium expired for user <@{P.get('user')}>. Their premium status has been removed and all associated servers have lost premium features."
                    )
                except:
                    pass

        for B in Bots:
            Z = await SubscriptionUser(UserID=B.get("user"), Sub="22733636")
            if Z is None:
                continue
            _, HasBranding, _ = Z
            if not HasBranding:
                if guild:
                    member = guild.get_member(B.get("user"))
                    if member:
                        role = guild.get_role(1182022232407543981)
                        Premium = guild.get_role(1233945875680596010)
                        if role and role in member.roles:
                            try:
                                await member.remove_roles(
                                    role, reason="Custom branding expired"
                                )
                            except (discord.Forbidden, discord.HTTPException):
                                pass

                        if Premium and Premium in member.roles:
                            try:
                                await member.remove_roles(
                                    Premium, reason="Premium expired"
                                )
                            except (discord.Forbidden, discord.HTTPException):
                                pass
                            try:
                                await member.remove_roles(
                                    role, reason="Custom branding expired"
                                )
                            except (discord.Forbidden, discord.HTTPException):
                                pass

                try:
                    if not B.get("user") or not isinstance(B.get("user"), int):
                        continue
                    User = await self.client.fetch_user(int(B.get("user")))
                except:
                    continue
                name = re.sub(r"[^a-zA-Z0-9]", "", User.name)
                Projects = await GetProjects()
                if Projects:
                    for project in Projects.get("applications", []):
                        if project.get("name") == name:
                            logger.info(
                                f"Branding expired for user {B.get('user')} - stopping application {project.get('applicationId')}"
                            )
                            await StopApplication(project.get("applicationId"))
                            try:
                                Owner = await self.client.fetch_user(
                                    1092976553752789054
                                )
                                await Owner.send(
                                    f"Branding expired for user <@{B.get('user')}> - application {project.get('applicationId')} has been stopped."
                                )
                            except:
                                pass
                            break


async def setup(client: commands.Bot) -> None:
    await client.add_cog(CheckSubscription(client))
