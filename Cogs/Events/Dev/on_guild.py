import discord
from discord.ext import commands
import os

from utils.emojis import *
from Cogs.Modules.promotions import SyncServer
from datetime import datetime
from sentry_sdk import metrics

import logging

logger = logging.getLogger(__name__)

PrimaryServers = (
    [int(x) for x in os.getenv("DEFAULT_ALLOWED_SERVERS").split(",")]
    if os.getenv("DEFAULT_ALLOWED_SERVERS")
    else []
)


class GuildJoins(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.GuildChannels = {
            "join": (
                1366053350554206310
                if not os.getenv("JoinChannel")
                else int(os.getenv("JoinChannel"))
            ),
            "leave": (
                1366053385564065842
                if not os.getenv("LeaveChannel")
                else int(os.getenv("LeaveChannel"))
            ),
            "webhook": 1366053439036981370,
            "notable-joins": 1366053372339421204,
            "notable-leaves": 1366053406413815888,
        }

    async def LogJoin(self, guild: discord.Guild):
        if not (guild and guild.member_count is not None and guild.id):
            return
        blacklist = await self.client.db["blacklists"].find_one(
            {"user": guild.owner_id}
        )

        try:
            embed = discord.Embed(
                description=f"**Owner:** <@{guild.owner_id}>\n**Guild ID** {guild.id}\n**Members:** {guild.member_count}\n**Created:** <t:{guild.created_at.timestamp():.0f}:F>\n**Blacklisted:** {f'{tick}' if blacklist else f'{no}'}",
                color=discord.Color.dark_embed(),
                timestamp=datetime.utcnow(),
            )
            embed.set_author(name=f"{guild.name}", icon_url=guild.icon)
            embed.set_footer(text=f"ID: {guild.id}")
            embed.set_thumbnail(url=guild.icon)
            if guild.member_count is not None and guild.member_count >= 1000:
                channel: discord.TextChannel = self.client.get_channel(
                    self.GuildChannels.get("notable-joins")
                )
            else:
                channel: discord.TextChannel = self.client.get_channel(
                    self.GuildChannels.get("join")
                )
            if not channel:
                return
            await channel.send(embed=embed)
        except (discord.HTTPException, discord.Forbidden, TypeError):
            return

    async def LogWebhookJoin(self, guild: discord.Guild):
        channel = self.client.get_channel(self.GuildChannels.get("webhook"))

        if channel:
            webhook = discord.utils.get(
                await channel.webhooks(), name="Public Bot Logs"
            )
            try:
                await webhook.send(
                    f"<:join:1140670830792159373> I am now in {len(self.client.guilds)} guilds.",
                    username=guild.name,
                    avatar_url=guild.icon,
                )
            except (discord.HTTPException, discord.Forbidden):
                pass
            inviter = None
            try:
                async for entry in guild.audit_logs(
                    action=discord.AuditLogAction.bot_add
                ):
                    if entry.target.id == self.client.user.id:
                        inviter = entry.user
                        break
                if inviter:
                    try:
                        await inviter.send(
                            f"🎉 Thank you for adding **Astro Birb** to your server. To get started run </config:1140463441136586784>!\n<:ArrowDropDown:1163171628050563153> Guild `#{len(self.client.guilds)}`"
                        )
                    except discord.Forbidden:
                        logger.warning(
                            "[⚠️] I couldn't DM the owner of the guild for the guild join."
                        )
            except discord.Forbidden:
                logger.warning(
                    "[⚠️] I couldn't DM the owner of the guild for the guild join."
                )

    async def LogLeave(self, guild: discord.Guild):

        if not (guild, guild.member_count, guild.id):
            return
        blacklist = await self.client.db["blacklists"].find_one(
            {"user": guild.owner_id}
        )
        try:
            embed = discord.Embed(
                description=f"**Owner:** <@{guild.owner_id}>\n**Guild ID** {guild.id}\n**Members:** {guild.member_count}\n**Created:** <t:{guild.created_at.timestamp():.0f}:F>\n**Blacklisted:** {f'{tick}' if blacklist else f'{no}'}",
                color=discord.Color.dark_embed(),
                timestamp=datetime.utcnow(),
            )
            embed.set_author(name=f"{guild.name}", icon_url=guild.icon)
            embed.set_footer(text=f"ID: {guild.id}")
            embed.set_thumbnail(url=guild.icon)
            if guild.member_count is not None and guild.member_count >= 1000:
                channel: discord.TextChannel = self.client.get_channel(
                    self.GuildChannels.get("notable-leaves")
                )
            else:
                channel: discord.TextChannel = self.client.get_channel(
                    self.GuildChannels.get("leave")
                )
            if not channel:
                return
            await channel.send(embed=embed)
        except (discord.HTTPException, discord.Forbidden):
            return

    async def HandlePrimaryServers(self, guild: discord.Guild):
        Whitelist = await self.client.db["whitelist"].find_one({"_id": str(guild.id)})
        if not guild.id in PrimaryServers and not Whitelist:
            try:
                await guild.leave()
            except discord.Forbidden:
                return False
            return False
        return True

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if not guild:
            return
        if not (guild.member_count, guild.id):
            return
        if os.getenv("DEFAULT_ALLOWED_SERVERS") or os.getenv("STAFF"):
            if not await self.HandlePrimaryServers(guild):
                return
        await self.LogJoin(guild)
        await self.LogWebhookJoin(guild)
        await self.UpdateData(datetime.now().strftime("%Y-%m-%d"), "new")
        await SyncServer(self.client, guild)
        if os.getenv("SENTRY_URL", None):
            mCount = guild.member_count if guild.member_count else 0
            metrics.count(
                "on_guild_join",
                1,
                attributes={">=1000": (mCount >= 1000), ">=5000": (mCount >= 5000)},
            )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        if not guild:
            return
        if not (guild.member_count, guild.id):
            return
        await self.LogLeave(guild)
        await self.UpdateData(datetime.now().strftime("%Y-%m-%d"), "left")
        if os.getenv("SENTRY_URL", None):
            metrics.count(
                "on_guild_leave",
                1,
            )

    async def UpdateData(self, TodayDate, action):
        Data = await self.client.db["Servers"].find_one({"_id": "Data"})
        if not Data:
            Data = {
                "_id": "Data",
                "today": {"new": 0, "left": 0},
                "total": {"new": 0, "left": 0},
                "stats": [],
            }
            await self.client.db["Servers"].insert_one(Data)

        TodayStat = next((stat for stat in Data["stats"] if TodayDate in stat), None)
        if TodayStat:
            TodayStat[TodayDate][action] += 1
        else:
            Data["stats"].append(
                {
                    TodayDate: {
                        "new": 1 if action == "new" else 0,
                        "left": 1 if action == "left" else 0,
                    }
                }
            )

        increment = {
            f"total.{action}": 1,
        }
        if action == "new":
            increment["today.new"] = 1
        elif action == "left":
            increment["today.left"] = 1

        await self.client.db["Servers"].update_one(
            {"_id": "Data"},
            {
                "$inc": increment,
                "$set": {
                    "stats": Data["stats"],
                },
            },
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(GuildJoins(client))
