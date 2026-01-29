import discord
from utils.emojis import *
from utils.permissions import premium
import logging

from utils.format import Replace, Replace, IsSeperateBot
from utils.HelpEmbeds import NoPremium, NotYourPanel
import discord

logger = logging.getLogger(__name__)


async def HandleButton(data: dict):
    if not data.get("components"):
        return None

    class Button(discord.ui.Button):
        def __init__(
            self,
            label,
            style,
            custom_id=None,
            url=None,
            emoji=None,
            disabled=False,
            cmd=False,
        ):
            super().__init__(
                label=label,
                style=style,
                custom_id=custom_id,
                url=url,
                emoji=emoji,
                disabled=disabled,
            )
            self.cmd = cmd

        async def callback(self, interaction: discord.Interaction):
            from Cogs.Modules.commands import run

            await run(interaction, self.cmd)

    view = discord.ui.View(timeout=None)

    for component in data.get("components", []):
        if component.get("type") == "voting":
            from Cogs.Modules.commands import Voting

            return Voting()

        if component.get("type") == "link":
            button = Button(
                label=component.get("label"),
                style=discord.ButtonStyle.link,
                url=component.get("link"),
            )
        elif component.get("type") == "button":
            emoji = component.get("emoji")

            if emoji:
                try:
                    emoji = discord.PartialEmoji(name=emoji)
                except discord.DiscordException:
                    emoji = None
            if emoji:
                emoji = component.get("emoji")
            button = Button(
                label=component.get("label"),
                style=discord.ButtonStyle.blurple,
                custom_id=component.get("custom_id", component.get("label").lower()),
                emoji=emoji if emoji else None,
                disabled=component.get("disabled", False),
                cmd=component.get("command"),
            )

        else:
            continue

        view.add_item(button)

    return view


async def DisplayEmbed(data: dict, user: discord.User = None, replacements: dict = {}):
    if not data:
        return None
    embed = discord.Embed(color=discord.Color.dark_embed())

    async def ReplaceData(data, replacements):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = Replace(value, replacements)
                elif isinstance(value, dict):
                    data[key] = await ReplaceData(value, replacements)
                elif isinstance(value, list):
                    data[key] = [
                        (
                            await ReplaceData(item, replacements)
                            if isinstance(item, dict)
                            else (
                                Replace(item, replacements)
                                if isinstance(item, str)
                                else item
                            )
                        )
                        for item in value
                    ]
                elif isinstance(data, list):
                    data = [
                        (
                            await ReplaceData(item, replacements)
                            if isinstance(item, dict)
                            else (
                                Replace(item, replacements)
                                if isinstance(item, str)
                                else item
                            )
                        )
                        for item in data
                    ]
        return data

    data = await ReplaceData(data, replacements)
    emdata = data.get("embed", {})
    if emdata.get("title"):
        embed.title = emdata.get("title")

    if emdata.get("description"):
        embed.description = emdata.get("description")

    if emdata.get("thumbnail"):
        if emdata.get("thumbnail") == "{staff.avatar}":
            embed.set_thumbnail(url=user.display_avatar)
        else:
            embed.set_thumbnail(url=emdata.get("thumbnail"))

    if emdata.get("image"):
        if emdata.get("image") == "{image}":
            pass
        else:
            embed.set_image(url=emdata.get("image"))
    author = emdata.get("author")
    if author and (name := author.get("name")):
        icon_url = author.get("icon_url")

        if icon_url == "{author.avatar}":
            icon_url = replacements.get("author.avatar")

        if isinstance(icon_url, (tuple, list)):
            icon_url = icon_url[0]

        if icon_url:
            embed.set_author(name=name, icon_url=str(icon_url))
        else:
            embed.set_author(name=name)

    for field in emdata.get("fields", [])[:25]:
        name = field.get("name")
        value = field.get("value")
        inline = field.get("inline", False)
        if name and value:
            embed.add_field(name=name, value=value, inline=inline)

    color = emdata.get("color", "2b2d31")

    try:
        if (
            isinstance(color, str)
            and len(color) == 6
            and all(c in "0123456789abcdefABCDEF" for c in color)
        ):
            embed.color = discord.Color(int(color, 16))
        else:
            embed.color = discord.Color.dark_embed()

    except (ValueError, TypeError) as e:
        embed.color = discord.Color.dark_embed()

    if not any(
        [
            embed.title,
            embed.description,
            embed.author.name if embed.author else None,
            embed.fields,
        ]
    ):
        embed.description = "You need at least one of the following: Title, Description, Author, or Fields."

    return embed


