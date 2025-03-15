import discord
from discord.ext import commands
from bson import ObjectId
from utils.format import IsSeperateBot

import logging
from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed
from utils.emojis import *
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class On_suggestions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_suggestion(self, objectID: ObjectId, settings: dict):
        back = await self.client.db["suggestions"].find_one({"_id": objectID})
        if not back:
            return logging.critical("[on_suggestion] I can't find the feedback.")

        guild = await self.client.fetch_guild(back.get("guild_id"))
        if not guild:
            return logging.critical("[on_suggestion] I can't find the server.")
        author = await guild.fetch_member(back.get("author_id"))
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
            return print(
                f"[🏠 on_feedback] @{guild.name} the feedback channel can't be found. [1]"
            )
        if channel is None:
            logging.warning(
                f"[🏠 on_feedback] @{guild.name} the feedback channel can't be found. [2]"
            )
            return
        custom = await self.client.db["Customisation"].find_one(
            {"guild_id": guild.id, "type": "Suggestion"}
        )
        if not custom:
            embed = discord.Embed(
                title="",
                description=f"<:Member:1226674150463111299> {author.mention}",
                color=discord.Color.yellow(),
            )
            embed.set_thumbnail(url=author.display_avatar)
            embed.set_image(
                url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png"
            )
            if back.get("image"):
                embed.set_image(url=back.get("image"))
            embed.add_field(
                name="<:pin:1226671966413389864> Suggestion",
                value=back.get("suggestion"),
            )
            embed.set_author(icon_url=author.display_avatar, name=author.name)
            embed.add_field(
                name="<:messageforward1:1230919023361921165> Opinions",
                value="0 <:UpVote:1223062893096996934> | 0 <:DownVote:1223063241433939989>",
            )
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
        view = Voting()
        if IsSeperateBot():
            view.settings.label = "Settings"
        msg = await channel.send(embed=embed, view=view)
        await self.client.db["suggestions"].update_one(
            {"_id": objectID}, {"$set": {"message_id": msg.id}}
        )


