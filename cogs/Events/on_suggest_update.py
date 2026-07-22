import logging

from bson import ObjectId
from discord.ext import commands

from cogs.Events.on_suggestion import Voting
from core.bot.CustomEmbed import DisplayEmbed
from core.bot.emojis import *
from core.format import IsSeperateBot

logger = logging.getLogger(__name__)


class On_suggestions_edit(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_suggestion_edit(self, objectID: ObjectId, settings: dict, action):
        back = await self.client.db["suggestions"].find_one({"_id": objectID})
        if not back:
            return logging.critical("[on_suggestion] I can't find the feedback.")

        guild = await self.client.fetch_guild(back.get("guild_id"))
        if not guild:
            return logging.critical("[on_suggestion] I can't find the server.")
        try:
            author = await self.client.fetch_user(back.get("author_id"))
        except (discord.HTTPException, discord.NotFound):
            return logger.critical("[on_suggestion] can't find the author")
        if not author:
            return logger.critical("[on_suggestion] can't find the author")

        ChannelID = settings.get("Suggestions").get("channel")
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
        MsgID = back.get("message_id")
        message = await channel.fetch_message(MsgID)
        if not message:
            logging.warning(
                f"[🏠 on_feedback] @{guild.name} I can't access the suggestion."
            )
            return
        custom = await self.client.db["Customisation"].find_one(
            {"guild_id": guild.id, "type": action}
        )
        view = Voting()
        if IsSeperateBot():
            view.settings.label = "Settings"
        if not custom:

            embed = discord.Embed(
                title="",
                description=f"{Emojis.member} {author.mention}",
                color=discord.Color.yellow(),
            )
            embed.set_thumbnail(url=author.display_avatar)
            embed.set_image(
                url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png"
            )
            if back.get("image"):
                embed.set_image(url=back.get("image"))
            embed.add_field(
                name=f"{Emojis.pin} Suggestion",
                value=back.get("suggestion"),
            )
            embed.set_author(icon_url=author.display_avatar, name=author.name)
            embed.add_field(
                name=f"{Emojis.message_forward} Opinions",
                value=f"{len(back.get('upvoters')) if back.get('upvoters') else 0} {Emojis.upvote} | {len(back.get('downvoters')) if back.get('downvoters') else 0} {Emojis.downvote}",
            )
            if action == "Accepted Suggestion":
                embed.title = f"{Emojis.green_tick} Suggestion Accepted"
                embed.color = discord.Color.brand_green()
                view.upvote.disabled = True
                view.downvote.disabled = True
                view.settings.disabled = True
            if action == "Denied Suggestion":
                embed.title = f"{Emojis.red_cross} Suggestion Denied"
                embed.color = discord.Color.brand_red()
                embed.add_field(
                    name="Denied Reason", value=f"{back.get('reason')}", inline=False
                )
                view.upvote.disabled = True
                view.downvote.disabled = True
                view.settings.disabled = True

        else:
            replacements = {
                "{author.mention}": author.mention,
                "{author.name}": author.display_name,
                "{author.avatar}": (
                    author.display_avatar.url if author.display_avatar else None,
                ),
                "{suggestion}": back.get("suggestion"),
                "{image}": back.get("image"),
                "{upvotes}": len(back.get("upvoters")) if back.get("upvoters") else 0,
                "{downvoters}": (
                    len(back.get("downvoters")) if back.get("downvoters") else 0
                ),
                "{reason}": back.get("reason"),
                "{downvote}": (
                    len(back.get("downvoters")) if back.get("downvoters") else 0
                ),
            }
            embed = await DisplayEmbed(custom, author, replacements=replacements)
            if action in ["Denied Suggestion", "Accepted Suggestion"]:
                view.upvote.disabled = True
                view.downvote.disabled = True
                view.settings.disabled = True
        await message.edit(embed=embed, view=view)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(On_suggestions_edit(client))
