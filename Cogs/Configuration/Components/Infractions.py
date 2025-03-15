import discord
import discord.http
import traceback

from utils.emojis import *

from dotenv import load_dotenv
from utils.format import IsSeperateBot
from utils.permissions import premium
from utils.HelpEmbeds import NoPremium, Support

load_dotenv()


class InfractionOption(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Infraction Channel", emoji="<:tag:1234998802948034721>"
                ),
                discord.SelectOption(
                    label="Infraction Audit Log",
                    emoji="<:Log:1349431938926252115>",
                    description="Logs for creation/void/modify.",
                ),
                discord.SelectOption(
                    label="Infraction Types",
                    emoji="<:gridiconstypes:1248299279513161829>",
                ),
                discord.SelectOption(
                    label="Infraction Approval",
                    description="Make infractions go through an approval system.",
                    emoji="<:Approval:1340271794694914058>",
                ),
                discord.SelectOption(
                    label="Preferences", emoji="<:leaf:1160541147320553562>"
                ),
                discord.SelectOption(
                    label="Customise Embed",
                    emoji="<:Customisation:1223063306131210322>",
                ),
                discord.SelectOption(
                    label="Preset Reasons", emoji="<:auto:1280563201662255137>"
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
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer()
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {
                "Infraction": {},
                "Module Options": {},
                "_id": interaction.guild.id,
            }

        view = discord.ui.View()

        selection = self.values[0]
        embed = discord.Embed(color=discord.Colour.dark_embed())

        if selection == "Infraction Channel":
            view.add_item(
                InfractionChannel(
                    interaction.user,
                    interaction.guild.get_channel(
                        Config.get("Infraction", {}).get("channel"),
                    ),
                    interaction.message,
                )
            )
        if selection == "Infraction Audit Log":
            view.add_item(
                LogChannel(
                    interaction.user,
                    interaction.guild.get_channel(
                        Config.get("Infraction", {}).get("LogChannel"),
                    ),
                    interaction.message,
                )
            )
        elif selection == "Infraction Types":
            view.add_item(ManageTypes(author=self.author, message=interaction.message))
        elif selection == "Preferences":
            view = Preferences(author=self.author)
            if not Config.get("Module Options"):
                Config["Module Options"] = {}
            view.children[0].style = (
                discord.ButtonStyle.green
                if Config.get("Module Options", {}).get("infractedbybutton", False)
                else discord.ButtonStyle.red
            )
            view.children[0].label = (
                "Issuer Button Display (Enabled)"
                if Config.get("Module Options", {}).get("infractedbybutton", False)
                else "Issuer Button Display (Disabled)"
            )
            view.children[1].style = (
                discord.ButtonStyle.green
                if Config.get("Module Options", {}).get("onvoid", False)
                else discord.ButtonStyle.red
            )
            view.children[1].label = (
                "Notify On Void (Enabled)"
                if Config.get("Module Options", {}).get("onvoid", False)
                else "Notify On Void (Disabled)"
            )
            view.children[2].style = (
                discord.ButtonStyle.green
                if Config.get("Module Options", {}).get("showissuer", False)
                else discord.ButtonStyle.red
            )

            view.children[2].label = (
                "Show Issuer (Enabled)"
                if Config.get("Module Options", {}).get("showissuer", True)
                else "Show Issuer (Disabled)"
            )
            view.children[3].style = (
                discord.ButtonStyle.green
                if Config.get("Module Options", {}).get(
                    "Infraction Confirmation", False
                )
                else discord.ButtonStyle.red
            )
            view.children[4].style = (
                discord.ButtonStyle.green
                if Config.get("Module Options", {}).get("Direct Message", True)
                else discord.ButtonStyle.red
            )
            view.children[4].label = (
                "Direct Messages (Enabled)"
                if Config.get("Module Options", {}).get("Direct Message", True)
                else "Direct Messages (Disabled)"
            )
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.description = f"> - **Infraction User Button:** It shows a **Issued By {interaction.user.display_name}** under the infraction embed\n> - **Notify On Void: ** It notifies the infracted staff member when their punishment is voided.\n> - **Show Issuer**: Disabling this will make it so the person infracting won't appear on the infraction embed. This won't work on customised embeds. The issuer will still appear on /infractions & all.\n> - **Infraction Confirmation:** Enables or disables confirmation prompts for infractions.\n> - **Direct Messages:** Enables or disables messages to staff members."

            embed.set_author(
                name="Preferences",
                icon_url="https://cdn.discordapp.com/emojis/1160541147320553562.webp?size=96&quality=lossless",
            )
            return await interaction.followup.send(
                view=view, embed=embed, ephemeral=True
            )
        elif selection == "Preset Reasons":
            if not await premium(interaction.guild.id):
                return await interaction.followup.send(
                    embed=NoPremium(), view=Support()
                )
            view = ManageReasons(author=self.author, message=interaction.message)
            if IsSeperateBot():
                view.RemoveReason.label = "Remove"
                view.AddReason.label = "Add"

        elif selection == "Customise Embed":
            try:
                custom = await interaction.client.db["Customisation"].find_one(
                    {"guild_id": interaction.guild.id, "type": "Infractions"}
                )
                embed = None

                from Cogs.Configuration.Components.EmbedBuilder import (
                    DisplayEmbed,
                    Embed,
                )

                if not custom:
                    embed = discord.Embed(color=discord.Color.dark_embed())
                    embed.title = "Staff Consequences & Discipline"
                    embed.description = "- **Staff Member:** {staff.mention}\n- **Action:** {action}\n- **Reason:** {reason}"
                    embed.set_author(
                        name="Signed, {author.name}",
                        icon_url=interaction.user.display_avatar,
                    )
                    embed.color = discord.Color.dark_embed()
                    embed.set_thumbnail(url=interaction.user.display_avatar)
                    view = Embed(
                        interaction.user,
                        FinalFunction,
                        "Infractions",
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
                    "Infractions",
                    {
                        "thumb": (
                            interaction.user.display_avatar.url
                            if custom.get("embed", {}).get("thumbnail")
                            == "{author.avatar}"
                            else (
                                "{staff.avatar}"
                                if custom.get("embed", {}).get("thumbnail")
                                == "{staff.avatar}"
                                else custom.get("embed", {}).get("thumbnail", "")
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
                                .get("icon_url", "")
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
        elif selection == "Infraction Approval":
            view.add_item(
                ApprovalChannel(
                    interaction.user,
                    interaction.guild.get_channel(
                        Config.get("Infraction", {}).get("Approval", {}).get("channel"),
                    ),
                    interaction.message,
                )
            )
            view.add_item(
                ApprovalRole(
                    interaction.user,
                    interaction.guild.get_role(
                        Config.get("Infraction", {}).get("Approval", {}).get("Ping"),
                    ),
                    interaction.message,
                )
            )
        await interaction.followup.send(view=view, ephemeral=True)


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
    await interaction.client.db["Customisation"].update_one(
        {"guild_id": interaction.guild.id, "type": "Infractions"},
        {"$set": data},
        upsert=True,
    )
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})

    view = discord.ui.View()
    view.add_item(InfractionOption(interaction.user))
    view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
    await interaction.response.edit_message(
        embed=await InfractionEmbed(
            interaction, Config, discord.Embed(color=discord.Color.dark_embed())
        ),
        view=view,
    )


class ApprovalChannel(discord.ui.ChannelSelect):
    def __init__(
        self,
        author: discord.Member,
        channel: discord.TextChannel = None,
        message: discord.Message = None,
    ):
        super().__init__(
            placeholder="Approval Channel",
            min_values=0,
            max_values=1,
            default_values=[channel] if channel else [],
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.channel = channel
        self.message = message

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Infraction": {}}
        elif "Infraction" not in config:
            config["Infraction"] = {}
        elif "Approval" not in config.get("Infraction", {}):
            config["Infraction"]["Approval"] = {}

        config["Infraction"]["Approval"]["channel"] = (
            self.values[0].id if self.values else None if self.values else None
        )
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await InfractionEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class ApprovalRole(discord.ui.RoleSelect):
    def __init__(
        self,
        author: discord.Member,
        role: discord.Role = None,
        message: discord.Message = None,
    ):
        super().__init__(
            min_values=0,
            max_values=1,
            default_values=[role] if role else [],
            placeholder="Approval Ping",
        )
        self.author = author
        self.role = role
        self.message = message

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Infraction": {}}
        elif "Infraction" not in config:
            config["Infraction"] = {}
        elif "Approval" not in config.get("Infraction", {}):
            config["Infraction"]["Approval"] = {}

        config["Infraction"]["Approval"]["Ping"] = (
            self.values[0].id if self.values else None if self.values else None
        )
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await InfractionEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class ManageReasons(discord.ui.View):
    def __init__(self, author: discord.Member, message: discord.Message = None):
        super().__init__(timeout=360)
        self.author = author
        self.message = message

    @discord.ui.button(label="", emoji="<:Add:1163095623600447558>")
    async def AddReason(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.response.send_modal(
            AddAndRemove(self.author, "add", self.message)
        )

    @discord.ui.button(label="", emoji="<:Subtract:1229040262161109003>")
    async def RemoveReason(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {
                "Infraction": {},
                "Module Options": {},
                "_id": interaction.guild.id,
            }
        if Config.get("Infraction", {}).get("reasons") is not None:
            await interaction.response.send_modal(
                AddAndRemove(self.author, "remove", self.message)
            )
        else:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** there are no preset reasons to remove!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)


class AddAndRemove(discord.ui.Modal, title="Preset Reasons"):
    def __init__(self, author: discord.Member, type: str, message: discord.Message):
        super().__init__()
        self.author = author
        self.type = type
        self.message = message
        self.reason = discord.ui.TextInput(
            label=f"{'Add' if type == 'add' else 'Remove'} Preset Reason",
            placeholder="Example: Being an idiot, staff abuse.",
            required=True,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {
                "Infraction": {},
                "Module Options": {},
                "_id": interaction.guild.id,
            }
        if self.type == "add":
            if Config.get("Infraction", {}).get("reasons") is None:
                Config["Infraction"]["reasons"] = []
            if self.reason.value in Config["Infraction"]["reasons"]:
                embed = discord.Embed(
                    description=f"  **{interaction.user.display_name},** this preset reason already exists!",
                    color=discord.Colour.brand_red(),
                )
                return await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )
            Config["Infraction"]["reasons"].append(self.reason.value)
        elif self.type == "remove":
            if self.reason.value not in Config["Infraction"]["reasons"]:
                embed = discord.Embed(
                    description=f"  **{interaction.user.display_name},** this preset reason doesn't exist!",
                    color=discord.Colour.brand_red(),
                )
                return await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )
            Config["Infraction"]["reasons"].remove(self.reason.value)
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": Config}
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name}**, {self.reason.value} has been {'added' if self.type == 'add' else 'removed'} to the preset reasons!",
            view=None,
        )
        try:
            await self.message.edit(
                embed=await InfractionEmbed(
                    interaction, Config, discord.Embed(color=discord.Color.dark_embed())
                )
            )
        except:
            pass


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
        if Config["Module Options"].get(Option, False):
            Config["Module Options"][Option] = False
            button.style = discord.ButtonStyle.red
            button.label = button.label.replace("(Enabled)", "(Disabled)")
        else:
            Config["Module Options"][Option] = True
            button.style = discord.ButtonStyle.green
            button.label = button.label.replace("(Disabled)", "(Enabled)")

        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": Config}
        )
        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        label="Issuer Button Display (Disabled)", style=discord.ButtonStyle.red
    )
    async def IssuerButton(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "infractedbybutton")

    @discord.ui.button(label="Notify On Void (Enabled)", style=discord.ButtonStyle.red)
    async def NotifyOnVoid(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "onvoid")

    @discord.ui.button(label="Show Issuer (Disable)", style=discord.ButtonStyle.green)
    async def ShowIssuer(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "showissuer")

    @discord.ui.button(
        label="Infraction Confirmation (Disable)", style=discord.ButtonStyle.green
    )
    async def Confirmation(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "Infraction Confirmation")

    @discord.ui.button(
        label="Direct Messages (Disable)", style=discord.ButtonStyle.green
    )
    async def DirectMessage(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "Direct Message")


