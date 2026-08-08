from typing import Literal

from cogs.Configuration.Components.Infractions import ConfigureGroupRoles
from core.bot.HelpEmbeds import NotYourPanel
from core.bot.emojis import *


class IntegrationsView(discord.ui.LayoutView):
    def __init__(
        self, author, features: Literal["infractions", "promotions"], extra: dict
    ):
        super().__init__()
        children = []
        if features.lower() != "infractions":
            children.append(
                discord.ui.Section(
                    discord.ui.TextDisplay(
                        f"### {Emojis.roblox} [Roblox](<https://roblox.com>) Communities"
                    ),
                    discord.ui.TextDisplay(
                        content="Using Roblox's communities api you can modify a users roblox rank."
                        "\n-# This uses the old communities roles, not the system where you can have multiple roles."
                    ),
                    accessory=ConfigureGroupRoles(author, extra.get("name")).Configure,
                )
            )
            children.append(discord.ui.Separator())

        children.extend(
            [
                discord.ui.Section(
                    discord.ui.TextDisplay(
                        "### [Melonly](<https://melonly.xyz>) - Workflows & Webhooks"
                    ),
                    discord.ui.TextDisplay(
                        "Using [Melonly workflows](<https://melonly.xyz/product/workflows>), you can trigger actions using their webhook trigger type."
                    ),
                ),
                discord.ui.Separator(),
                discord.ui.Section(
                    discord.ui.TextDisplay("### Custom Webhooks"),
                    discord.ui.TextDisplay("Send requests to a custom webhook"),
                ),
            ]
        )


class Integrations(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(label="Roblox Groups", emoji=f"{Emojis.roblox}")
            ]
        )
        self.author = author

    async def callback(self, interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        if self.values[0] == "Roblox Groups":
            from core.integrations.roblox import GetValidToken
            from core.bot.HelpEmbeds import NotRobloxLinked

            token = await GetValidToken(user=interaction.user)
            if not token:
                return await interaction.followup.send(
                    embed=NotRobloxLinked(), ephemeral=True
                )
            view = discord.ui.View()
            view.add_item(GroupOptions(interaction.user))

            await interaction.followup.send(view=view, ephemeral=True)


class GroupOptions(discord.ui.Select):
    def __init__(self, author: discord.User):
        options = [
            discord.SelectOption(
                label="Group", description="Link the roblox group to the server."
            )
        ]
        super().__init__(options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        modal = EnterGroup(self.author)
        await interaction.response.send_modal(modal)


class EnterGroup(discord.ui.Modal):
    def __init__(self, author: discord.User):
        super().__init__(title="Enter Roblox Group ID")
        self.author = author
        self.group_id = discord.ui.TextInput(
            label="Group ID", placeholder="Enter the Roblox Group ID here"
        )

        self.add_item(self.group_id)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(embed=NotYourPanel(), ephemeral=True)
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"_id": interaction.guild.id, "groups": {}}
        if not config.get("groups"):
            config["groups"] = {}

        from core.integrations.roblox import GetGroup2, GetUser
        from core.bot.HelpEmbeds import NotRobloxLinked

        group = await GetGroup2(self.group_id.value, interaction.user)
        if not group or not group.get("owner"):
            return await interaction.edit_original_response(
                content=f"{Emojis.crisis} **{interaction.user.display_name},** I couldn't find the roblox group from your account.",
                view=None,
                embed=None,
            )
        user = await GetUser(user=interaction.user)
        if not user:
            return await interaction.edit_original_response(
                embed=NotRobloxLinked(), view=None, content=None
            )
        RobloxID = (
            int(user.get("roblox", {}).get("id"))
            if user.get("roblox", {})
            else int(user.get("sub"))
        )

        OwnerID = int(group.get("owner").split("/")[1])
        if not OwnerID == RobloxID:
            return await interaction.edit_original_response(
                content=f"{Emojis.crisis} **{interaction.user.display_name},** you aren't the owner of this group. Please get the owner of it to link it.",
                view=None,
                embed=None,
            )

        config["groups"]["id"] = self.group_id.value
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}, upsert=True
        )
        await interaction.edit_original_response(
            content=f"{Emojis.tick} **{interaction.user.display_name}**, group successfullyy linked.",
            view=None,
        )


async def integrationsEmbed(interaction: discord.Interaction, embed: discord.Embed):
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = (
        "> Integrations are an easy way to connect external providers to the bot. "
        "You can find out more at [the documentation](https://docs.astrobirb.dev/)."
    )
    config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    Groups = config.get("groups", {}).get("id", None) if config else None
    embed.add_field(
        name=f"{Emojis.link} Integrations",
        value=f"> **Groups**: {'Linked' if Groups else 'Unlinked'}",
        inline=False,
    )
    return embed
