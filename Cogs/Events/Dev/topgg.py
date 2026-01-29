from discord.ext import commands, tasks
from utils.emojis import *
import topgg

import os

environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")
dbl_token = os.getenv("DBL_TOKEN")

import logging
logger = logging.getLogger(__name__)

class Topgg(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        self.topggpy = topgg.DBLClient(self.client, dbl_token)
        self.update_stats.start()

    @tasks.loop(minutes=30)
    async def update_stats(self):
        if environment == "custom":
            return
        try:
            await self.topggpy.post_guild_count()
            logger.info(f"[🔝] Posted server count ({self.topggpy.guild_count})")
        except Exception as e:
            logger.error("[⬇️] Failed to post server count")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Topgg(client))
