import discord
import discord.http
import os
import traceback
import logging

from utils.emojis import *
from utils.HelpEmbeds import NotYourPanel
from utils.permissions import premium

logger = logging.getLogger(__name__)


class ModmailOptions(discord.ui.Select):
    def __init__(self, author: discord.User, type):
        if type == "threads":
            options = [
                discord.SelectOption(
                    label="Threads Channel",
                    emoji="<:category:1248312604733210735>",
                ),
                discord.SelectOption(
                    label="Modmail Pings", emoji="<:Ping:1298301862906298378>"
                ),
                discord.SelectOption(
                    label="Preferences", emoji="<:leaf:1160541147320553562>"
                ),
                discord.SelectOption(
                    label="Modmail Categories",
                    description="Allows users to make different categories in the modmail system. ",
                    emoji="<:integrations:1272191311234990131>",
                ),
            ]

        else:
            options = [
                discord.SelectOption(
                    label="Category", emoji="<:category:1248312604733210735>"
                ),
                discord.SelectOption(
                    label="Transcripts Channel",
                    emoji="<:tag:1234998802948034721>",
                ),
                discord.SelectOption(
                    label="Modmail Pings", emoji="<:Ping:1298301862906298378>"
                ),
                discord.SelectOption(
                    label="Preferences", emoji="<:leaf:1160541147320553562>"
                ),
                discord.SelectOption(
                    label="Modmail Categories",
                    description="Allows users to make different categories in the modmail system. ",
                    emoji="<:integrations:1272191311234990131>",
                ),
            ]

        super().__init__(options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        from Cogs.Configuration.Configuration import Reset, ConfigMenu, Options

        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        option = interaction.data["values"][0]
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        await Reset(
            interaction,
            lambda: ModmailOptions(interaction.user, self.type),
            lambda: ConfigMenu(Options(config), interaction.user),
        )
        if option == "Category":
            if not config:
                config = {"Modmail": {}, "_id": interaction.guild.id}
            view = discord.ui.View()
            view.add_item(
                Category(
                    self.author,
                    interaction.guild.get_channel(
                        config.get("Modmail", {}).get("category")
                    ),
                    interaction.message,
                )
            )
            await interaction.followup.send(view=view, ephemeral=True)
        elif option == "Transcripts Channel":
            if not config:
                config = {"Modmail": {}, "_id": interaction.guild.id}
            view = discord.ui.View()
            view.add_item(
                Transcript(
                    self.author,
                    interaction.guild.get_channel(
                        config.get("Modmail", {}).get("transcripts")
                    ),
                    interaction.message,
                )
            )

            await interaction.followup.send(view=view, ephemeral=True)
        elif option == "Modmail Pings":
            if not config:
                config = {"Modmail": {}, "_id": interaction.guild.id}
            view = discord.ui.View()
            Role = (
                config.get("Modmail", {}).get("ping", [])[0]
                if config.get("Modmail", {}).get("ping")
                else []
            )
            if not isinstance(Role, list):
                Role = config.get("Modmail", {}).get("ping", [])

            view.add_item(
                ModmailPings(
                    self.author,
                    [role for role in interaction.guild.roles if role.id in Role],
                    interaction.message,
                )
            )
            await interaction.followup.send(view=view, ephemeral=True)
        elif option == "Threads Channel":
            if not config:
                config = {"Modmail": {}, "_id": interaction.guild.id}
            view = discord.ui.View()
            view.add_item(
                ThreadsChannel(
                    self.author,
                    interaction.guild.get_channel(
                        config.get("Modmail", {}).get("threads")
                    ),
                    interaction.message,
                )
            )
            await interaction.followup.send(view=view, ephemeral=True)

        elif option == "Preferences":
            if not config:
                config = {"Module Options": {}, "_id": interaction.guild.id}
            if not config.get("Module Options"):
                config["Module Options"] = {}
            view = Preferences(self.author, interaction.message)
            if config.get("Module Options", {}).get("automessage"):
                view.ModmailButton.label = "Auto Message (Enabled)"
                view.ModmailButton.style = discord.ButtonStyle.green
            if (
                config.get("Module Options", {}).get("MessageFormatting", "Embeds")
                == "Messages"
            ):
                view.UseMessages.label = "Use Messages (Enabled)"
                view.UseMessages.style = discord.ButtonStyle.green
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.description = "> - **Auto Message:** Makes it so whenever you talk in the modmail channel your message automatically gets sent.\n> - **Use Messages:** Make it so all the modmail messages are in messages instead of embeds."

            embed.set_author(
                name="Preferences",
                icon_url="https://cdn.discordapp.com/emojis/1160541147320553562.webp?size=96&quality=lossless",
            )
            await interaction.followup.send(view=view, ephemeral=True, embed=embed)
        elif option == "Modmail Categories":
            view = ModmailCategories(interaction.user)
            if os.getenv("ENVIRONMENT") == "custom":
                view.create.label = "Create"
                view.delete.label = "Delete"
            fields = []
            if config.get("Modmail", {}).get("Categories"):
                for category_name, category in config["Modmail"]["Categories"].items():
                    transcript = (
                        interaction.guild.get_channel(category.get("transcript"))
                        if isinstance(category.get("transcript"), int)
                        else "Not Configured"
                    )
                    if isinstance(transcript, discord.TextChannel):
                        transcript = transcript.mention

                    ping = category.get("ping") if isinstance(category, dict) else None
                    if ping:
                        pingroles = [f"<@&{roleid}>" for roleid in ping]
                        pingroles = ", ".join(pingroles)
                    else:
                        pingroles = "Not Configured"

                    categorychannel = (
                        interaction.guild.get_channel(category.get("category"))
                        if isinstance(category.get("category"), int)
                        else "Not Configured"
                    )
                    if isinstance(categorychannel, discord.CategoryChannel):
                        categorychannel = categorychannel.mention

                    threads = (
                        interaction.guild.get_channel(category.get("threads"))
                        if isinstance(category.get("threads"), int)
                        else "Not Configured"
                    )
                    if isinstance(threads, discord.TextChannel):
                        threads = threads.mention

                    fields.append(
                        {
                            "name": f"{category_name}",
                            "value": (
                                f"`Transcript:` {transcript}\n"
                                f"`Ping:` {pingroles}\n"
                                f"`Category Channel:` {categorychannel}\n"
                                f"`Threads Channel:` {threads}"
                            ),
                            "inline": False,
                        }
                    )

            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_author(
                name="Modmail Categories",
                icon_url="https://cdn.discordapp.com/emojis/1272191311234990131.webp?size=96?quality=lossless",
            )

            for field in fields[:25]:
                embed.add_field(
                    name=field["name"], value=field["value"], inline=field["inline"]
                )

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class ThreadsChannel(discord.ui.ChannelSelect):
    def __init__(self, author: discord.User, default, message: discord.Message):
        super().__init__(
            placeholder="Select Channel",
            channel_types=[discord.ChannelType.text],
            default_values=[default] if default else None,
        )
        self.author = author
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != self.author.id:

            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if not config.get("Modmail"):
            config["Modmail"] = {}
        config["Modmail"]["threads"] = self.values[0].id if self.values else None
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}, upsert=True
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )
        await interaction.edit_original_response(content=None)
        try:
            await self.message.edit(
                embed=await ModmailEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")


class Preferences(discord.ui.View):
    def __init__(self, author: discord.User, message: discord.Message):
        super().__init__()
        self.author = author
        self.message = message

    async def ToggleOption(
        self, interaction: discord.Interaction, button: discord.ui.Button, Option: str
    ):
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Module Options": {}, "_id": interaction.guild.id}
        if not config.get("Module Options"):
            config["Module Options"] = {}

        if Option == "automessage":
            if config.get("Module Options", {}).get("automessage"):
                config["Module Options"]["automessage"] = False
                button.label = "Auto Message (Disabled)"
                button.style = discord.ButtonStyle.red
            else:
                config["Module Options"]["automessage"] = True
                button.label = "Auto Message (Enabled)"
                button.style = discord.ButtonStyle.green
        elif Option == "MessageFormatting":
            if config.get("Module Options", {}).get("MessageFormatting") == "Messages":
                config["Module Options"]["MessageFormatting"] = "Embeds"
                button.label = "Use Messages (Disabled)"
                button.style = discord.ButtonStyle.red
            else:
                config["Module Options"]["MessageFormatting"] = "Messages"
                button.label = "Use Messages (Enabled)"
                button.style = discord.ButtonStyle.green

        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Auto Message (Disabled)", style=discord.ButtonStyle.red)
    async def ModmailButton(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "automessage")

    @discord.ui.button(label="Use Messages (Disabled)", style=discord.ButtonStyle.red)
    async def UseMessages(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "MessageFormatting")

    @discord.ui.button(
        label="Modmail Type",
        style=discord.ButtonStyle.grey,
        emoji="<:List:1223063187063308328>",
    )
    async def ModmailType(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        view = discord.ui.View()
        view.add_item(SelectModmailType(self.author, self.message))
        await interaction.followup.send(view=view, ephemeral=True)


class SelectModmailType(discord.ui.Select):
    def __init__(self, author: discord.User, message: discord.Message):
        super().__init__(
            placeholder="Select Modmail Type",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Threads",
                    value="threads",
                ),
                discord.SelectOption(
                    label="Channel",
                    value="channel",
                ),
            ],
        )
        self.author = author
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        from Cogs.Configuration.Configuration import ConfigMenu, Options

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Module Options": {}, "_id": interaction.guild.id}
        if not config.get("Module Options"):
            config["Module Options"] = {}
        config["Module Options"]["ModmailType"] = self.values[0]
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.response.edit_message(
            content=f"{tick} {interaction.user.display_name}, the modmail type has been updated to {self.values[0]}.",
            view=None,
        )

        try:
            view = discord.ui.View()
            view.add_item(
                ModmailOptions(
                    self.author,
                    self.values[0],
                )
            )
            view.add_item(ConfigMenu(Options(config), interaction.user))

            await self.message.edit(
                embed=await ModmailEmbed(interaction, config, discord.Embed()),
                view=view,
            )

            await self.message.edit(
                embed=await ModmailEmbed(interaction, config, discord.Embed()),
                view=view,
            )
        except Exception as e:
            logger.error(str(e))


