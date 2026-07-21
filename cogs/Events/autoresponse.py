import logging
import random
import re
from datetime import datetime

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

from core.discord.Variables import Variables
from core.discord.permissions import premium
from core.format import ReplaceVariables

logger = logging.getLogger(__name__)


class autoresponse(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return
        if message.author == self.client.user:
            return
        if message.author.bot:
            return

        if not await premium(message.guild.id):
            return

        autoresponses = (
            await self.client.db["Auto Responders"]
            .find({"guild_id": message.guild.id}, limit=750)
            .to_list(length=None)
        )

        if not autoresponses:
            return

        replacements = await Variables.build(
            staff=message.author,
            author=message.author,
            guild=message.guild,
            extra=Variables.channel(message.channel),
        )

        for response in autoresponses:
            trigger = response.get("trigger")
            if response.get("similarity") is None:
                similarity_threshold = None
            else:
                similarity_threshold = int(response.get("similarity"))
            response_text = ReplaceVariables(response.get("response"), replacements)

            if (
                similarity_threshold is None and trigger == message.content.lower()
            ) or (
                similarity_threshold is not None
                and int(fuzz.ratio(trigger.lower(), message.content.lower()))
                >= similarity_threshold
            ):
                await message.reply(response_text)
                break
            try:
                pattern = re.compile(trigger, re.IGNORECASE)
                if pattern.search(message.content):
                    await message.reply(response_text)
                    break
            except re.error as e:
                logger.error(f"regex issue: {trigger} - {e}")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(autoresponse(client))