class Voting(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Upvote",
        style=discord.ButtonStyle.green,
        custom_id="PERSISTENTR:UPVOTE",
        emoji="<:UpVote:1223062893096996934>",
    )
    async def upvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )
        result = await interaction.client.db["suggestions"].find_one(
            {"message_id": interaction.message.id}
        )
        if not result:
            return logging.critical(
                f"[upvoting] in {interaction.guild.name} I couldn't find the suggestion data to update it."
            )

        if interaction.user.id in result.get("upvoters"):
            await interaction.client.db["suggestions"].update_one(
                {"message_id": interaction.message.id},
                {"$pull": {"upvoters": interaction.user.id}},
            )
        else:
            await interaction.client.db["suggestions"].update_one(
                {"message_id": interaction.message.id},
                {"$push": {"upvoters": interaction.user.id}},
            )
            if interaction.user.id in result.get("downvoters"):
                await interaction.client.db["suggestions"].update_one(
                    {"message_id": interaction.message.id},
                    {"$pull": {"downvoters": interaction.user.id}},
                )

        interaction.client.dispatch(
            "suggestion_edit", result.get("_id"), settings, "Suggestion"
        )
        await interaction.response.edit_message(content="")

    @discord.ui.button(
        label="Downvote",
        style=discord.ButtonStyle.red,
        custom_id="PERSISTENTR:DOWNVOTE",
        emoji="<:DownVote:1059585429357211760>",
    )
    async def downvote(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        settings = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )
        result = await interaction.client.db["suggestions"].find_one(
            {"message_id": interaction.message.id}
        )
        if not result:
            return logging.critical(
                f"[downvoting] in {interaction.guild.name} I couldn't find the suggestion data to update it."
            )

        if interaction.user.id in result.get("downvoters"):
            await interaction.client.db["suggestions"].update_one(
                {"message_id": interaction.message.id},
                {"$pull": {"downvoters": interaction.user.id}},
            )
        else:
            await interaction.client.db["suggestions"].update_one(
                {"message_id": interaction.message.id},
                {"$push": {"downvoters": interaction.user.id}},
            )
            if interaction.user.id in result.get("upvoters"):
                await interaction.client.db["suggestions"].update_one(
                    {"message_id": interaction.message.id},
                    {"$pull": {"upvoters": interaction.user.id}},
                )

        interaction.client.dispatch(
            "suggestion_edit", result.get("_id"), settings, "Suggestion"
        )
        await interaction.response.edit_message(content="")

    @discord.ui.button(
        label="Voters", style=discord.ButtonStyle.gray, custom_id="VOTING;RESADADJ"
    )
    async def voters(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await interaction.client.db["suggestions"].find_one(
            {"message_id": interaction.message.id}
        )
        if not result:
            return logging.critical(
                f"[voters] in {interaction.guild.name} I couldn't find the suggestion data to display voters."
            )

        upvoters = result.get("upvoters", [])
        downvoters = result.get("downvoters", [])
        upvoter_mentions = [f"<@{user_id}>" for user_id in upvoters]
        downvoter_mentions = [f"<@{user_id}>" for user_id in downvoters]
        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(
            name="Suggestions",
            icon_url="https://cdn.discordapp.com/emojis/1207370004379607090.webp?size=96",
        )
        embed.add_field(
            name="Upvoters",
            value="\n".join(upvoter_mentions) if upvoter_mentions else "> No upvotes",
            inline=False,
        )
        embed.add_field(
            name="Downvoters",
            value=(
                "\n".join(downvoter_mentions)
                if downvoter_mentions
                else "> No downvotes"
            ),
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="",
        emoji="<:Setting:1223062944187813918>",
        custom_id="settingsbuttonforsuggestions",
    )
    async def settings(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            from utils.permissions import has_admin_role

            if not await has_admin_role(interaction):
                print("check")
                return

            await interaction.response.defer(ephemeral=True)
            suggestion_data = await interaction.client.db["suggestions"].find_one(
                {"message_id": interaction.message.id}
            )
            if not suggestion_data:
                await interaction.followup.send(
                    f"  **Suggestion** data for this suggestion can not be found.",
                    ephemeral=True,
                )
                return
            if suggestion_data is None:
                await interaction.followup.send(
                    f"  **Suggestion** data for this suggestion can not be found.",
                    ephemeral=True,
                )
                return
            view = discord.ui.View()
            view.add_item(ManageSuggestion(interaction.message))
            await interaction.followup.send(
                f"  **{interaction.user.display_name}**, here are the settings for this suggestion.",
                view=view,
                ephemeral=True,
            )
        except Exception as e:
            print(e)


class ManageSuggestion(discord.ui.Select):
    def __init__(self, msg):
        options = [
            discord.SelectOption(
                label="Approve",
                description="Approve the suggestion",
                emoji="<:whitecheck:1223062421212631211>",
            ),
            discord.SelectOption(
                label="Reject",
                description="Reject the suggestion",
                emoji="<:whitex:1190819175447408681>",
            ),
        ]
        super().__init__(
            placeholder="⚙️ | Manage Suggestion",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
        settings = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )
        result = await interaction.client.db["suggestions"].find_one(
            {"message_id": self.msg.id}
        )
        if not result:
            return logging.critical(
                f"[ManageSuggestion] in {interaction.guild.name} I couldn't find the suggestion data to manage it."
            )

        if selected_option == "Approve":
            interaction.client.dispatch(
                "suggestion_edit", result.get("_id"), settings, "Accepted Suggestion"
            )
            await interaction.response.edit_message(
                content=f"  **{interaction.user.display_name}**, it has been marked as accepted.",
                view=None,
            )

        elif selected_option == "Reject":
            await interaction.response.send_modal(DenialReason(self.msg))


class DenialReason(discord.ui.Modal, title="Denial Reason"):
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.long)

    def __init__(self, msg):
        super().__init__()
        self.msg = msg

    async def on_submit(self, interaction: discord.Interaction):
        settings = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )
        result = await interaction.client.db["suggestions"].find_one(
            {"message_id": self.msg.id}
        )
        if not result:
            return logging.critical(
                f"[DenialReason] in {interaction.guild.name} I couldn't find the suggestion data to manage it."
            )

        await interaction.client.db["suggestions"].update_one(
            {"message_id": self.msg.id},
            {"$set": {"reason": self.reason.value}},
        )
        interaction.client.dispatch(
            "suggestion_edit", result.get("_id"), settings, "Denied Suggestion"
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** suggestion marked as denied.",
            view=None,
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(On_suggestions(client))
