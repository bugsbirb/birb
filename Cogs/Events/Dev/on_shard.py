import discord
from discord.ext import commands
from utils.emojis import *
import os
from sentry_sdk import metrics
import logging
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
                content=f"<:status_green:1227365520857104405> • `{shard}` has connected."
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
                content=f"<:status_red:1227365495376711700> • `{shard}` has disconnected."
            )
        except discord.Forbidden:
            return
        if os.getenv("SENTRY_URL", None):
            metrics.count("shard_disconnect", 1)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Shards(client))