################################# MODMAIL CATEGORIES


class ModmailCategories(discord.ui.View):
    def __init__(self, user: discord.member):
        super().__init__(timeout=360)
        self.user = user

    @discord.ui.button(emoji="<:Add:1163095623600447558>")
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if not config.get("Modmail"):
            config["Modmail"] = {}
        if 3 <= len(config.get("Modmail", {}).get("Categories", [])):
            if not await premium(interaction.guild.id):
                embed = discord.Embed(
                    description=f"{redx} **{interaction.user.display_name},** you've reached the maximum amount of categories!\n-# Upgrade to premium for unlimited.",
                    color=discord.Colour.brand_red(),
                )
                return await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )

        await interaction.response.send_modal(CreateCategory(interaction.user))

    @discord.ui.button(emoji="<:Subtract:1229040262161109003>")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if not config.get("Modmail"):
            config["Modmail"] = {}
        if not config.get("Modmail").get("Categories"):
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** there are no categories to delete!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_modal(DeleteCategory(interaction.user))


class DeleteCategory(discord.ui.Modal):
    def __init__(self, user: discord.User):
        super().__init__(title="Modmail Categories")
        self.user = user
        self.add_item(
            discord.ui.TextInput(
                label="Name",
                placeholder="What category should be deleted?",
                style=discord.TextStyle.short,
                required=True,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        name = self.children[0].value
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if not config.get("Modmail"):
            config["Modmail"] = {}
        if not config.get("Modmail").get("Categories"):
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** there are no categories to delete!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if name not in config.get("Modmail", {}).get("Categories", []):
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this category doesn't exist!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        del config["Modmail"]["Categories"][name]
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name},** the category `{name}` has been deleted.",
            view=None,
            embed=None,
        )


