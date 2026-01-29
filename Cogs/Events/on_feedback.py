import discord
from discord.ext import commands
from bson import ObjectId

import logging
from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed

logger = logging.getLogger(__name__)

class OnFEEDABCKS(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_feedback(self, objectID: ObjectId, settings: dict):
        back = await self.client.db['feedback'].find_one({"_id": objectID})
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
        custom = await self.client.db['Customisation'].find_one(
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
            replacements = {
                "{staff.mention}": staff.mention,
                "{staff.name}": staff.display_name,
                "{staff.display_name}": staff.display_name,
                "{staff.avatar}": (
                    staff.display_avatar.url if staff.display_avatar else None
                ),
                "{author.mention}": author.mention,
                "{author.name}": author.display_name,
                "{author.avatar}": (
                    author.display_avatar.url if author.display_avatar else None,
                ),
                "{author.display_name}": (
                    author.display_name if author.display_name else None
                ),
                "{feedback}": back.get("feedback"),
                "{rating}": back.get("rating"),
            }
            embed = await DisplayEmbed(custom, author, replacements=replacements)
            embed.set_footer(text=f"Feedback ID: {back.get('feedbackid')}")
        await channel.send(embed=embed, content=staff.mention)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(OnFEEDABCKS(client))
