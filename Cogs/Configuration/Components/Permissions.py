import discord
import discord.http
from utils.emojis import *


class PermissionsUpdate(discord.ui.RoleSelect):
    def __init__(
        self, author: discord.Member, type: str, roles: list[discord.Role] = []
    ):
        super().__init__(
            default_values=roles,
            placeholder="Staff Role" if type == "staffrole" else "Admin Role",
            min_values=0,
            max_values=25,
        )
        self.author = author

        self.typed = type
        self.roles = roles

    async def callback(self, interaction):
        from Cogs.Configuration.Configuration import ConfigMenu, Options
        from Cogs.Configuration.Components.AdvancedPermissions import (
            PermissionsDropdown,
        )

        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Permissions": {}}
        elif "Permissions" not in config:
            config["Permissions"] = {}

        config["Permissions"][self.typed] = [role.id for role in self.values]
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )
        view = discord.ui.View()
        view.add_item(
            PermissionsUpdate(
                interaction.user,
                "staffrole",
                [
                    role
                    for role in interaction.guild.roles
                    if role.id in Updated.get("Permissions", {}).get("staffrole", [])
                ],
            )
        )
        view.add_item(
            PermissionsUpdate(
                interaction.user,
                "adminrole",
                [
                    role
                    for role in interaction.guild.roles
                    if role.id in Updated.get("Permissions", {}).get("adminrole", [])
                ],
            )
        )
        view.add_item(PermissionsDropdown(interaction.user))
        view.add_item(ConfigMenu(Options(Updated), interaction.user))
        await interaction.response.edit_message(
            view=view,
            embed=await PermissionsEmbed(
                interaction, Updated, discord.Embed(color=discord.Color.dark_embed())
            ),
        )


async def PermissionsEmbed(
    interaction: discord.Interaction, Config: dict, embed: discord.Embed
):
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not Config:
        Config = {"Permissions": {}}
    StaffRole = (
        ", ".join(
            f"<@&{int(Role)}>"
            for Role in Config.get("Permissions", {}).get("staffrole") or []
        )
        or "Not Configured"
    )

    AdminRole = (
        ", ".join(
            f"<@&{int(Role)}>"
            for Role in Config.get("Permissions", {}).get("adminrole") or []
        )
        or "Not Configured"
    )
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's permissions! If you wanna know more about what these permissions do head to the [advanced permissions page](https://docs.astrobirb.dev/advanced-permissions) on the [documentation](https:/docs.astrobirb.dev)\n"
    value = f"{replytop} `Staff Role:` {StaffRole} \n{replybottom} `Admin Role:` {AdminRole}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)"
    if len(value) > 1021:
        value = value[:1018] + "..."

    embed.add_field(
        name="<:Permissions:1207365901956026368> Permissions",
        value=value,
        inline=False,
    )
    return embed