class ManageTypes(discord.ui.Select):  # Infraction Types
    def __init__(self, author: discord.Member, message: discord.Message = None):
        super().__init__(
            options=[
                discord.SelectOption(label="Add"),
                discord.SelectOption(label="Remove"),
                discord.SelectOption(label="Edit"),
            ]
        )
        self.author = author
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        selection = self.values[0]
        if selection == "Add":
            await interaction.response.send_modal(
                InfractionTypeModal(interaction.user, "add", self.message)
            )
            return
        elif selection == "Edit":
            await interaction.response.send_modal(
                InfractionTypeModal(interaction.user, "edit", self.message)
            )
            return

        elif selection == "Remove":
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            if config.get("Infraction", {}).get("types") is not None:
                await interaction.response.send_modal(
                    InfractionTypeModal(interaction.user, "remove", self.message)
                )
                return

            else:
                embed = discord.Embed(
                    description=f"  **{interaction.user.display_name},** there are no infraction types to remove!",
                    color=discord.Colour.brand_red(),
                )
                return await interaction.followup.send(embed=embed, ephemeral=True)


class InfractionTypeModal(discord.ui.Modal, title="Infraction Type"):
    def __init__(
        self,
        author: discord.Member,
        type: str,
        message: discord.Message = None,
    ):
        super().__init__()
        self.author = author
        self.type = type
        self.message = message
        self.name = discord.ui.TextInput(
            label=f"{'Add' if type == 'add' else 'Edit' if type == 'edit' else 'Remove'} Infraction Type",
            placeholder="Example: Warning, Strike, Activity Notice",
            required=True,
        )
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Infraction": {}}
        elif "Infraction" not in config:
            config["Infraction"] = {}
        if self.type == "add":
            if self.name in config.get("Infraction").get("types"):
                embed = discord.Embed(
                    description=f"  **{interaction.user.display_name},** this infraction type already exists!",
                    color=discord.Colour.brand_red(),
                )
                return await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )

        if self.type == "add":
            if config.get("Infraction").get("types") is None:
                config["Infraction"]["types"] = []
            config["Infraction"]["types"].append(self.name.value)
        elif self.type == "remove":

            if config.get("Infraction").get("types") is not None:
                if not self.name.value in config.get("Infraction").get("types"):
                    embed = discord.Embed(
                        description=f"  **{interaction.user.display_name},** this infraction type doesn't exist.",
                        color=discord.Colour.brand_red(),
                    )
                    return await interaction.response.send_message(
                        embed=embed, ephemeral=True
                    )
                config["Infraction"]["types"].remove(self.name.value)
        view = discord.ui.View()
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )
        if self.type == "add":
            view = NoThanks()
            view.add_item(InfractionTypesAction(self.author, self.name.value))
            return await interaction.response.edit_message(
                content=f"  **{interaction.user.display_name}**, Do you want to add extra stuff to this infraction type?",
                view=view,
            )
        elif self.type == "edit":
            if self.name.value not in config["Infraction"].get("types", []):
                embed = discord.Embed(
                    description=f"  **{interaction.user.display_name},** there isn't an infraction type named this.",
                    color=discord.Colour.brand_red(),
                )
                return await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )
            view = Done()
            view.add_item(InfractionTypesAction(self.author, self.name.value))
            return await interaction.response.edit_message(
                content=f"  **{interaction.user.display_name}**, you are now editing the infraction type.",
                view=view,
            )

        else:
            self.type == "remove"
            await interaction.response.edit_message(content="")
            try:
                await self.message.edit(
                    embed=await InfractionEmbed(
                        interaction,
                        Config=Updated,
                        embed=discord.Embed(color=discord.Color.dark_embed()),
                    )
                )
            except:
                pass


