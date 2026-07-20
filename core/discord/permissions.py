import discord
from motor.motor_asyncio import AsyncIOMotorClient

from core.discord.HelpEmbeds import (
    BotNotConfigured,
    Support,
)
from core.discord.emojis import *
from core.errors.Permissions import *
from core.format import CommandType

ENVIRONMENT = os.getenv("ENVIRONMENT")
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = (
    client["BETA"]
    if ENVIRONMENT and ENVIRONMENT.lower() == "development"
    else client["astro"]
)

premiums = db["Subscriptions"]
blacklist = db["blacklists"]
Configuration = db["Config"]


def Permissions(permissions: Literal["Admin", "Staff"]):
    async def predicate(interaction: discord.Interaction) -> bool:
        author, guild, _, command = CommandType(interaction)
        Config = await Configuration.find_one({"_id": guild.id})
        if not Config:
            raise MissingSetup()
        if Config.get("Advanced Permissions", None):
            if command:
                if (
                    command.qualified_name
                    in Config.get("Advanced Permissions", {}).keys()
                ):
                    Permissions = Config.get("Advanced Permissions", {}).get(
                        command.qualified_name, []
                    )
                    if not isinstance(Permissions, list):
                        Permissions = [Permissions]
                    if any(role.id in Permissions for role in author.roles):
                        return True
                    else:
                        raise MissingAdvancedPermissions()
        if not Config.get("Permissions"):
            raise MissingPermissionSetup("All")

        if not Config.get("Permissions").get("adminrole"):
            raise MissingPermissionSetup("Admin")

        if permissions == "Admin":
            if RequireAdmin(Config, author):
                return True

        if permissions == "Staff":
            if RequireStaff(Config, author):
                return True

        raise MissingPermission(permissions)

    def decorator(func):
        func = app_commands.check(predicate)(func)
        func = commands.check(predicate)(func)
        return func

    return decorator


def RequireStaff(Config: dict, author: discord.Member):
    StaffIDs = Config.get("Permissions").get("staffrole")
    if not isinstance(StaffIDs, list):
        StaffIDs = [StaffIDs]

    if StaffIDs:
        if any(role.id in StaffIDs for role in author.roles):
            return True

    AdminIDs = Config.get("Permissions").get("adminrole")
    if not isinstance(AdminIDs, list):
        AdminIDs = [AdminIDs]

    if AdminIDs:
        if any(role.id in AdminIDs for role in author.roles):
            return True
        if any(role.id in StaffIDs for role in author.roles):
            return True
    return False


def RequireAdmin(Config: dict, author: discord.Member):
    Ids = Config.get("Permissions").get("adminrole")
    if not isinstance(Ids, list):
        Ids = [Ids]

    if any(role.id in Ids for role in author.roles):
        return True
    if author.guild_permissions.administrator:
        return True
    return False


async def premium(id):
    R1 = await Configuration.find_one({"_id": id, "Features": {"$in": ["PREMIUM"]}})
    R2 = await premiums.find_one({"guilds": {"$in": [id]}})
    if R1 or R2:
        return True
    return False


# ————————————————— Deprecated - for component interaction ———————————————————————————————————
async def has_staff_role(I: discord.Interaction):
    if isinstance(I, commands.Context):
        author = I.author
        guild = I.guild
        send = I.send
    else:
        author = I.user
        guild = I.guild
        if I.response.is_done():
            send = I.followup.send

        else:
            send = I.response.send_message

    Config = await Configuration.find_one({"_id": guild.id})
    if not Config:
        await send(embed=BotNotConfigured(), view=Support())
        return False

    if Config.get("Advanced Permissions", None):
        if I.command:
            if (
                I.command.qualified_name
                in Config.get("Advanced Permissions", {}).keys()
            ):
                Permissions = Config.get("Advanced Permissions", {}).get(
                    I.command.qualified_name, []
                )
                if not isinstance(Permissions, list):
                    Permissions = [Permissions]
                if any(role.id in Permissions for role in author.roles):
                    return True
                else:
                    await send(
                        f"{no} **{author.display_name}**, you don't have permission to use this command.\n-# Advanced Permission"
                    )
                    return False

    if not Config.get("Permissions"):
        await send(
            f"{no} **{author.display_name}**, the permissions haven't been setup yet please run `/config`"
        )
        return False

    if not Config.get("Permissions").get("adminrole"):
        await send(
            f"{no} **{author.display_name}**, the admin role hasn't been setup yet please run `/config`"
        )
        return False

    if Config.get("Permissions").get("staffrole"):
        StaffIDs = Config.get("Permissions").get("staffrole")
        if not isinstance(StaffIDs, list):
            StaffIDs = [StaffIDs]

        if not Config.get("Permissions").get("adminrole"):
            if any(role.id in StaffIDs for role in author.roles):
                return True
        else:
            AdminIDs = Config.get("Permissions").get("adminrole")
            if not isinstance(AdminIDs, list):
                AdminIDs = [AdminIDs]
            if any(role.id in AdminIDs for role in author.roles):
                return True
            if any(role.id in StaffIDs for role in author.roles):
                return True

    await send(
        f"{no} **{author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Staff Role`",
    )
    return False