class NoEmbed(discord.ui.View):
    def __init__(
        self, author: discord.User, finalfunc: callable, type: str, data: dict = {}
    ):
        super().__init__(timeout=2048)
        self.finalfunc = finalfunc
        self.author = author
        self.typed = type
        self.data = data
        self.add_item(
            discord.ui.Button(
                label="Documentation",
                style=discord.ButtonStyle.link,
                url="https://docs.astrobirb.dev",
                row=3,
            )
        )

    @discord.ui.button(
        label="Add Embed",
        style=discord.ButtonStyle.green,
        emoji="<:Add:1163095623600447558>",
    )
    async def AddEmbed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:

            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        view = Embed(interaction.user, self.finalfunc, self.typed, self.data)
        if self.typed in ("Promotions", "Infractions"):
            view.remove_item(view.Buttons)
            view.remove_item(view.ForumsChannel)
            view.remove_item(view.Permissions)
            view.remove_item(view.Ping)
            view.remove_item(view.RemoveEmbed)
        elif self.typed == "Forum":

            view.remove_item(view.reset)
            view.remove_item(view.Permissions)
            view.remove_item(view.RemoveEmbed)

        elif self.typed == "Custom Commands":
            view.remove_item(view.Ping)
            view.remove_item(view.ForumsChannel)
            view.remove_item(view.reset)
        else:
            view.remove_item(view.Buttons)
            view.remove_item(view.ForumsChannel)
            view.remove_item(view.Permissions)
            view.remove_item(view.Ping)

        await interaction.edit_original_response(
            embed=discord.Embed(description="Untitled"), view=view
        )

    @discord.ui.button(
        label="Button",
        style=discord.ButtonStyle.blurple,
        emoji="<:Button:1223063359184830494>" if not IsSeperateBot() else None,
    )
    async def Buttons(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        if self.typed == "Custom Commands":
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(
                name="Components",
                icon_url="https://cdn.discordapp.com/emojis/1223063359184830494.webp?size=96",
            )
            comp = self.data.get("components")
            if comp and len(comp) > 0:
                for components in self.data.get("components", []):
                    Linkdata = ""
                    ButtonData = ""
                    if components.get("type") == "link":
                        Linkdata += f"\n> **Link:** {components.get('link')}\n> **Label:** {components.get('label')}"
                    if components.get("type") == "button":
                        ButtonData += f"\n> **Label:** {components.get('label')}\n> **Emoji**: {components.get('emoji')}\n> **Command:** {components.get('command')}"

                    embed.add_field(
                        name=f"{components.get('ix', 0)} | {components.get('label', '???')}",
                        value=f"> **Type:** {components.get('type')}{ButtonData}{Linkdata}",
                        inline=False,
                    )
            else:
                embed.description = "There are no buttons yet. You can create one below by pressing the **plus button.**"

            view = componentmanager(interaction.user, self.data)
            await interaction.followup.send(view=view, embed=embed, ephemeral=True)
        else:
            view = Buttons(
                self.data,
                [
                    discord.SelectOption(label="Close", value="Close"),
                    discord.SelectOption(label="Lock", value="Lock"),
                ],
            )
            await interaction.followup.send(view=view, ephemeral=True)

    @discord.ui.button(
        label="Content",
        style=discord.ButtonStyle.gray,
        emoji="<:MEssage:1297957000440844382>" if not IsSeperateBot() else None,
    )
    async def Content(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.send_modal(Context(interaction.message.content))

    @discord.ui.button(
        label="Permissions",
        style=discord.ButtonStyle.grey,
        emoji="<:Permissions:1207365901956026368>" if not IsSeperateBot() else None,
    )
    async def Permissions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        view = discord.ui.View()
        view.add_item(PermissionRoles(interaction.user, self.data))
        await interaction.followup.send(view=view, ephemeral=True)

    @discord.ui.button(
        label="Reset",
        style=discord.ButtonStyle.red,
        emoji="<:Reset:1297957894624510093>" if not IsSeperateBot() else None,
    )
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:

            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        try:
            await interaction.client.config.delete_one(
                {"guild_id": interaction.guild.id, "type": self.typed}
            )
            if self.typed == "Promotions":
                from Cogs.Configuration.Components.Promotions import (
                    PSelect,
                    PromotionEmbed,
                )
                from Cogs.Configuration.Configuration import (
                    Options,
                    ConfigMenu,
                )

                Config = await interaction.client.config.find_one(
                    {"_id": interaction.guild.id}
                )

                view = discord.ui.View()
                view.add_item(
                    PSelect(
                        interaction.user,
                        Config.get("Promo", {}).get("System", {}).get("type", "og"),
                    )
                )
                view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
                await interaction.edit_original_response(
                    embed=await PromotionEmbed(
                        interaction,
                        Config,
                        discord.Embed(color=discord.Color.dark_embed()),
                    ),
                    view=view,
                )
            elif self.typed == "Infractions":
                from Cogs.Configuration.Components.Infractions import (
                    InfractionOption,
                    InfractionEmbed,
                )
                from Cogs.Configuration.Configuration import (
                    Options,
                    ConfigMenu,
                )

                Config = await interaction.client.config.find_one(
                    {"_id": interaction.guild.id}
                )

                view = discord.ui.View()
                view.add_item(InfractionOption(interaction.user))
                view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
                await interaction.edit_original_response(
                    embed=await InfractionEmbed(
                        interaction,
                        Config,
                        discord.Embed(color=discord.Color.dark_embed()),
                    ),
                    view=view,
                )
        except Exception as e:
            logger.error(str(e))

    @discord.ui.button(
        label="Finish",
        style=discord.ButtonStyle.green,
        emoji="<:Save:1223293419678470245>" if not IsSeperateBot() else None,
    )
    async def Finished(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):

        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        await self.finalfunc(interaction, self.data)
        self.stop()


class Embed(discord.ui.View):
    def __init__(
        self,
        author: discord.User,
        finalfunc: callable,
        type: str,
        data: dict = {},
    ):
        super().__init__(timeout=2048)
        self.author = author
        self.typed = type
        self.finalfunc = finalfunc
        self.data = data

        self.add_item(
            discord.ui.Button(
                label="Documentation",
                style=discord.ButtonStyle.link,
                url="https://docs.astrobirb.dev",
                row=2,
            )
        )

    @discord.ui.button(
        label="Remove Embed",
        style=discord.ButtonStyle.red,
        emoji="<:Subtract:1229040262161109003>" if not IsSeperateBot() else None,
        row=0,
    )
    async def RemoveEmbed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        view = NoEmbed(self.author, self.finalfunc, self.typed, self.data)
        if self.typed == "Promotions" or self.typed == "Infractions":
            view.remove_item(view.Buttons)
            view.remove_item(view.Permissions)
        elif self.typed == "Forum":

            view.remove_item(view.reset)
            view.remove_item(view.Permissions)
        elif self.typed == "Custom Commands":
            view.remove_item(view.reset)
        else:
            view.remove_item(view.reset)
            view.remove_item(view.Permissions)
            view.remove_item(view.Buttons)
            view.remove_item(view.Permissions)

        if "embed" in self.data:
            del self.data["embed"]
        await interaction.edit_original_response(embed=None, view=view)

    @discord.ui.button(
        label="Content",
        style=discord.ButtonStyle.gray,
        emoji="<:MEssage:1297957000440844382>" if not IsSeperateBot() else None,
        row=0,
    )
    async def Content(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.send_modal(Context(interaction.message.content))

    @discord.ui.button(
        label="Button",
        style=discord.ButtonStyle.blurple,
        emoji="<:Button:1223063359184830494>" if not IsSeperateBot() else None,
    )
    async def Buttons(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        if self.typed == "Custom Commands":
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(
                name="Components",
                icon_url="https://cdn.discordapp.com/emojis/1223063359184830494.webp?size=96",
            )
            comp = self.data.get("components")
            if comp and len(comp) > 0:
                for components in self.data.get("components", []):
                    Linkdata = ""
                    ButtonData = ""
                    if components.get("type") == "link":
                        Linkdata += f"\n> **Link:** {components.get('link')}\n> **Label:** {components.get('label')}"
                    if components.get("type") == "button":
                        ButtonData += f"\n> **Label:** {components.get('label')}\n> **Emoji**: {components.get('emoji')}\n> **Command:** {components.get('command')}"

                    embed.add_field(
                        name=f"{components.get('ix', 0)} | {components.get('label', '???')}",
                        value=f"> **Type:** {components.get('type')}{ButtonData}{Linkdata}",
                        inline=False,
                    )
            else:
                embed.description = "There are no buttons yet. You can create one below by pressing the **plus button.**"

            view = componentmanager(interaction.user, self.data)
            await interaction.followup.send(view=view, embed=embed, ephemeral=True)

        else:
            if not await premium(interaction.guild.id):
                return await interaction.followup.send(
                    embed=NoPremium(), ephemeral=True
                )
            view = discord.ui.View()
            view.add_item(
                Buttons(
                    self.data,
                    [
                        discord.SelectOption(label="Close", value="Close"),
                        discord.SelectOption(label="Lock", value="Lock"),
                    ],
                    self.typed,
                )
            )
            await interaction.followup.send(view=view, ephemeral=True)

    @discord.ui.button(
        label="Title",
        style=discord.ButtonStyle.blurple,
        emoji="<:Application:1224722901328986183>" if not IsSeperateBot() else None,
        row=0,
    )
    async def Title(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.send_modal(
            Title(
                interaction.message.embeds[0].title
                if interaction.message.embeds[0].title
                else None
            )
        )

    @discord.ui.button(
        label="Description",
        style=discord.ButtonStyle.blurple,
        emoji="<:description:1223062677572812920>" if not IsSeperateBot() else None,
        row=0,
    )
    async def Desc(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.send_modal(
            Description(
                interaction.message.embeds[0].description
                if interaction.message.embeds[0].description
                else None
            )
        )

    @discord.ui.button(
        label="Thumbnail",
        style=discord.ButtonStyle.blurple,
        emoji="<:image:1223062544135094363>" if not IsSeperateBot() else None,
        row=1,
    )
    async def Thu(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.send_modal(
            Thumbnail(
                (
                    interaction.message.embeds[0].thumbnail.url
                    if interaction.message.embeds[0].thumbnail
                    else None
                ),
                self.data,
            )
        )

    @discord.ui.button(
        label="Image",
        style=discord.ButtonStyle.blurple,
        emoji="<:Image:1223063095417765938>" if not IsSeperateBot() else None,
        row=1,
    )
    async def Im(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.send_modal(
            Image(
                (
                    interaction.message.embeds[0].image.url
                    if interaction.message.embeds[0].image
                    else None
                ),
                self.data,
            )
        )

    @discord.ui.button(
        label="Author",
        style=discord.ButtonStyle.blurple,
        emoji="<:Author:1297956338738925722>" if not IsSeperateBot() else None,
        row=1,
    )
    async def Au(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.send_modal(
            Author(
                (
                    interaction.message.embeds[0].author.name
                    if interaction.message.embeds[0].author
                    else None
                ),
                (
                    interaction.message.embeds[0].author.icon_url
                    if interaction.message.embeds[0].author
                    else None
                ),
                self.data,
            )
        )

    @discord.ui.button(
        label="Color",
        style=discord.ButtonStyle.blurple,
        emoji="<:tag:1234998802948034721>" if not IsSeperateBot() else None,
        row=1,
    )
    async def Colo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.send_modal(
            Colour(
                interaction.message.embeds[0].color.value
                if interaction.message.embeds[0].color
                else None
            )
        )

    @discord.ui.button(label="Fields", style=discord.ButtonStyle.blurple, row=1)
    async def Fields(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        view = EmbedFieldManager(interaction.user, self.data, interaction.message)
        await interaction.followup.send(view=view, ephemeral=True)

    @discord.ui.button(
        label="Ping",
        style=discord.ButtonStyle.blurple,
        emoji="<:Ping:1298301862906298378>" if not IsSeperateBot() else None,
        row=2,
    )
    async def Ping(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        view = discord.ui.View()
        view.add_item(Ping(interaction.user, self.data))
        await interaction.followup.send(view=view, ephemeral=True)

    @discord.ui.button(
        label="Forums Channel",
        style=discord.ButtonStyle.blurple,
        emoji="<:tag:1234998802948034721>" if not IsSeperateBot() else None,
        row=2,
    )
    async def ForumsChannel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        view = discord.ui.View()
        view.add_item(ForumsChannel(interaction.user, self.data))
        await interaction.followup.send(view=view, ephemeral=True)

    @discord.ui.button(
        label="Permissions",
        style=discord.ButtonStyle.grey,
        row=2,
        emoji="<:Permissions:1207365901956026368>" if not IsSeperateBot() else None,
    )
    async def Permissions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        view = discord.ui.View()
        view.add_item(PermissionRoles(interaction.user, self.data))
        await interaction.followup.send(view=view, ephemeral=True)

    @discord.ui.button(
        label="Reset",
        style=discord.ButtonStyle.red,
        emoji="<:Reset:1297957894624510093>" if not IsSeperateBot() else None,
        row=2,
    )
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        try:
            await interaction.client.db["Customisation"].delete_one(
                {"guild_id": interaction.guild.id, "type": self.typed}
            )
            if self.typed == "Promotions":
                from Cogs.Configuration.Components.Promotions import (
                    PSelect,
                    PromotionEmbed,
                )
                from Cogs.Configuration.Configuration import (
                    Options,
                    ConfigMenu,
                )

                Config = await interaction.client.config.find_one(
                    {"_id": interaction.guild.id}
                )

                view = discord.ui.View()
                view.add_item(PSelect(interaction.user))
                view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
                await interaction.edit_original_response(
                    embed=await PromotionEmbed(
                        interaction,
                        Config,
                        discord.Embed(color=discord.Color.dark_embed()),
                    ),
                    view=view,
                )
            elif self.typed == "Infractions":
                from Cogs.Configuration.Components.Infractions import (
                    InfractionOption,
                    InfractionEmbed,
                )
                from Cogs.Configuration.Configuration import (
                    Options,
                    ConfigMenu,
                )

                Config = await interaction.client.config.find_one(
                    {"_id": interaction.guild.id}
                )

                view = discord.ui.View()
                view.add_item(InfractionOption(interaction.user))
                view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
                await interaction.edit_original_response(
                    embed=await InfractionEmbed(
                        interaction,
                        Config,
                        discord.Embed(color=discord.Color.dark_embed()),
                    ),
                    view=view,
                )
            elif self.typed == "Suspension":
                from Cogs.Configuration.Components.Suspensions import (
                    SuspensionOptions,
                    SuspensionEmbed,
                )
                from Cogs.Configuration.Configuration import (
                    Options,
                    ConfigMenu,
                )

                Config = await interaction.client.config.find_one(
                    {"_id": interaction.guild.id}
                )

                view = discord.ui.View()
                view.add_item(SuspensionOptions(interaction.user))
                view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
                await interaction.edit_original_response(
                    embed=await SuspensionEmbed(
                        interaction,
                        Config,
                        discord.Embed(color=discord.Color.dark_embed()),
                    ),
                    view=view,
                )
            elif self.typed == "Feedback":
                from Cogs.Configuration.Components.StaffFeedback import (
                    StaffFeedback,
                    StaffFeedbackEmbed,
                )
                from Cogs.Configuration.Configuration import (
                    Options,
                    ConfigMenu,
                )

                Config = await interaction.client.config.find_one(
                    {"_id": interaction.guild.id}
                )

                view = discord.ui.View()
                view.add_item(StaffFeedback(interaction.user))
                view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
                await interaction.edit_original_response(
                    embed=await StaffFeedbackEmbed(
                        interaction,
                        Config,
                        discord.Embed(color=discord.Color.dark_embed()),
                    ),
                    view=view,
                )
            elif self.typed in [
                "Denied Suggestion",
                "Suggestion",
                "Accepted Suggestion",
            ]:
                from Cogs.Configuration.Components.Suggestions import (
                    Suggestions,
                    SuggestionsEmbed,
                )
                from Cogs.Configuration.Configuration import (
                    Options,
                    ConfigMenu,
                )

                Config = await interaction.client.config.find_one(
                    {"_id": interaction.guild.id}
                )

                view = discord.ui.View()
                view.add_item(Suggestions(interaction.user))
                view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
                await interaction.edit_original_response(
                    embed=await SuggestionsEmbed(
                        interaction,
                        Config,
                        discord.Embed(color=discord.Color.dark_embed()),
                    ),
                    view=view,
                )

        except Exception as e:
            logger.error(str(e))

    @discord.ui.button(
        label="Finish",
        style=discord.ButtonStyle.green,
        emoji="<:Save:1223293419678470245>" if not IsSeperateBot() else None,
        row=3,
    )
    async def Finished(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.finalfunc(interaction, self.data)
        self.stop()


class Ping(discord.ui.RoleSelect):
    def __init__(self, author: discord.Member, data: dict):
        super().__init__(
            placeholder="Select Roles",
            min_values=0,
            max_values=25,
        )
        self.author = author
        self.data = data

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        if self.values:
            self.data["ping"] = [role.id for role in self.values]
        else:
            self.data.pop("ping")
        await interaction.edit_original_response(
            content=f"{tick} **{interaction.user.display_name},** the ping has been updated.",
            view=None,
            embed=None,
        )


class ForumsChannel(discord.ui.ChannelSelect):
    def __init__(self, author: discord.Member, data: dict):
        super().__init__(
            placeholder="Select Forums Channel",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.forum],
        )
        self.author = author
        self.data = data

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:

            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)

        self.data["channel_id"] = self.values[0].id if self.values else None
        await interaction.edit_original_response(
            content=f"{tick} **{interaction.user.display_name},** the channel has been updated.",
            view=None,
            embed=None,
        )


class PermissionRoles(discord.ui.RoleSelect):
    def __init__(self, author: discord.Member, data: dict):
        super().__init__(
            placeholder="Select Roles",
            min_values=0,
            max_values=25,
        )
        self.author = author
        self.data = data

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        if self.values:
            self.data["permissionroles"] = [role.id for role in self.values]
        else:
            self.data.pop("permissionroles")

        await interaction.edit_original_response(
            content=f"{tick} **{interaction.user.display_name},** the command has been updated.",
            view=None,
            embed=None,
        )


class Title(discord.ui.Modal, title="Title"):
    def __init__(self, titled):
        super().__init__()
        self.titled = titled

        self.Titles = discord.ui.TextInput(
            label="Title",
            placeholder="What is the title?",
            required=False,
            max_length=256,
            default=self.titled if self.titled else None,
        )
        self.add_item(self.Titles)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = interaction.message.embeds[0]
        embed.title = self.Titles.value
        try:
            await interaction.edit_original_response(embed=embed)
        except discord.HTTPException():
            return await interaction.followup.send(
                f"{no} {interaction.user.display_name}, had an error adding the title please try again.",
                ephemeral=True,
            )


class Buttons(discord.ui.Select):
    def __init__(self, data: dict, options: list, typed: str):
        super().__init__(
            options=options, max_values=1 if typed != "Forum" else len(options)
        )
        self.data = data
        self.typed = typed

    async def callback(self, interaction: discord.Interaction):
        if self.typed == "Custom Commands":
            if self.values[0] == "Voting Buttons":
                await interaction.response.defer()
                self.data["components"].append(
                    {
                        "type": "voting",
                        "label": "Voting Buttons",
                        "ix": (
                            0
                            if len(self.data.get("components")) == 0
                            else len(self.data.get("components")) + 1
                        ),
                    }
                )
                await interaction.edit_original_response(
                    content=f"{tick} **@{interaction.user.name}** I've successfully added voting buttons. (This doesn't support other button types)",
                    view=None,
                    embed=None,
                )
                return
            elif self.values[0] == "Link Button":
                await interaction.response.send_modal(LinkButton(self.data))
            elif self.values[0] == "Custom Button":
                await interaction.response.send_modal(CustomButton(self.data))
            return

        elif self.typed == "Forum":
            await interaction.response.defer()
            options = self.values
            if "Close" in options:
                self.data["Close"] = True
            if "Lock" in options:
                self.data["Lock"] = True
            else:
                self.data["Close"] = False
                self.data["Lock"] = False
        await interaction.edit_original_response(
            content=f"{tick} **{interaction.user.display_name},** I've updated the buttons.",
            embed=None,
            view=None,
        )


class CustomButton(discord.ui.Modal, title="Custom Button"):
    def __init__(self, data: dict):
        super().__init__()
        self.data = data

        self.cmd = discord.ui.TextInput(
            label="Command",
            placeholder="What is the name of the custom command it'll send when pressed?",
            required=True,
            max_length=256,
        )
        self.label = discord.ui.TextInput(
            label="Label",
            placeholder="What is the label?",
            required=True,
            max_length=256,
        )
        self.emoji = discord.ui.TextInput(
            label="Emoji",
            placeholder="What emoji should be on the button? (Example: <:Alert:1208972002803712000>)",
            required=False,
            max_length=256,
        )
        self.color = discord.ui.TextInput(
            placeholder="What is the color? (Blue, Red, Grey, Green)",
            label="Color",
            required=False,
            max_length=256,
        )
        self.add_item(self.cmd)
        self.add_item(self.label)
        self.add_item(self.emoji)
        self.add_item(self.color)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not self.data["components"]:
            self.data["components"] = []
        color = self.color.value
        if self.color.value == "":
            color = "Grey"
        if self.color.value not in ["Red", "Blue", "Grey", "Green"]:
            return await interaction.response.edit_message(
                content=f"{tick} **{interaction.user.display_name},** you can only select from the following colors: Red, Blue, Grey, Green",
                embed=None,
                view=None,
            )

        self.data["components"].append(
            {
                "type": "button",
                "ix": (
                    0
                    if len(self.data.get("components")) == 0
                    else len(self.data.get("components")) + 1
                ),
                "label": self.label.value,
                "emoji": self.emoji.value,
                "color": color,
                "command": self.cmd.value,
            }
        )

        await interaction.edit_original_response(
            content=f"{tick} **{interaction.user.display_name},** I've updated the buttons.",
            embed=None,
            view=None,
        )


class LinkButton(discord.ui.Modal, title="Link Button"):
    def __init__(self, data: dict):
        super().__init__()
        self.data = data
        self.name = discord.ui.TextInput(
            label="Name",
            placeholder="What is the name of the link button?",
            required=True,
        )

        self.link = discord.ui.TextInput(
            label="Link",
            placeholder="What is the link?",
            required=True,
            max_length=2048,
        )
        self.label = discord.ui.TextInput(
            label="Label",
            placeholder="What is the label?",
            required=True,
            max_length=256,
        )
        self.emoji = discord.ui.TextInput(
            label="Emoji",
            placeholder="What emoji should be on the button? (Example: <:Alert:1208972002803712000>)",
            required=False,
            max_length=256,
        )
        self.add_item(self.link)
        self.add_item(self.label)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not self.data.get("components"):
            self.data["components"] = []

        self.data["components"].append(
            {
                "ix": (
                    0
                    if len(self.data.get("components")) == 0
                    else len(self.data.get("components")) + 1
                ),
                "type": "link",
                "name": self.name.value,
                "link": self.link.value,
                "label": self.label.value,
                "emoji": self.emoji.value,
            }
        )

        await interaction.edit_original_response(
            content=f"{tick} **{interaction.user.display_name},** I've updated the buttons.",
            embed=None,
            view=None,
        )


class Description(discord.ui.Modal, title="Description"):
    def __init__(self, description):
        super().__init__()
        self.descriptions = description

        self.description = discord.ui.TextInput(
            label="Description",
            placeholder="What is the description?",
            style=discord.TextStyle.long,
            max_length=4000,
            required=False,
            default=self.descriptions,
        )

        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = interaction.message.embeds[0]
        embed.description = self.description.value

        await interaction.edit_original_response(embed=embed)


class Colour(discord.ui.Modal, title="Colour"):
    def __init__(self, colour):
        super().__init__()
        self.colour = colour

        self.color = discord.ui.TextInput(
            label="Colour",
            placeholder="Do not include the hashtag",
            max_length=30,
            default=self.colour,
        )
        self.add_item(self.color)

    async def on_submit(self, interaction: discord.Interaction):
        color_value = self.color.value
        if len(color_value) != 6:
            await interaction.response.send_message(
                f" {no} Please provide a valid hex color. (A hex is 6 characters long without the hashtag.)",
                ephemeral=True,
            )
            return

        try:
            color = discord.Color(int(color_value, 16))
        except ValueError:
            await interaction.response.send_message(
                f" {no} Please provide a valid hex color without the hashtag.",
                ephemeral=True,
            )
            return

        embed = interaction.message.embeds[0]
        embed.color = color
        await interaction.response.edit_message(embed=embed)


class Context(discord.ui.Modal, title="Content"):
    def __init__(self, content):
        super().__init__()
        self.content = content

        self.color = discord.ui.TextInput(
            label="Content",
            placeholder="What do you want the content to be?",
            required=False,
            style=discord.TextStyle.long,
            max_length=2000,
            default=self.content,
        )
        self.add_item(self.color)

    async def on_submit(self, interaction: discord.Interaction):
        color_value = self.color.value
        await interaction.response.edit_message(content=color_value)


class Thumbnail(discord.ui.Modal, title="Thumbnail"):
    def __init__(self, thumb, data):
        super().__init__()
        self.thumb = thumb
        self.data = data

        self.Thumbnaile = discord.ui.TextInput(
            label="Thumbnail",
            placeholder="What's the thumbnail URL?",
            required=False,
            max_length=2048,
            default=self.thumb,
        )
        self.add_item(self.Thumbnaile)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = interaction.message.embeds[0]
        org = self.Thumbnaile.value.strip() if self.Thumbnaile.value else None
        url = org

        if url in ["{author.avatar}", "{staff.avatar}"]:
            url = str(interaction.user.display_avatar.url)

        try:
            embed.set_thumbnail(url=url)
            await interaction.edit_original_response(embed=embed)
            self.data["thumb"] = org

        except discord.HTTPException:
            return await interaction.followup.send(
                content=f"{crisis} **{interaction.user.display_name}**, this isn't a proper link."
            )


class Image(discord.ui.Modal, title="Image"):
    def __init__(self, ima, data: dict):
        super().__init__()
        self.ima = ima
        self.data = data

        self.Thumbnaile = discord.ui.TextInput(
            label="Image",
            placeholder="What's the image URL?",
            required=False,
            max_length=2048,
            default=self.ima,
        )
        self.add_item(self.Thumbnaile)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = interaction.message.embeds[0]
        org = self.Thumbnaile.value.strip() if self.Thumbnaile.value else None
        url = org

        if org in ["{author.avatar}", "{staff.avatar}", "{image}"]:
            url = str(interaction.user.display_avatar.url)

        try:
            embed.set_image(url=url)
            await interaction.edit_original_response(embed=embed)
            self.data["image"] = org
        except discord.HTTPException:
            return await interaction.followup.send(
                content=f"{crisis} **{interaction.user.display_name}**, this isn't a proper link."
            )


class Author(discord.ui.Modal, title="Author"):
    def __init__(self, authotext, iconurl, data):
        super().__init__()
        self.authotext = authotext
        self.iconurl = iconurl
        self.data = data

        self.authortext = discord.ui.TextInput(
            label="Author Name",
            placeholder="What's the author name?",
            required=False,
            max_length=256,
            default=self.authotext,
        )

        self.iconUrl = discord.ui.TextInput(
            label="Icon URL",
            placeholder="What's the icon URL?",
            required=False,
            max_length=2048,
            default=self.iconurl,
        )

        self.add_item(self.authortext)
        self.add_item(self.iconUrl)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = interaction.message.embeds[0]
        Author = self.authortext.value or ""
        Org = self.iconUrl.value
        Url = Org

        if self.iconUrl.value in ["{author.avatar}", "{staff.avatar}"]:
            Url = str(interaction.user.display_avatar.url)

        if not Url and embed.author and getattr(embed.author, "icon_url", None):
            Url = embed.author.icon_url

        try:
            embed.set_author(name=Author, icon_url=Url)
            await interaction.edit_original_response(embed=embed)
            self.data["author_url"] = Org
        except discord.HTTPException:
            return await interaction.followup.send(
                content=f"{crisis} **{interaction.user.display_name}**, this isn't a proper link."
            )


class componentmanager(discord.ui.View):
    def __init__(self, author: discord.User, data: dict):
        super().__init__()
        self.author = author
        self.data = data

    @discord.ui.button(
        label="", style=discord.ButtonStyle.gray, emoji="<:Add:1163095623600447558>"
    )
    async def AddButton(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not self.data.get("components"):
            self.data["components"] = []
        options = [
            discord.SelectOption(label="Voting Buttons", value="Voting Buttons"),
            discord.SelectOption(label="Link Button", value="Link Button"),
            discord.SelectOption(label="Custom Button", value="Custom Button"),
        ]
        view = discord.ui.View()
        view.add_item(Buttons(self.data, options, "Custom Commands"))
        await interaction.response.edit_message(view=view, embed=None)

    @discord.ui.button(
        label="",
        style=discord.ButtonStyle.gray,
        emoji="<:Subtract:1229040262161109003>",
    )
    async def RemoveButton(
        self,
        interaction: discord.Interaction,
        button: discord.Interaction,
    ):
        await interaction.response.defer()
        if not self.data.get("components") or len(self.data.get("components")) == 0:
            return await interaction.followup.send(
                content=f"{no} **{interaction.user.display_name},** there are no buttons to remove.",
                ephemeral=True,
            )
        options = [
            discord.SelectOption(
                label=component.get("label"), value=component.get("ix")
            )
            for component in self.data.get("components")
            if "label" in component
        ][:25]
        view = discord.ui.View()
        view.add_item(EraseButtons(interaction.user, self.data, options))
        await interaction.edit_original_response(
            view=view,
            embed=None,
            content="<:List:1223063187063308328> Select which components you want to remove.",
        )


class EraseButtons(discord.ui.Select):
    def __init__(self, author: discord.User, data: dict, options: list):
        super().__init__(options=options)
        self.data = data

    async def callback(self, interaction: discord.Interaction):
        Selected = self.values[0]
        self.data["components"] = [
            c for c in self.data["components"] if c.get("ix") != Selected
        ]
        await interaction.response.edit_message(
            content=f"{tick} successfully removed component.", view=None, embed=None
        )


class EmbedFieldEditor(discord.ui.Modal, title="Edit Embed Field"):
    def __init__(
        self,
        field_name=None,
        field_value=None,
        inline=False,
        msg: discord.Message = None,
    ):
        super().__init__()
        self.field_name = field_name
        self.field_value = field_value
        self.inline = inline
        self.msg = msg

        self.field_name_input = discord.ui.TextInput(
            label="Field Name",
            placeholder="Enter the field name",
            required=True,
            default=self.field_name,
        )
        self.field_value_input = discord.ui.TextInput(
            label="Field Value",
            placeholder="Enter the field value",
            style=discord.TextStyle.long,
            required=True,
            default=self.field_value,
        )
        self.inline_input = discord.ui.TextInput(
            label="Inline",
            placeholder="True or False",
            required=True,
            default=str(self.inline),
        )

        self.add_item(self.field_name_input)
        self.add_item(self.field_value_input)
        self.add_item(self.inline_input)

    async def on_submit(self, interaction: discord.Interaction):
        embed = self.msg.embeds[0]
        field_name = self.field_name_input.value
        field_value = self.field_value_input.value
        inline = self.inline_input.value.lower() == "true"
        for field in embed.fields:
            if field.name == field_name:
                field.value = field_value
                field.inline = inline
                break
        else:
            embed.add_field(name=field_name, value=field_value, inline=inline)
        try:
            msg = await interaction.channel.fetch_message(self.msg.id)
            await msg.edit(embed=embed)
        except discord.NotFound:
            await interaction.response.send_message(
                content=f"{crisis} **@{interaction.user.display_name},** to be able to edit fields you must be in a channel I can access so I can add the fields.",
                ephemeral=True,
            )
        await interaction.response.edit_message(content="")


class EmbedFieldManager(discord.ui.View):
    def __init__(self, author: discord.User, data: dict, msg: discord.Message):
        super().__init__()
        self.author = author
        self.data = data
        self.msg = msg

    @discord.ui.button(
        label="", style=discord.ButtonStyle.gray, emoji="<:Add:1163095623600447558>"
    )
    async def add_field(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(EmbedFieldEditor(msg=self.msg))

    @discord.ui.button(
        label="", style=discord.ButtonStyle.blurple, emoji="<:Pen:1235001839036923996>"
    )
    async def edit_field(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = self.msg.embeds[0]
        if not embed.fields or len(embed.fields) == 0:
            await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name},** there are no fields to edit.",
                ephemeral=True,
            )
            return
        options = [
            discord.SelectOption(label=field.name, value=str(index))
            for index, field in enumerate(embed.fields)
        ]
        view = discord.ui.View()
        view.add_item(FieldSelector(self.author, options, msg=self.msg))
        await interaction.response.send_message(view=view, ephemeral=True)

    @discord.ui.button(
        label="",
        style=discord.ButtonStyle.gray,
        emoji="<:Subtract:1229040262161109003>",
    )
    async def delete_field(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = self.msg.embeds[0]
        if not embed.fields or len(embed.fields) == 0:
            await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name},** there are no fields to edit.",
                ephemeral=True,
            )
            return
        options = [
            discord.SelectOption(label=field.name, value=str(index))
            for index, field in enumerate(embed.fields)
        ]
        view = discord.ui.View()
        view.add_item(FieldDeleter(self.author, options, msg=self.msg))
        await interaction.response.send_message(view=view, ephemeral=True)


class FieldSelector(discord.ui.Select):
    def __init__(self, author: discord.User, options: list, msg):
        super().__init__(placeholder="Select a field to edit", options=options)
        self.author = author
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        embed = self.msg.embeds[0]
        selected_index = int(self.values[0])
        field = embed.fields[selected_index]
        await interaction.response.send_modal(
            EmbedFieldEditor(field.name, field.value, field.inline, msg=self.msg)
        )


class FieldDeleter(discord.ui.Select):
    def __init__(self, author: discord.User, options: list, msg: discord.Message):
        super().__init__(placeholder="Select a field to delete", options=options)
        self.author = author
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        embed = self.msg.embeds[0]
        selected_index = int(self.values[0])
        embed.remove_field(selected_index)
        try:
            msg = await interaction.channel.fetch_message(self.msg.id)
            await msg.edit(embed=embed)
        except discord.NotFound:
            await interaction.response.send_message(
                content="Please use the embed builder in a channel I can actually see.",
                ephemeral=True,
            )
        await interaction.response.edit_message(content="")