class CreateCategory(discord.ui.Modal):
    def __init__(self, user: discord.User):
        super().__init__(title="Modmail Categories")
        self.user = user
        self.add_item(
            discord.ui.TextInput(
                label="Name",
                placeholder="What should the category be called?",
                style=discord.TextStyle.short,
                required=True,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer()
        name = self.children[0].value
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if not config.get("Modmail"):
            config["Modmail"] = {}
        if not config.get("Modmail").get("Categories"):

            config["Modmail"]["Categories"] = []
        if name in config.get("Modmail", {}).get("Categories", []):
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this category already exists!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if config.get("Module Options", {}).get("ModmailType") == "threads":
            options = [
                discord.SelectOption(
                    label="Ping", value="Ping", emoji="<:Ping:1298301862906298378>"
                ),
                discord.SelectOption(
                    label="Threads Channel",
                    value="Threads Channel",
                    emoji="<:threads:1248312604733210735>",
                ),
            ]

        else:
            options = [
                discord.SelectOption(
                    label="Ping", value="Ping", emoji="<:Ping:1298301862906298378>"
                ),
                discord.SelectOption(
                    label="Category",
                    value="Category",
                    emoji="<:category:1248312604733210735>",
                ),
                discord.SelectOption(
                    label="Transcript Channel",
                    value="Transcript Channel",
                    emoji="<:tag:1234998802948034721>",
                ),
            ]
        view = NoThanks(self.user, name)
        view.add_item(CategoryType(interaction.user, name, options))
        await interaction.edit_original_response(
            content=f"{Settings} **{interaction.user.display_name},** do you want to add extra stuff to this modmail category?",
            view=view,
            embed=None,
        )


class NoThanks(discord.ui.View):
    def __init__(self, user: discord.Member, name: str):
        super().__init__()
        self.name = name
        self.user = user

    @discord.ui.button(label="Finished", style=discord.ButtonStyle.green, row=2)
    async def Finished(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name},** I've created the modmail category for you.",
            view=None,
        )

    @discord.ui.button(label="No Thanks", style=discord.ButtonStyle.red, row=2)
    async def NahImGood(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if not config.get("Modmail"):
            config["Modmail"] = {}
        if not config.get("Modmail").get("Categories"):
            config["Modmail"]["Categories"] = {}
        if self.name in config.get("Modmail", {}).get("Categories", []):
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this category already exists!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        config["Modmail"]["Categories"].append(self.name)
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )

        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name}**, No problem! I've created the modmail category for you!",
            view=None,
        )


