import discord
from discord.ext import commands
from utils.emojis import *
import re
import random
from fuzzywuzzy import fuzz
from datetime import datetime
from utils.permissions import premium
import logging
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
        try:
            guild = message.guild
            owner = await guild.fetch_member(guild.owner_id)
            ownermention = owner.mention
            ownername = owner.name
            ownerid = owner.id
        except discord.NotFound:
            ownermention = None
            ownername = None
            ownerid = None
        timestamp = datetime.utcnow().timestamp()
        timestampformat = f"<t:{int(timestamp)}:F>"
        replacements = {
            "{author.mention}": message.author.mention,
            "{author.name}": message.author.display_name,
            "{author.id}": str(message.author.id),
            "{timestamp}": timestampformat,
            "{guild.name}": message.guild.name if message.guild else "",
            "{guild.id}": str(message.guild.id) if message.guild else "",
            "{guild.owner.mention}": (
                ownermention if message.guild and ownermention else ""
            ),
            "{guild.owner.name}": ownername if message.guild and owner else "",
            "{guild.owner.id}": str(ownerid) if message.guild and owner else "",
            "{random}": int(random.randint(1, 1000000)),
            "{guild.members}": int(message.guild.member_count),
            "{channel.name}": (
                message.channel.name if message.channel else message.channel.name
            ),
            "{channel.id}": (
                str(message.channel.id) if message.channel else str(message.channel.id)
            ),
            "{channel.mention}": (
                message.channel.mention if message.channel else message.channel.mention
            ),
        }

        for response in autoresponses:
            trigger = response["trigger"]
            if response.get("similarity") is None:
                similarity_threshold = None
            else:
                similarity_threshold = int(response.get("similarity"))
            response_text = await self.replace_variables(
                response["response"], replacements
            )

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

    @staticmethod
    async def replace_variables(message, replacements):
        for placeholder, value in replacements.items():
            if value is not None:
                message = str(message).replace(placeholder, str(value))
            else:
                message = str(message).replace(placeholder, "")
        return message


async def setup(client: commands.Bot) -> None:
    await client.add_cog(autoresponse(client))
