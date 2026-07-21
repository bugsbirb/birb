import logging

import discord
from bson import ObjectId
from discord.ext import commands

from core.bot.CustomEmbed import DisplayEmbed
from core.bot.Variables import Variables

logger = logging.getLogger(__name__)


class OnFeedback(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_feedback(self, objectID: ObjectId, settings: dict):
        back = await self.client.db["feedback"].find_one({"_id": objectID})
        if not back:
            return logging.critical("[on_feedback] I can't find the feedback.")

        guild = await self.client.fetch_guild(back.get("guild_id"))
        if not guild:
            return logging.critical("[on_feedback] I can't find the server.")
        staff = await guild.fetch_member(back.get("staff"))
        if not staff:
            return logger.critical("[on_feedback] can't find the staff member")
        author = await guild.fetch_member(back.get("author"))
        if not author:
            return logger.critical("[on_feedback] can't find the author")

        ChannelID = settings.get("Feedback").get("channel")
        if not ChannelID:
            logging.warning(
                f"[🏠 on_feedback] @{guild.name} no channel ID found in settings."
            )
            return
        try:
            channel = await guild.fetch_channel(int(ChannelID))
        except Exception as e:
            logger.error(
                f"[🏠 on_feedback] @{guild.name} the feedback channel can't be found. [1]"
            )
            return
        if channel is None:
            logging.warning(
                f"[🏠 on_feedback] @{guild.name} the feedback channel can't be found. [2]"
            )
            return
        custom = await self.client.db["Customisation"].find_one(
            {"guild_id": guild.id, "type": "Feedback"}
        )
        if not custom:
            embed = discord.Embed(
                title="Staff Feedback",
                description=f"* **Staff:** {staff.mention}\n* **Rating:** {back.get('rating')}\n* **Feedback:** {back.get('feedback')}",
                color=discord.Color.dark_embed(),
            )
            embed.set_thumbnail(url=staff.display_avatar)
            embed.set_author(
                name=f"From {author.display_name}",
                icon_url=author.display_avatar,
            )
            embed.set_footer(text=f"Feedback ID: {back.get('feedbackid')}")
        else:
            replacements = await Variables.feedback(
                staff=staff, feedback=back, author=author, guild=guild
            )
            embed = await DisplayEmbed(custom, author, replacements=replacements)
            embed.set_footer(text=f"Feedback ID: {back.get('feedbackid')}")
        await channel.send(embed=embed, content=staff.mention)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(OnFeedback(client))
