import discord
import discord.http
from utils.emojis import *

from dotenv import load_dotenv
import traceback

load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# Configuration = DB["Config"]
# Customisation = DB["Customisation"]


class StaffFeedback(discord.ui.Select):
    def __init__(self, author: discord.User):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Feedback Channel", emoji="<:tag:1234998802948034721>"
                ),
                discord.SelectOption(
                    label="Preferences", emoji="<:leaf:1160541147320553562>"
                ),
                discord.SelectOption(
                    label="Customise Embed",
                    emoji="<:Customisation:1223063306131210322>",
                ),
            ]
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        option = interaction.data["values"][0]
        if option == "Feedback Channel":
            Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
            if not Config:
                Config = {"Feedback": {}, "_id": interaction.guild.id}
            view = discord.ui.View()
            view.add_item(
                FeedbackChannel(
                    self.author,
                    interaction.guild.get_channel(
                        Config.get("Feedback", {}).get("channel")
                    ),
                    interaction.message,
                )
            )
            await interaction.response.send_message(view=view, ephemeral=True)
        elif option == "Preferences":
            Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
            if not Config:
                Config = {
                    "Infraction": {},
                    "Module Options": {},
                    "_id": interaction.guild.id,
                }
            if not Config.get("Module Options"):
                Config["Module Options"] = {}
            view = Preferences(self.author)
            if Config.get("Module Options", {}).get("multiplefeedback", False) is True:
                view.children[0].label = "Multiple Feedback (Enabled)"
                view.children[0].style = discord.ButtonStyle.green
            else:
                view.children[0].label = "Multiple Feedback (Disabled)"
                view.children[0].style = discord.ButtonStyle.red
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.description = "> - **Multiple Feedback:** Its in the name basically you can submit multiple feedback for the same person."

            embed.set_author(
                name="Preferences",
                icon_url="https://cdn.discordapp.com/emojis/1160541147320553562.webp?size=96&quality=lossless",
            )
            await interaction.response.send_message(
                embed=embed, view=view, ephemeral=True
            )
        elif option == "Customise Embed":
            try:
                await interaction.response.defer()
                custom = await interaction.client.db['Customisation'].find_one(
                    {"guild_id": interaction.guild.id, "type": "Feedback"}
                )
                embed = None

                from Cogs.Configuration.Components.EmbedBuilder import (
                    DisplayEmbed,
                    Embed,
                )

                if not custom:
                    embed = discord.Embed(
                        title="Staff Feedback",
                        description="* **Staff:** {staff.mention}\n* **Rating:** {rating}\n* **Feedback:** {feedback}",
                        color=discord.Color.dark_embed(),
                    )
                    embed.set_thumbnail(url=interaction.user.display_avatar)
                    embed.set_author(
                        name="From {author.display_name}",
                        icon_url=interaction.user.display_avatar,
                    )
                    embed.set_footer(text="Feedback ID: {feedbackid}")
                    view = Embed(
                        interaction.user,
                        FinalFunction,
                        "Feedback",
                        {"thumb": "{staff.avatar}", "author_url": "{author.avatar}"},
                    )
                    view.remove_item(view.Buttons)
                    view.remove_item(view.RemoveEmbed)
                    view.remove_item(view.Content)
                    view.remove_item(view.Permissions)
                    view.remove_item(view.ForumsChannel)
                    view.remove_item(view.Ping)
                    return await interaction.edit_original_response(
                        embed=embed, view=view
                    )
                view = Embed(
                    interaction.user,
                    FinalFunction,
                    "Feedback",
                    {
                        "thumb": (
                            interaction.user.display_avatar.url
                            if custom.get("embed", {}).get("thumbnail")
                            == "{author.avatar}"
                            else (
                                "{staff.avatar}"
                                if custom.get("embed", {}).get("thumbnail")
                                == "{staff.avatar}"
                                else custom.get("embed", {}).get("thumbnail")
                            )
                        ),
                        "author_url": (
                            interaction.user.display_avatar.url
                            if custom.get("embed", {}).get("author", {}).get("icon_url")
                            == "{author.avatar}"
                            else (
                                "{staff.avatar}"
                                if custom.get("embed", {})
                                .get("author", {})
                                .get("icon_url")
                                == "{staff.avatar}"
                                else custom.get("embed", {})
                                .get("author", {})
                                .get("icon_url")
                            )
                        ),
                        "image": (
                            interaction.user.display_avatar.url
                            if custom.get("embed", {}).get("image") == "{author.avatar}"
                            else (
                                "{staff.avatar}"
                                if custom.get("embed", {}).get("image")
                                == "{staff.avatar}"
                                else custom.get("embed", {}).get("image")
                            )
                        ),
                    },
                )
                embed = await DisplayEmbed(custom, interaction.user)
                view.remove_item(view.Buttons)
                view.remove_item(view.RemoveEmbed)
                view.remove_item(view.Content)
                view.remove_item(view.Permissions)
                view.remove_item(view.ForumsChannel)
                view.remove_item(view.Ping)

                return await interaction.edit_original_response(embed=embed, view=view)
            except Exception as e:
                traceback.print_exc(e)


