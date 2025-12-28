import discord
from discord.ext import commands
from utils.emojis import *

from utils.Module import ModuleCheck


class ConnectionRolesEvent(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        addRoles = set(after.roles) - set(before.roles)
        removedRoles = set(before.roles) - set(after.roles)
        if not await ModuleCheck(after.guild.id, "connectionroles"):
            return
        for role in addRoles:
            parentRoles = (
                await self.client.db["connectionroles"]
                .find({"parent": role.id})
                .to_list(length=1000)
            )
            for Parents in parentRoles:
                childRole = after.guild.get_role(Parents.get("child"))
                if childRole:
                    try:
                        await after.add_roles(
                            childRole,
                            reason=f"Connection Roles updated. Connection Name: {Parents.get('name')}",
                        )
                    except discord.Forbidden:
                        print("[⚠️] I don't have permission to add roles to this user")
                        return

        for role in removedRoles:
            parentRoles = (
                await self.client.db["connectionroles"]
                .find({"parent": role.id})
                .to_list(length=1000)
            )
            for Parents in parentRoles:
                childId = Parents.get("child")
                childRole = after.guild.get_role(childId)
                parentRoles = (
                    await self.client.db["connectionroles"]
                    .find({"child": childId})
                    .to_list(length=1000)
                )
                otherParents = any(
                    after.guild.get_role(pr["parent"]) in after.roles
                    for pr in parentRoles
                )

                if not otherParents and childRole:
                    try:
                        await after.remove_roles(
                            childRole,
                            reason=f"Connection Roles updated. Connection Name: {Parents.get('name')}",
                        )
                    except discord.Forbidden:
                        print(
                            "[⚠️] I don't have permission to remove roles from this user"
                        )
                        return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ConnectionRolesEvent(client))
