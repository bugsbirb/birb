import discord
from discord.ext import commands
from typing import Literal
import os
from utils.emojis import *
from utils.ui import YesOrNo
import asyncio
from utils.permissions import has_admin_role

from discord import app_commands

class Link(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    integrations = app_commands.Group(
        name="integrations",
        description="integrations",
    )

    async def Request(
        ctx: commands.Context, interaction: discord.Interaction, current: str
    ):
        try:
            from utils.roblox import GetRequests, FetchUsersByID
            import re

            Requests = await GetRequests(interaction)
            if not Requests:
                return [
                    app_commands.Choice(
                        name="No current requests.", value="Not a role idiot"
                    )
                ]
            if Requests == 403:
                return [
                    app_commands.Choice(
                        name="Please relink you are missing a scope.",
                        value="Not a role idiot",
                    )
                ]
            if Requests == 401:
                return [
                    app_commands.Choice(
                        name="Please link with /integrations link.",
                        value="Not a role idiot",
                    )
                ]

            user_ids = [req.get("user").split("/")[1] for req in Requests]
            RobloxUsers = await FetchUsersByID(user_ids)
            id_to_data = {
                str(user["id"]): {
                    "displayName": user.get("displayName", "Unknown User"),
                    "name": user.get("name", "Unknown Name"),
                }
                for user in RobloxUsers
            }

            for req in Requests:
                user_id = req.get("user").split("/")[1]
                req["displayName"] = id_to_data.get(user_id, {}).get(
                    "displayName", "Unknown User"
                )
                req["name"] = id_to_data.get(user_id, {}).get("name", "Unknown Name")

            filtered_requests = (
                Requests
                if not current
                else [
                    req
                    for req in Requests
                    if re.search(
                        re.escape(current), req.get("displayName", ""), re.IGNORECASE
                    )
                ]
            )

            return [
                app_commands.Choice(
                    name=request.get("displayName", "Unknown User"),
                    value=request.get("name") or "Unknown Name",
                )
                for request in filtered_requests[:25]
            ]

        except (ValueError, discord.HTTPException, discord.NotFound, TypeError):
            return [
                app_commands.Choice(
                    name="[ERROR CONTACT SUPPORT]", value="[ERROR CONTACT SUPPORT]"
                )
            ]

    async def Roles(
        ctx: commands.Context, interaction: discord.Interaction, current: str
    ):
        try:
            from utils.roblox import GroupRoles

            Roles = await GroupRoles(interaction)

            if Roles == 1:
                return [
                    app_commands.Choice(
                        name="Please link with /integrations link.",
                        value="Not a role idiot",
                    )
                ]
            if not Roles:
                return [
                    app_commands.Choice(
                        name="No roles found.", value="Not a role idiot"
                    )
                ]
            Roles = Roles.get("groupRoles")
            return [
                app_commands.Choice(
                    name=role.get("displayName"), value=role.get("path")
                )
                for role in Roles
            ]
        except (ValueError, discord.HTTPException, discord.NotFound, TypeError):
            return [
                app_commands.Choice(
                    name="[ERROR CONTACT SUPPORT]", value="[ERROR CONTACT SUPPORT]"
                )
            ]

    @commands.hybrid_group()
    async def group(self, ctx):
        return

    @group.group()
    async def membership(self, ctx):
        return

    @group.group()
    async def requests(self, ctx):
        return

    @requests.command(description="Accept a group join request.")
    @app_commands.autocomplete(roblox=Request)
    async def accept(self, ctx: commands.Context, roblox: str):
        if not await has_admin_role(ctx, "Infraction Permissions"):
            return
        from utils.roblox import (
            AcceptRequest,
            GetRequest,
            GetValidToken,
            FetchRobloxUser,
        )
        from utils.HelpEmbeds import NotRobloxLinked

        await ctx.defer()

        token = await GetValidToken(user=ctx.author)
        if not token:
            return await ctx.send(embed=NotRobloxLinked(), ephemeral=True)

        c = await self.client.config.find_one({"_id": ctx.guild.id})
        if not c.get("groups"):
            return 2

        group = c.get("groups", {}).get("id", None) if c else None
        if not (group, c):
            return await ctx.send(
                f"  **{ctx.author.display_name},** a group hasn't been linked.",
                ephemeral=True,
            )
        RobloxUser = await FetchRobloxUser(roblox)
        if not RobloxUser:
            return await ctx.send(
                f"  **{ctx.author.display_name},** I couldn't find this user.",
                ephemeral=True,
            )
        Request = await GetRequest(group, RobloxUser[0].get("id"), ctx.author)
        if not Request:
            return await ctx.send(
                f"  **{ctx.author.display_name},** this user doesn't have a request.",
                ephemeral=True,
            )
        if Request == 403:
            return await ctx.send(
                f"  **{ctx.author.display_name},** please relink your account. There is a missing scope.",
                ephemeral=True,
            )

        join_request_path = Request.get("groupJoinRequests", {})[0].get("path")
        join_request_id = join_request_path.split("/")[-1]
        request = await AcceptRequest(group, join_request_id, user=ctx.author)
        if not request:
            return await ctx.send(
                f"  **{ctx.author.display_name},** you couldn't accept this request. Make sure you have permission to do this.",
                ephemeral=True,
            )
        await ctx.send(
            f"  **{ctx.author.display_name},** sucessfully accepted the request."
        )

    @requests.command(description="Reject a group join request.")
    @app_commands.autocomplete(roblox=Request)
    async def reject(self, ctx: commands.Context, roblox: str):
        if not await has_admin_role(ctx, "Infraction Permissions"):
            return
        from utils.roblox import (
            RejectRequest,
            GetRequest,
            GetValidToken,
            FetchRobloxUser,
        )
        from utils.HelpEmbeds import NotRobloxLinked


        if not await has_admin_role(ctx, "Infraction Permissions"):
            return
        from utils.roblox import (
            AcceptRequest,
            GetRequest,
            GetValidToken,
            FetchRobloxUser,
        )
        from utils.HelpEmbeds import NotRobloxLinked

        await ctx.defer()

        token = await GetValidToken(user=ctx.author)
        if not token:
            return await ctx.send(embed=NotRobloxLinked(), ephemeral=True)

        c = await self.client.config.find_one({"_id": ctx.guild.id})
        if not c.get("groups"):
            return 2

        group = c.get("groups", {}).get("id", None) if c else None
        if not (group, c):
            return await ctx.send(
                f"  **{ctx.author.display_name},** a group hasn't been linked.",
                ephemeral=True,
            )
        RobloxUser = await FetchRobloxUser(roblox)
        if not RobloxUser:
            return await ctx.send(
                f"  **{ctx.author.display_name},** I couldn't find this user.",
                ephemeral=True,
            )
        Request = await GetRequest(group, RobloxUser[0].get("id"), ctx.author)
        if not Request:
            return await ctx.send(
                f"  **{ctx.author.display_name},** this user doesn't have a request.",
                ephemeral=True,
            )
        if Request == 403:
            return await ctx.send(
                f"  **{ctx.author.display_name},** please relink your account. There is a missing scope.",
                ephemeral=True,
            )

        join_request_path = Request.get("groupJoinRequests", {})[0].get("path")
        join_request_id = join_request_path.split("/")[-1]
        request = await RejectRequest(group, join_request_id, user=ctx.author)
        if not request:
            return await ctx.send(
                f"  **{ctx.author.display_name},** you couldn't accept this request. Make sure you have permission to do this.",
                ephemeral=True,
            )
        await ctx.send(
            f"  **{ctx.author.display_name},** sucessfully denied the request."
        )

    @membership.command(description="Update a users group roles.")
    @app_commands.autocomplete(role=Roles)
    async def update(self, ctx: commands.Context, roblox: str, role: str):
        if not await has_admin_role(ctx, "Infraction Permissions"):
            return
        from utils.roblox import UpdateMembership, GroupRoles, FetchRobloxUser

        c = await self.client.config.find_one({"_id": ctx.guild.id})

        Roles = await GroupRoles(ctx.interaction)
        if Roles == 0:
            from utils.HelpEmbeds import NotRobloxLinked

            return await ctx.send(embed=NotRobloxLinked(), ephemeral=True)
        if Roles == 1:

            return await ctx.send(
                f"  **{ctx.author.display_name},** you don't have access to the groups roles.",
                ephemeral=True,
            )
        if Roles == 2:
            return await ctx.send(
                f"  **{ctx.author.display_name},** a group hasn't been linked.",
                ephemeral=True,
            )
        RobloxUser = await FetchRobloxUser(roblox)
        if not RobloxUser:
            return await ctx.send(
                f"  **{ctx.author.display_name},** I couldn't find this user.",
                ephemeral=True,
            )
        update = await UpdateMembership(
            roblox_id=RobloxUser[0].get("id"), author=ctx.author, config=c, role=role
        )
        if update == 404:
            return await ctx.send(
                f"  **{ctx.author.display_name},** you don't have permission to update this user to that role. Make sure you actually have permission to do this.",
                ephemeral=True,
            )
        await ctx.send(
            f"  **{ctx.author.name},** succesfully updated members role."
        )

    @integrations.command(
        description="Link an integration to your discord account (e.g., Roblox)"
    )
    async def link(
        self,
        interaction: discord.Interaction,
        service: Literal["Roblox Groups", "Roblox Auth"],
    ):
        AlreadyRegistered = await interaction.client.db['integrations'].find_one(
            {"discord_id": str(interaction.user.id)}
        )
        msg = None
        await interaction.response.defer(ephemeral=True)
        if AlreadyRegistered:
            view = YesOrNo()
            msg: discord.Message = await interaction.followup.send(
                embed=discord.Embed(
                    title="Already Linked",
                    description="You are already linked. Do you want to reverify?",
                    color=discord.Color.dark_embed(),
                ),
                view=view,
                ephemeral=True,
            )
            await view.wait()
            if view.value is None:
                await interaction.followup.send(
                    "You took too long to respond.", ephemeral=True
                )
                return
            if not view.value:
                return await interaction.followup.send(
                    f"  cancelled.", ephemeral=True
                )

        await self.client.db['Pending'].update_one(
            {"user": interaction.user.id},
            {"$set": {"user": str(interaction.user.id)}},
            upsert=True,
        )
        embed = discord.Embed()
        embed.set_author(
            name="Verify With Roblox",
            icon_url="https://cdn.discordapp.com/emojis/1206670134064717904.webp?size=96",
        )
        embed.description = "You are authorising to manage the roblox group from the discord.\n\n-# Press the button link below."

        view = discord.ui.View()
        if service == "Roblox Groups":
            view.add_item(
                discord.ui.Button(
                    label="Authorise",
                    style=discord.ButtonStyle.link,
                    url=f"https://authorize.roblox.com/?client_id={os.getenv('CLIENT_ID')}&response_type=code&redirect_uri=https%3A%2F%2Fverify.astrobirb.dev%2Fauth&scope=group%3Awrite+group%3Aread+openid+profile&o=&state={interaction.user.id}&step=accountConfirm",
                )
            )
        else:
            view.add_item(
                discord.ui.Button(
                    label="Authorise",
                    style=discord.ButtonStyle.link,
                    url=f"https://authorize.roblox.com/?client_id={os.getenv('CLIENT_ID')}&response_type=code&redirect_uri=https%3A%2F%2Fverify.astrobirb.dev%2Fauth&scope=openid+profile&o=&state={interaction.user.id}&step=accountConfirm",
                )
            )

        if AlreadyRegistered:
            msg: discord.Message = await interaction.followup.edit_message(
                msg.id, embed=embed, view=view
            )
        else:
            msg: discord.Message = await interaction.followup.send(
                embed=embed, view=view, ephemeral=True
            )

        await interaction.client.db['integrations'].delete_one({"discord_id": str(interaction.user.id)})

        try:
            await asyncio.wait_for(
                self.wait_for_token_verification(interaction), timeout=180
            )
            if await interaction.client.db['integrations'].find_one({"discord_id": str(interaction.user.id)}):
                if msg:
                    if service == "Roblox Groups":
                        embed = (
                            discord.Embed(color=discord.Color.brand_green())
                            .set_author(
                                name="Successfully Verified",
                                icon_url=interaction.user.display_avatar,
                            )
                            .add_field(
                                name="What you can do!",
                                value="> * Manage group users\n> * Infraction Types (with group role management.)",
                            )
                        )
                    else:
                        embed = discord.Embed(
                            color=discord.Color.brand_green()
                        ).set_author(
                            name="Successfully Verified",
                            icon_url=interaction.user.display_avatar,
                        )
                    await msg.edit(view=None, embed=embed)
                    await interaction.client.db['Pending'].delete_one({"user": interaction.user.id})
                return
        except asyncio.TimeoutError:
            if msg:
                await interaction.edit_original_response(
                    content="Verification timed out."
                )
            return

    async def wait_for_token_verification(self, interaction: discord.Interaction):
        attempts = 0
        while attempts < 60:
            if await interaction.client.db['integrations'].find_one({"discord_id": str(interaction.user.id)}):
                return True
            attempts += 1
            print("Checking token...")
            await asyncio.sleep(3)
        return False


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Link(client))