async def FinalFunction(interaction: discord.Interaction, d={}):
    from Cogs.Configuration.Configuration import ConfigMenu, Options

    embed = interaction.message.embeds[0]
    if embed:

        data = {
            "content": interaction.message.content,
            "creator": interaction.user.id,
            "embed": {
                "title": embed.title,
                "description": embed.description,
                "thumbnail": d.get("thumb"),
                "image": d.get("image"),
                "color": f"{embed.color.value:06x}" if embed.color else None,
                "author": {
                    "name": embed.author.name if embed.author else None,
                    "icon_url": d.get("author_url"),
                },
                "fields": [
                    {
                        "name": field.name,
                        "value": field.value,
                        "inline": field.inline,
                    }
                    for field in embed.fields
                ],
            },
        }
    await interaction.client.db['Customisation'].update_one(
        {"guild_id": interaction.guild.id, "type": "Feedback"},
        {"$set": data},
        upsert=True,
    )
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})

    view = discord.ui.View()
    view.add_item(StaffFeedback(interaction.user))
    view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
    await interaction.response.edit_message(
        embed=await StaffFeedbackEmbed(
            interaction, Config, discord.Embed(color=discord.Color.dark_embed())
        ),
        view=view,
    )


class Preferences(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    async def ToggleOption(
        self, interaction: discord.Interaction, button: discord.ui.Button, Option: str
    ):
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {
                "Infraction": {},
                "Module Options": {},
                "_id": interaction.guild.id,
            }
        if not Config.get("Module Options"):
            Config["Module Options"] = {}
        if Option == "multiplefeedback":
            if Config.get("Module Options", {}).get("multiplefeedback", False) is True:
                Config["Module Options"]["multiplefeedback"] = False
                button.label = "Multiple Feedback (Disabled)"
                button.style = discord.ButtonStyle.red
            else:
                Config["Module Options"]["multiplefeedback"] = True
                button.label = "Multiple Feedback (Enabled)"
                button.style = discord.ButtonStyle.green

        await interaction.client.config.update_one({"_id": interaction.guild.id}, {"$set": Config})
        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        label="Multiple Feedback (Disabled)", style=discord.ButtonStyle.red
    )
    async def IssuerButton(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "multiplefeedback")


class FeedbackChannel(discord.ui.ChannelSelect):
    def __init__(
        self,
        author: discord.User,
        channel: discord.TextChannel = None,
        message: discord.Message = None,
    ):
        super().__init__(
            min_values=0,
            max_values=1,
            default_values=[channel] if channel else [],
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.channel = channel
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Feedback": {}}
        elif "Feedback" not in config:
            config["Feedback"] = {}

        config["Feedback"]["channel"] = self.values[0].id if self.values else None
        await interaction.client.config.update_one({"_id": interaction.guild.id}, {"$set": config})
        Updated = await interaction.client.config.find_one({"_id": interaction.guild.id})
        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await StaffFeedbackEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


async def StaffFeedbackEmbed(
    interaction: discord.Interaction, config: dict, embed: discord.Embed
):
    if not config:
        config = {"Feedback": {}}
    Channel = (
        interaction.guild.get_channel(config.get("Feedback", {}).get("channel"))
        or "Not Configured"
    )

    if isinstance(Channel, discord.TextChannel):
        Channel = Channel.mention

    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's staff feedback settings! Staff feedback is a way for members to give feedback to staff. You can find out more at [the documentation](https://docs.astrobirb.dev/)."
    embed.add_field(
        name="<:settings:1207368347931516928> Staff Feedback",
        value=f"> `Feedback Channel:` {Channel}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
        inline=False,
    )
    return embed
