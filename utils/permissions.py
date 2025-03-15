import discord
import sys
from discord.ext import commands

sys.dont_write_bytecode = True
import os
from motor.motor_asyncio import AsyncIOMotorClient
from utils.emojis import *


from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo["astro"]

premiums = db["premium"]
blacklist = db["blacklists"]
Configuration = db["Config"]

from utils.HelpEmbeds import (
    BotNotConfigured,
    Support,
)


async def has_staff_role(toy, permissions=None):
    if isinstance(toy, commands.Context):
        author = toy.author
        guild = toy.guild
        send = toy.send
    else:
        author = toy.user
        guild = toy.guild
        send = toy.response.send_message

    blacklists = await blacklist.find_one({"user": author.id})
    if blacklists:
        await send(
            f"  **{author.display_name}**, you are blacklisted from using **Astro Birb.** You are probably a shitty person and that might be why?",
            ephemeral=True,
        )
        return False

    Config = await Configuration.find_one({"_id": guild.id})
    if not Config:
        await send(embed=BotNotConfigured(), view=Support())
        return False

    if Config.get("Advanced Permissions", None):
        if toy.command.qualified_name in Config.get("Advanced Permissions", {}).keys():
            Permissions = Config.get("Advanced Permissions", {}).get(
                toy.command.qualified_name, []
            )
            if not isinstance(Permissions, list):
                Permissions = [Permissions]
            if any(role.id in Permissions for role in author.roles):
                return True
            else:
                await send(
                    f"  **{author.display_name}**, you don't have permission to use this command.\n-# Advanced Permission",
                    ephemeral=True,
                )
                return False

    if not Config.get("Permissions"):
        await send(
            f"  **{author.display_name}**, the permissions haven't been setup yet please run `/config`"
        )
        return False

    if not Config.get("Permissions").get("adminrole"):
        await send(
            f"  **{author.display_name}**, the admin role hasn't been setup yet please run `/config`"
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
        f"  **{author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Staff Role`",
    )
    return False


async def premium(id):
    result = await premiums.find_one({"guild_id": id})
    if result:
        return True
    else:
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


async def has_admin_role(toy, permissions=None):
    if isinstance(toy, commands.Context):
        author = toy.author
        guild = toy.guild
        send = toy.send
        s = "context"
    else:
        author = toy.user
        guild = toy.guild
        send = toy.followup.send
        s = "interaction"

    blacklists = await blacklist.find_one({"user": author.id})
    if blacklists:
        await send(
            f"  **{author.display_name}**, you are blacklisted from using **Astro Birb.** You are probably a shitty person and that might be why?",
            ephemeral=True,
        )
        return False

    filter = {"guild_id": guild.id}
    Config = await Configuration.find_one({"_id": guild.id})
    if not Config:
        await send(embed=BotNotConfigured(), view=Support())
        return False

    if Config.get("Advanced Permissions", None):
        if toy.command:
            if (
                toy.command.qualified_name
                in Config.get("Advanced Permissions", {}).keys()
            ):
                Permissions = Config.get("Advanced Permissions", {}).get(
                    toy.command.qualified_name, []
                )
                if not isinstance(Permissions, list):
                    Permissions = [Permissions]
                if any(role.id in Permissions for role in author.roles):
                    return True
                else:
                    await send(
                        f"  **{author.display_name}**, you don't have permission to use this command.\n-# Advanced Permission",
                        ephemeral=True,
                    )
                    return False

    if not Config.get("Permissions"):
        await send(
            f"  **{author.display_name}**, the permissions haven't been setup yet please run `/config`",
            ephemeral=True if s == "interaction" else False,
        )
        return False

    if not Config.get("Permissions").get("adminrole"):
        await send(
            f"  **{author.display_name}**, the admin role hasn't been setup yet please run `/config`",
            ephemeral=True if s == "interaction" else False,
        )
        return False

    # advancedresult = await advancedpermissions.find(filter).to_list(length=None)
    # if advancedresult:
    #     for advanced in advancedresult:
    #         if permissions in advanced.get("permissions", []):
    #             if any(role.id == advanced.get("role") for role in author.roles):
    #                 return True

    if Config.get("Permissions").get("adminrole"):
        Ids = Config.get("Permissions").get("adminrole")
        if not isinstance(Ids, list):
            Ids = [Ids]

        if any(role.id in Ids for role in author.roles):
            return True
    else:
        if author.guild_permissions.administrator:
            await send(
                f"  **{author.display_name}**, the admin role isn't set please run </config:1140463441136586784>",
                view=PermissionsButtons(),
                ephemeral=True if s == "interaction" else False,
            )
        else:
            await send(
                f"  **{author.display_name}**, the admin role is not setup please tell an admin to run </config:1140463441136586784> to fix it.",
                view=PermissionsButtons(),
                ephemeral=True if s == "interaction" else False,
            )
        return False

    await send(
        f"  **{author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`",
        ephemeral=True if s == "interaction" else False,
    )
    return False


class PermissionsButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        url1 = "https://discord.gg/DhWdgfh3hN"
        self.add_item(
            discord.ui.Button(
                label="Support Server", url=url1, style=discord.ButtonStyle.blurple
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Documentation",
                url="https://docs.astrobirb.dev/overview",
                style=discord.ButtonStyle.blurple,
            )
        )