class NoThanks(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()

    @discord.ui.button(label="No Thanks", style=discord.ButtonStyle.red, row=1)
    async def NahImGood(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** No problem! I've created the infraction type for you!",
            view=None,
        )


class InfractionChannel(discord.ui.ChannelSelect):
    def __init__(
        self,
        author: discord.Member,
        channel: discord.TextChannel = None,
        message: discord.Message = None,
    ):
        super().__init__(
            placeholder="Infraction Channel",
            min_values=0,
            max_values=1,
            default_values=[channel] if channel else [],
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.channel = channel
        self.message = message

    async def callback(self, interaction):
        from Cogs.Configuration.Configuration import ConfigMenu, Options

        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Infraction": {}}
        elif "Infraction" not in config:
            config["Infraction"] = {}
        elif "channel" not in config.get("Infraction", {}):
            config["Infraction"]["channel"] = None

        config["Infraction"]["channel"] = self.values[0].id if self.values else None
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await InfractionEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class LogChannel(discord.ui.ChannelSelect):
    def __init__(
        self,
        author: discord.Member,
        channel: discord.TextChannel = None,
        message: discord.Message = None,
    ):
        super().__init__(
            placeholder="Audit Log Channel",
            min_values=0,
            max_values=1,
            default_values=[channel] if channel else [],
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.channel = channel
        self.message = message

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Infraction": {}}
        elif "Infraction" not in config:
            config["Infraction"] = {}
        elif "LogChannel" not in config.get("Infraction", {}):
            config["Infraction"]["LogChannel"] = None

        config["Infraction"]["LogChannel"] = self.values[0].id
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await InfractionEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


class InfractionTypesAction(discord.ui.Select):
    def __init__(self, author, name):
        self.author = author
        self.name = name
        options = [
            discord.SelectOption(
                label="Send to channel", emoji="<:tag:1234998802948034721>"
            ),
            discord.SelectOption(
                label="Give Roles", emoji="<:Promotion:1234997026677198938>"
            ),
            discord.SelectOption(
                label="Remove Roles", emoji="<:Infraction:1223063128275943544>"
            ),
            discord.SelectOption(
                label="Staff Database Removal", emoji="<:staffdb:1206253848298127370>"
            ),
            discord.SelectOption(
                label="Escalate", emoji="<:escalate:1340246894013841440>"
            ),
            discord.SelectOption(
                label="Void Shift",
                emoji="<:erm:1203823601107861504>",
                description="Requires ERM API",
            ),
            discord.SelectOption(
                label="Change Group Role", emoji="<:robloxWhite:1200584000390053899>"
            ),
        ]
        super().__init__(
            placeholder="Select Infraction Actions",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"  This is not your panel!",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        from utils.roblox import GroupRoles

        filter = {"guild_id": interaction.guild.id, "name": self.name}
        update_data = {"name": self.name}
        view = discord.ui.View()

        action_mapping = {
            "Send to channel": TypeChannel,
            "Give Roles": GiveRoles,
            "Remove Roles": RemoveRoles,
            "Change Group Role": ChangeGroupRole,
        }

        option = self.values[0]
        if option == "Escalate":
            await interaction.response.send_modal(Escalate(self.name))
            return
        if option == "Change Group Role":
            Roles = await GroupRoles(interaction)
            if Roles == 0:
                from utils.HelpEmbeds import NotRobloxLinked

                return await interaction.response.send_message(
                    embed=NotRobloxLinked(), ephemeral=True
                )
            if Roles == 1:

                return await interaction.response.send_message(
                    f"  **{interaction.user.display_name},** you don't have access to the groups roles.",
                    ephemeral=True,
                )
            if Roles == 2:
                return await interaction.response.send_message(
                    f"  **{interaction.user.display_name},** a group hasn't been linked.",
                    ephemeral=True,
                )
            Roles = Roles.get("groupRoles")
            options = []
            for role in Roles:
                options.append(
                    discord.SelectOption(
                        label=f"{role.get('displayName')}",
                        value=role.get("path"),
                    )
                )
            view.add_item(ChangeGroupRole(self.author, self.name, options))

        if option in action_mapping and option != "Change Group Role":
            view.add_item(action_mapping[option](self.author, self.name))
        else:
            update_data[option.lower().replace(" ", "")] = True

        await interaction.client.db["infractiontypeactions"].update_one(
            filter, {"$set": update_data}, upsert=True
        )
        await interaction.response.edit_message(
            content=f"  Infraction type successfully updated.",
            view=view if view.children else None,
        )


class Done(discord.ui.View):
    class Done(discord.ui.Button):
        def __init__(
            self, label: str, style: discord.ButtonStyle, author: discord.Member
        ):
            super().__init__(label=label, style=style, row=3)
            self.author = author

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.author.id:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        description=f"  This is not your panel!",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            await interaction.response.edit_message(
                content=f"  **{interaction.user.display_name},** succesfully updated infraction type.",
                view=None,
            )


class Escalate(discord.ui.Modal, title="Escalate"):
    def __init__(self, type: str):
        super().__init__()
        self.threshold = discord.ui.TextInput(
            label="Threshold",
            placeholder="Number of infractions with this type needed before escalating",
        )
        self.nexttype = discord.ui.TextInput(
            label="Escalated To",
            placeholder="What type is added after reaching the threshold",
        )
        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="The infraction reason after hitting the threshold.",
        )
        self.add_item(self.threshold)
        self.add_item(self.nexttype)
        self.add_item(self.reason)
        self.type = type

    async def on_submit(self, interaction: discord.Interaction):
        Result = await interaction.client.db["infractiontypeactions"].find_one(
            {"guild_id": interaction.guild.id, "name": self.type}
        )
        if not Result:
            Result = {"guild_id": interaction.guild.id, "name": self.type}

        if not Result.get("Escalation"):
            Result.update({"Escalation": {}})

        Result["Escalation"]["Threshold"] = self.threshold.value
        Result["Escalation"]["Next Type"] = self.nexttype.value
        Result["Escalation"]["Reason"] = self.reason.value
        if "_id" in Result:
            del Result["_id"]
        await interaction.client.db["infractiontypeactions"].update_one(
            {"guild_id": interaction.guild.id, "name": self.type}, {"$set": Result}
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** succesfully updated infraction type.",
            view=None,
        )


class TypeChannel(discord.ui.ChannelSelect):
    def __init__(self, author, name):
        super().__init__(
            placeholder="Select a Channel",
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author, self.name = author, name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"  This is not your panel!",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        filter = {"guild_id": interaction.guild.id, "name": self.name}
        await interaction.client.db["infractiontypeactions"].update_one(
            filter,
            {"$set": {"channel": self.values[0].id if self.values else None}},
            upsert=True,
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** succesfully updated infraction type.",
            view=None,
        )


class RemoveRoles(discord.ui.RoleSelect):
    def __init__(self, author, name):
        super().__init__(placeholder="Select Removed Roles", max_values=10)
        self.author, self.name = author, name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"  This is not your panel!",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        filter = {"guild_id": interaction.guild.id, "name": self.name}
        await interaction.client.db["infractiontypeactions"].update_one(
            filter,
            {"$set": {"removedroles": [role.id for role in self.values]}},
            upsert=True,
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** succesfully updated infraction type.",
            view=None,
        )


class GiveRoles(discord.ui.RoleSelect):
    def __init__(self, author, name):
        super().__init__(placeholder="Select Given Roles", max_values=10)
        self.author, self.name = author, name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"  This is not your panel!",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        filter = {"guild_id": interaction.guild.id, "name": self.name}
        await interaction.client.db["infractiontypeactions"].update_one(
            filter,
            {"$set": {"givenroles": [role.id for role in self.values]}},
            upsert=True,
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** succesfully updated infraction type.",
            view=None,
        )


class ChangeGroupRole(discord.ui.Select):
    def __init__(self, author, name, options):
        super().__init__(
            options=options, placeholder="What should we change their role to?"
        )
        self.author, self.name = author, name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"  This is not your panel!",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        filter = {"guild_id": interaction.guild.id, "name": self.name}
        await interaction.client.db["infractiontypeactions"].update_one(
            filter,
            {"$set": {"grouprole": self.values[0]}},
            upsert=True,
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** succesfully updated infraction type.",
            view=None,
        )


async def InfractionEmbed(
    interaction: discord.Interaction, Config: dict, embed: discord.Embed
):
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not Config:
        Config = {"Infraction": {}, "_id": interaction.guild.id}

    Channel = (
        interaction.guild.get_channel(Config.get("Infraction", {}).get("channel"))
        or "Not Configured"
    )
    if isinstance(Channel, discord.TextChannel):
        Channel = Channel.mention

    Audit = (
        interaction.guild.get_channel(Config.get("Infraction", {}).get("LogChannel"))
        or "Not Configured"
    )
    if isinstance(Channel, discord.TextChannel):
        Audit = Audit.mention

    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's infraction settings! Infractions are a way to punish staff members. You can find out more at [the documentation](https://docs.astrobirb.dev/)."
    Types = Config.get("Infraction", {}).get(
        "types",
        [
            "Activity Notice",
            "Verbal Warning",
            "Warning",
            "Strike",
            "Demotion",
            "Termination",
        ],
    )
    Reasons = Config.get("Infraction", {}).get("reasons", [])
    value = f"{replytop} `Infraction Channel:` {Channel}\n{replymiddle} `Audit Log Channel`:  {Audit}\n{replymiddle} `Types:` {', '.join(Types)}\n{replybottom} `Reasons:` {', '.join(Reasons) if Reasons else 'Not Configured'}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)"[
        :1024
    ]

    embed.add_field(
        name="<:settings:1207368347931516928> Infractions",
        value=value[:1021] + "..." if len(value) > 1024 else value,
        inline=False,
    )
    return embed
