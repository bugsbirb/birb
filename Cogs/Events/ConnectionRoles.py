import discord
from discord.ext import commands
from utils.emojis import *

from utils.Module import ModuleCheck

class ConnectionRolesEvent(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        added_roles = set(after.roles) - set(before.roles)
        removed_roles = set(before.roles) - set(after.roles)
        guild = after.guild
        if not await ModuleCheck(guild.id, "connectionroles"):
            return

        for role in added_roles:
            parent_roles_data = await self.client.db['connectionroles'].find({"parent": role.id}).to_list(
                length=1000
            )
            for parent_role_data in parent_roles_data:
                child_role_id = parent_role_data["child"]
                child_role = after.guild.get_role(child_role_id)
                if child_role:
                    try:
                        await after.add_roles(child_role, reason="Connection Roles updated")
                    except discord.Forbidden:
                        print("[⚠️] I don't have permission to add roles to this user")
                        return

        for role in removed_roles:
            parent_roles_data = await self.client.db['connectionroles'].find({"parent": role.id}).to_list(
                length=1000
            )
            for parent_role_data in parent_roles_data:
                child_role_id = parent_role_data["child"]
                child_role = after.guild.get_role(child_role_id)
                parent_roles = await self.client.db['connectionroles'].find(
                    {"child": child_role_id}
                ).to_list(length=1000)
                has_other_parent_role = any(
                    after.guild.get_role(pr["parent"]) in after.roles
                    for pr in parent_roles
                )

                if not has_other_parent_role and child_role:
                    try:
                        await after.remove_roles(child_role, reason="Connection Roles updated")
                    except discord.Forbidden:
                        print(
                            "[⚠️] I don't have permission to remove roles from this user"
                        )
                        return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ConnectionRolesEvent(client))