async def check_admin_and_staff(guild: discord.Guild, user: discord.User):
    Config = await Configuration.find_one({"_id": guild.id})
    if not Config or not Config.get("Permissions"):
        return False

    staff_role_ids = Config["Permissions"].get("staffrole", [])
    staff_role_ids = (
        staff_role_ids if isinstance(staff_role_ids, list) else [staff_role_ids]
    )

    admin_role_ids = Config["Permissions"].get("adminrole", [])
    admin_role_ids = (
        admin_role_ids if isinstance(admin_role_ids, list) else [admin_role_ids]
    )

    if any(role.id in staff_role_ids + admin_role_ids for role in user.roles):
        return True
    return False


async def has_admin_role(
    I: discord.Interaction, permissions=None, msg=None, ephemeral=False
):
    if isinstance(I, commands.Context):
        author = I.author
        guild = I.guild
        send = I.send
    else:
        author = I.user
        guild = I.guild
        if I.response.is_done():
            send = I.followup.send
        else:
            send = I.response.send_message

    if msg:
        send = msg.edit

    blacklists = await blacklist.find_one({"user": author.id})
    if blacklists:
        await send(
            f"{no} **{author.display_name}**, you are blacklisted from using **Birb.**",
            ephemeral=ephemeral,
        )
        return False

    Config = await Configuration.find_one({"_id": guild.id})
    if not Config:
        await send(embed=BotNotConfigured(), view=Support())
        return False

    if Config.get("Advanced Permissions", None):
        if I.command:
            if (
                I.command.qualified_name
                in Config.get("Advanced Permissions", {}).keys()
            ):
                Permissions = Config.get("Advanced Permissions", {}).get(
                    I.command.qualified_name, []
                )
                if not isinstance(Permissions, list):
                    Permissions = [Permissions]
                if any(role.id in Permissions for role in author.roles):
                    return True
                else:
                    await send(
                        f"{no} **{author.display_name}**, you don't have permission to use this command.\n-# Advanced Permission",
                        ephemeral=ephemeral,
                    )
                    return False

    if not Config.get("Permissions"):
        await send(
            f"{no} **{author.display_name}**, the permissions haven't been setup yet please run `/config`",
            ephemeral=ephemeral,
        )
        return False

    if not Config.get("Permissions").get("adminrole"):
        await send(
            f"{no} **{author.display_name}**, the admin role hasn't been setup yet please run `/config`",
            ephemeral=ephemeral,
        )
        return False

    if Config.get("Permissions").get("adminrole"):
        Ids = Config.get("Permissions").get("adminrole")
        if not isinstance(Ids, list):
            Ids = [Ids]

        if any(role.id in Ids for role in author.roles):
            return True
    else:
        if author.guild_permissions.administrator:
            await send(
                f"{no} **{author.display_name}**, the admin role isn't set please run </config:1140463441136586784>",
                view=Support(),
                ephemeral=ephemeral,
            )
        else:
            await send(
                f"{no} **{author.display_name}**, the admin role is not setup please tell an admin to run </config:1140463441136586784> to fix it.",
                view=Support(),
                ephemeral=ephemeral,
            )
        return False

    await send(
        f"{no} **{author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`",
        ephemeral=ephemeral,
    )
    return False
