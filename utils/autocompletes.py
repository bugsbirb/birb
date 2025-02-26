import discord
from discord.ext import commands
from discord import app_commands
from utils.format import DefaultTypes
import typing


Current = {}


async def DepartmentAutocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice]:
    C = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not C:
        return [
            app_commands.Choice(
                name="[Bot hasn't been configured yet]", value="not_configured"
            )
        ]

    PromoSystemType = C.get("Promo", {}).get("System", {}).get("type", "")
    if PromoSystemType == "multi":
        Departments = (
            C.get("Promo", {}).get("System", {}).get("multi", {}).get("Departments", [])
        )
        choices = []
        for dept_list in Departments:
            for department in dept_list:
                if current.lower() in department.get("name").lower():
                    choices.append(
                        app_commands.Choice(
                            name=department.get("name"), value=department.get("name")
                        )
                    )
        return choices

    return []


async def CloseReason(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    PreviousTicketReasons = interaction.client.db["Tickets"].find(
        {"GuildID": interaction.guild.id, "Closed": {"$exists": True}}
    )
    Reasons = []
    async for Ticket in PreviousTicketReasons:
        if Ticket.get("closed", {}).get("reason"):
            if (
                current.lower() in Ticket.get("closed", {}).get("reason").lower()
                or not current
            ):
                Reasons.append(
                    app_commands.Choice(
                        name=Ticket.get("closed", {}).get("reason")[:100],
                        value=Ticket.get("closed", {}).get("reason")[:100],
                    )
                )
    return Reasons[:25]


async def Snippets(
    interaction: discord.Interaction, current: str
) -> typing.List[app_commands.Choice[str]]:
    filter = {"guild_id": interaction.guild_id}

    tag_names = await interaction.client.db["Modmail Snippets"].distinct("name", filter)

    filtered_names = [name for name in tag_names if current.lower() in name.lower()]
    filtered_names = filtered_names[:25]

    choices = [app_commands.Choice(name=name, value=name) for name in filtered_names]

    return choices


async def ConnectionRoles(
    interaction: discord.Interaction, current: str
) -> typing.List[app_commands.Choice[str]]:
    try:
        filter = {"guild": interaction.guild_id}

        tag_names = await interaction.client.db["connectionroles"].distinct(
            "name", filter
        )

        filtered_names = [name for name in tag_names if current.lower() in name.lower()]
        filtered_names = filtered_names[:25]

        choices = [
            app_commands.Choice(name=name, value=name) for name in filtered_names
        ]

        return choices
    except Exception as e:
        print(e)


async def infractiontypes(
    interaction: discord.Interaction, current: str
):
    try:
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            return [app_commands.Choice(name="Not Configured", value="Not Configured")]

        types = Config.get("Infraction", {}).get("types", [])
        if not types:
            types = DefaultTypes()

        choices = [
            app_commands.Choice(name=name[:100], value=name[:100])
            for name in types[:25]
        ]

        return choices
    except (ValueError, discord.HTTPException, discord.NotFound, TypeError):
        return [
            app_commands.Choice(
                name="[ERROR CONTACT SUPPORT]", value="[ERROR CONTACT SUPPORT]"
            )
        ]


async def infractionreasons(
    interaction: discord.Interaction, current: str
) -> typing.List[app_commands.Choice[str]]:
    try:
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if Config is None:
            return [app_commands.Choice(name="Not Configured", value="Not Configured")]

        Reasons = Config.get("Infraction", {}).get("reasons", [])
        if not Reasons:
            return []

        choices = [
            app_commands.Choice(name=name[:100], value=name[:100])
            for name in Reasons[:25]
        ]

        return choices

    except (ValueError, discord.HTTPException, discord.NotFound, TypeError):
        return [app_commands.Choice(name="Error", value="Error")]


async def RoleAutocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    C = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not C:
        return [
            app_commands.Choice(
                name="[Bot hasn't been configured yet]", value="not_configured"
            )
        ]

    PromoSystemType = C.get("Promo", {}).get("System", {}).get("type", "")

    if PromoSystemType == "multi":

        SelectedDept = interaction.namespace.department

        if not SelectedDept:
            return [app_commands.Choice(name="[No Role selected]", value="no_role")]
        Departments = (
            C.get("Promo", {}).get("System", {}).get("multi", {}).get("Departments", [])
        )
        SelectedDeptData = next(
            (
                dept
                for dept_list in Departments
                for dept in dept_list
                if dept.get("name") == SelectedDept
            ),
            None,
        )

        if not SelectedDeptData:
            return [
                app_commands.Choice(
                    name="[Department not found]", value="department_not_found"
                )
            ]

        RoleIDs = [str(role_id) for role_id in SelectedDeptData.get("ranks", [])]
        roles = [
            app_commands.Choice(
                name=interaction.guild.get_role(int(role_id)).name,
                value=str(interaction.guild.get_role(int(role_id)).id),
            )
            for role_id in RoleIDs
            if interaction.guild.get_role(int(role_id))
            and current.lower() in interaction.guild.get_role(int(role_id)).name.lower()
        ]
        return roles[:25]

    if PromoSystemType == "single":
        RoleIDs = [
            str(role_id)
            for role_id in C.get("Promo", {})
            .get("System", {})
            .get("single", {})
            .get("Hierarchy", [])
        ]
        roles = [
            app_commands.Choice(
                name=interaction.guild.get_role(int(role_id)).name,
                value=f"{interaction.guild.get_role(int(role_id)).id}",
            )
            for role_id in RoleIDs
            if interaction.guild.get_role(int(role_id))
            and current.lower() in interaction.guild.get_role(int(role_id)).name.lower()
        ]
        return roles[:25]

    return []
