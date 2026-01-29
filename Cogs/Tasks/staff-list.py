import discord
from discord.ext import commands

from discord.ext import tasks
import os
from utils.emojis import *
from datetime import datetime
from utils.Module import ModuleCheck
import asyncio
import logging
import sentry_sdk

logger = logging.getLogger(__name__)

environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")


class StaffList(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.updatelist.start()
        client.Tasks.add("Staff List")

    @tasks.loop(minutes=30, reconnect=True)
    @sentry_sdk.trace()
    async def updatelist(self):
        logger.info("Checking Staff List")
        if environment == "custom":
            activelistresult = (
                await self.client.db["Active Staff List"]
                .find({"guild_id": int(guildid)})
                .to_list(length=None)
            )
        else:
            activelistresult = (
                await self.client.db["Active Staff List"].find({}).to_list(length=None)
            )

        if not activelistresult:
            return
        semaphore = asyncio.Semaphore(5)

        async def process(data):
            async with semaphore:
                await self.UpdateList(data)

        await asyncio.gather(*(process(data) for data in activelistresult))
        del activelistresult

    @sentry_sdk.trace()
    async def UpdateList(self, data):
        try:
            guild = self.client.get_guild(data.get("guild_id"))
            if not guild:
                return
            if not await ModuleCheck(guild.id, "Staff List"):
                return

            results = (
                await self.client.db["Staff List"]
                .find({"guild_id": guild.id})
                .to_list(length=None)
            )
            if not results:
                return

            results = sorted(results, key=lambda x: int(x.get("position", 0)))
            MemberRoles = {}
            HighestSeen = {}

            if not guild.chunked:
                await guild.chunk()

            for member in guild.members:
                HighestRole = max(
                    (
                        role
                        for role in member.roles
                        if any(role.id == result["rank"] for result in results)
                    ),
                    key=lambda role: role.position,
                    default=None,
                )
                MemberRoles[member] = HighestRole
                HighestSeen[member] = HighestRole

            embed = discord.Embed(
                title="Staff Team",
                color=discord.Color.dark_embed(),
                timestamp=datetime.now(),
            )
            embed.set_thumbnail(url=guild.icon)
            embed.set_author(name=guild.name, icon_url=guild.icon)
            embed.set_footer(text="Last Updated")

            description = ""
            for result in results:
                role = guild.get_role(result.get("rank"))
                if role:
                    members = [
                        member.mention
                        for member in MemberRoles
                        if MemberRoles[member] == role and HighestSeen[member] == role
                    ]
                    if members:
                        description += (
                            f"### **{role.mention}** ({len(members)})\n\n> "
                            + "\n> ".join(members)
                            + "\n"
                        )

            embed.description = description
            ChannelID = data.get("channel_id")
            MessageId = data.get("msg")

            if ChannelID and MessageId:
                try:
                    channel = await self.client.fetch_channel(ChannelID)
                    msg = await channel.fetch_message(MessageId)
                    if msg:
                        await msg.edit(embed=embed)
                except (discord.HTTPException, discord.NotFound):
                    return            
        except Exception as e:
            logger.error(f"[ERROR] {e}")

    @updatelist.before_loop
    async def before_updatelist(self):
        await self.client.wait_until_ready()


async def setup(client):
    await client.add_cog(StaffList(client))