class CategoryType(discord.ui.Select):
    def __init__(self, user: discord.User, name, options):
        super().__init__(options=options)
        self.user = user
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        selection = self.values[0]
        if selection == "Transcript Channel":
            view = discord.ui.View()
            view.add_item(TranscriptChannel(self.user, self.name))
            await interaction.response.send_message(view=view, ephemeral=True)
        elif selection == "Ping":
            view = discord.ui.View()
            view.add_item(PingRoles(self.user, self.name))
            await interaction.response.send_message(view=view, ephemeral=True)
        elif selection == "Category":
            view = discord.ui.View()
            view.add_item(CategoryChannel(self.user, self.name))
            await interaction.response.send_message(view=view, ephemeral=True)
        elif selection == "Threads Channel":
            view = discord.ui.View()
            view.add_item(Threads(self.user, self.name))
            await interaction.response.send_message(view=view, ephemeral=True)


class Threads(discord.ui.ChannelSelect):
    def __init__(self, user: discord.User, name):
        super().__init__(
            placeholder="Select Threads Channel",
            channel_types=[discord.ChannelType.text],
        )
        self.user = user
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if "Modmail" not in config:
            config["Modmail"] = {}
        if "Categories" not in config["Modmail"]:
            config["Modmail"]["Categories"] = {}
        if self.name not in config["Modmail"]["Categories"]:
            config["Modmail"]["Categories"][self.name] = {}
        config["Modmail"]["Categories"][self.name]["threads"] = (
            self.values[0].id if self.values else None
        )
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name},** Successfully set threads channel for `{self.name}`.",
            view=None,
        )


class TranscriptChannel(discord.ui.ChannelSelect):
    def __init__(self, user: discord.User, name):
        super().__init__(
            placeholder="Select Transcript Channel",
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.user = user
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if "Modmail" not in config:
            config["Modmail"] = {}
        if "Categories" not in config["Modmail"]:
            config["Modmail"]["Categories"] = {}
        if self.name not in config["Modmail"]["Categories"]:
            config["Modmail"]["Categories"][self.name] = {}
        config["Modmail"]["Categories"][self.name]["transcript"] = (
            self.values[0].id if self.values else None
        )
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name},** Successfully set transcript channel for `{self.name}`.",
            view=None,
        )


class CategoryChannel(discord.ui.ChannelSelect):
    def __init__(self, user: discord.User, name):
        super().__init__(
            placeholder="Select Category",
            channel_types=[discord.ChannelType.category],
        )
        self.user = user
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if "Modmail" not in config:
            config["Modmail"] = {}
        if "Categories" not in config["Modmail"]:
            config["Modmail"]["Categories"] = {}
        if self.name not in config["Modmail"]["Categories"]:
            config["Modmail"]["Categories"][self.name] = {}
        config["Modmail"]["Categories"][self.name]["category"] = (
            self.values[0].id if self.values else None
        )
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name},** Successfully set category for `{self.name}`.",
            view=None,
        )


