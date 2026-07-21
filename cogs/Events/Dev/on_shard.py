import logging
import os

import discord
from discord.ext import commands
from sentry_sdk import metrics

from core.bot.emojis import Emojis

logger = logging.getLogger(__name__)


class Shards(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_shard_connect(self, shard: int):
        await self.client.wait_until_ready()
        try:
            channel = await self.client.fetch_channel(
                os.getenv("SHARD_CHANNEL", 1371586445466407012)
            )
            await channel.send(
                content=f"{Emojis.status_green} • `{shard}` has connected."
            )
        except discord.Forbidden:
            return
        if os.getenv("SENTRY_URL", None):
            metrics.count("shard_connect", 1)

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard: int):
        await self.client.wait_until_ready()
        try:
            channel = await self.client.fetch_channel(
                os.getenv("SHARD_CHANNEL", 1371586445466407012)
            )
            await channel.send(
                content=f"{Emojis.status_red} • `{shard}` has disconnected."
            )
        except discord.Forbidden:
            return
        if os.getenv("SENTRY_URL", None):
            metrics.count("shard_disconnect", 1)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Shards(client))