class PingRoles(discord.ui.RoleSelect):
    def __init__(self, user: discord.User, name):
        super().__init__(placeholder="Select Roles to Ping", max_values=25)
        self.user = user
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description=f"{redx} **{interaction.user.display_name},** this is not your view",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if "Modmail" not in config:
            config["Modmail"] = {}
        if "Categories" not in config["Modmail"]:
            config["Modmail"]["Categories"] = {}
        if self.name not in config["Modmail"]["Categories"]:
            config["Modmail"]["Categories"][self.name] = {}
        config["Modmail"]["Categories"][self.name]["ping"] = [
            role.id for role in self.values
        ]
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name},** Successfully set ping roles for `{self.name}`.",
            view=None,
        )


#####################################################################################################################################################################


class ModmailPings(discord.ui.RoleSelect):
    def __init__(self, author: discord.User, default, message: discord.Message):
        super().__init__(
            placeholder="Select Roles",
            min_values=0,
            max_values=25,
            default_values=default if default else None,
        )
        self.author = author
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"Modmail": {}, "_id": interaction.guild.id}
        if not config.get("Modmail"):
            config["Modmail"] = {}
        if self.values:
            config["Modmail"]["ping"] = [role.id for role in self.values]
        else:
            config["Modmail"].pop("ping", None)
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}, upsert=True
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )
        try:
            await self.message.edit(
                embed=await ModmailEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class Category(discord.ui.ChannelSelect):
    def __init__(self, author: discord.User, default, message: discord.Message):
        super().__init__(
            default_values=[default] if default else None,
            channel_types=[discord.ChannelType.category],
        )
        self.author = author
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        try:
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            if not config:
                config = {"Modmail": {}, "_id": interaction.guild.id}
            if not config.get("Modmail"):
                config["Modmail"] = {}
            config["Modmail"]["category"] = self.values[0].id if self.values else None
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$set": config}, upsert=True
            )
            Updated = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            await self.message.edit(
                embed=await ModmailEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except Exception as e:
            traceback.print_exc(e)


class Transcript(discord.ui.ChannelSelect):
    def __init__(self, author: discord.User, default, message: discord.Message):
        super().__init__(
            default_values=[default] if default else [],
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.defer()
        try:
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            if not config:
                config = {"Modmail": {}, "_id": interaction.guild.id}
            if not config.get("Modmail"):
                config["Modmail"] = {}

            config["Modmail"]["transcripts"] = (
                self.values[0].id if self.values else None
            )
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$set": config}, upsert=True
            )
            Updated = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            await interaction.edit_original_response(content=None)
            try:
                await self.message.edit(
                    embed=await ModmailEmbed(
                        interaction,
                        Updated,
                        discord.Embed(color=discord.Color.dark_embed()),
                    ),
                )
            except:
                pass
        except Exception as e:
            traceback.print_exc(e)


async def ModmailEmbed(
    interaction: discord.Interaction, Config: dict, embed: discord.Embed
):
    config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not config:
        config = {"Modmail": {}, "_id": interaction.guild.id}
    Category = (
        interaction.guild.get_channel(config.get("Modmail", {}).get("category"))
        or "Not Configured"
    )
    if isinstance(Category, discord.TextChannel):
        Category = Category.mention

    Transcripts = (
        interaction.guild.get_channel(config.get("Modmail", {}).get("transcripts"))
        or "Not Configured"
    )

    Role = (
        config.get("Modmail", {}).get("ping", [])[0]
        if config.get("Modmail", {}).get("ping")
        else "Not Configured"
    )
    if not isinstance(Role, list):
        Role = config.get("Modmail", {}).get("ping", [])

    if isinstance(Role, list):
        ModmailRoles = [f"<@&{int(roleid)}>" for roleid in Role]
        ModmailRoles = ", ".join(ModmailRoles) if ModmailRoles else "Not Configured"
    else:
        try:
            ModmailRoles = f"<@&{int(Role)}>"
        except TypeError:
            ModmailRoles = "Not Configured"

    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's modmail settings! Modmail is a way for users to contact staff. You can find out more at [the documentation](https://docs.astrobirb.dev/Modules/modmail)."
    if config.get("Module Options", {}).get("ModmailType", "channel") == "channel":
        value = f"{replytop} `Category:` {Category}\n{replymiddle} `Transcripts:` {Transcripts}\n{replybottom} `Roles:` {ModmailRoles}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev/Modules/modmail)."

    else:
        value = f"{replytop} `Threads Channel:` <#{config.get('Modmail', {}).get('threads', 'Not Configured')}>\n{replybottom} `Roles:` {ModmailRoles}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev/Modules/modmail)."

    embed.add_field(
        name="<:settings:1207368347931516928> Modmail",
        value=value,
        inline=False,
    )

    return embed
