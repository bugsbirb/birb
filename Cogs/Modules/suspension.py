from utils.permissions import *
import discord
from discord import app_commands
from discord.ext import commands
import datetime
from datetime import timedelta

from utils.emojis import *
import re
import os

from datetime import datetime


from dotenv import load_dotenv

load_dotenv()
environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")

from utils.Module import ModuleCheck
from utils.HelpEmbeds import (
    BotNotConfigured,
    NoPermissionChannel,
    ChannelNotFound,
    ModuleNotEnabled,
    Support,
)


class Suspensions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(description="Suspend a staff member")
    @app_commands.describe(
        staff="What user are you suspending?",
        length="e.g 1w (m/h/d/w)",
        reason="What is the reason for this suspension?",
    )
    async def suspend(
        self,
        ctx: commands.Context,
        staff: discord.Member,
        length: discord.ext.commands.Range[str, 1, 20],
        *,
        reason: discord.ext.commands.Range[str, 1, 2000],
        notes: str = None,
    ):
        await ctx.defer(ephemeral=True)
        if not await ModuleCheck(ctx.guild.id, "suspensions"):

            await ctx.send(embed=ModuleNotEnabled(), view=Support())
            return
        if not await has_admin_role(ctx, "Suspension Permissions"):
            return
        if staff.bot:
            await ctx.send(
                f"  **{ctx.author.display_name}**, you can't suspend a bot.",
            )
            return

        if not re.match(r"^\d+[mhdw]$", length):
            await ctx.send(
                f"  **{ctx.author.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.",
            )
            return

        if ctx.author == staff:
            await ctx.send(
                f"  You can't suspend yourself.",
            )
            return

        if ctx.author.top_role <= staff.top_role:
            await ctx.send(
                f"  **{ctx.author.display_name}**, you don't have authority to suspend this user they are higher then you in the hierarchy.",
                ephemeral=True,
            )
            return

        filter = {"guild_id": ctx.guild.id, "staff": staff.id, "active": True}
        existing_suspensions = await self.client.db["Suspensions"].find_one(filter)

        if existing_suspensions:
            await ctx.send(
                f"  **{staff.display_name}** is already suspended.",
                ephemeral=True,
            )
            return

        duration_value = int(length[:-1])
        duration_unit = length[-1]
        duration_seconds = duration_value

        if duration_unit == "m":
            duration_seconds *= 60
        elif duration_unit == "h":
            duration_seconds *= 3600
        elif duration_unit == "d":
            duration_seconds *= 86400
        elif duration_unit == "w":
            duration_seconds *= 604800

        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        embed = discord.Embed(
            title="",
            description="<:Tip:1223062864793702431> **TIP:** Make sure the bot has permissions to send messages to the channel & to removes roles.",
            color=discord.Color.light_embed(),
        )
        view = RoleTakeAwayYesOrNo(
            staff, ctx.author, reason, end_time, start_time, notes
        )
        await ctx.send(
            "<:Role:1223077527984144474> Would you like to **remove roles** from this person? Don't worry the roles will be **returned** after suspension.",
            view=view,
            embed=embed,
        )

    @commands.hybrid_group()
    async def suspension(self, ctx: commands.Context):
        pass

    @suspension.command(description="View all active suspension")
    async def active(self, ctx: commands.Context):
        if not await ModuleCheck(ctx.guild.id, "suspensions"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Suspension Permissions"):
            return

        filter = {"guild_id": ctx.guild.id, "active": True}

        loa_requests = (
            await self.client.db["Suspensions"].find(filter).to_list(length=None)
        )

        if len(loa_requests) == 0:
            await ctx.send(
                f"  **{ctx.author.display_name}**, there aren't any active suspensions on this server.",
            )
        else:
            embed = discord.Embed(
                title="Active Suspensions", color=discord.Color.dark_embed()
            )
            embed.set_thumbnail(url=ctx.guild.icon)
            embed.set_author(icon_url=ctx.guild.icon, name=ctx.guild.name)
            for request in loa_requests:
                try:
                    user = await self.client.fetch_user(request["staff"])
                except discord.NotFound:
                    continue
                start_time = request["start_time"]
                end_time = request["end_time"]
                start_time = request["start_time"]
                reason = request.get("reason", "None")
                notes = request.get("notes", "N/A")

                embed.add_field(
                    name=f"<:Infraction:1223063128275943544>{user.name.capitalize()}",
                    value=f"{arrow}**Start Date:** <t:{int(start_time.timestamp())}:f>\n{arrow}**End Date:** <t:{int(end_time.timestamp())}:f>\n{arrow}**Reason:** {reason}\n{arrow}**Notes:** {notes}",
                    inline=False,
                )

            await ctx.send(embed=embed)

    @suspension.command(description="Manage suspensions on a user")
    @app_commands.describe(staff="The user to manage suspensions for.")
    async def manage(self, ctx: commands.Context, staff: discord.Member):
        if not await ModuleCheck(ctx.guild.id, "suspensions"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Suspension Permissions"):
            return
        filter = {"guild_id": ctx.guild.id, "staff": staff.id}
        suspension_requests = self.client.db["Suspensions"].find(filter)

        suspension_records = []

        async for request in suspension_requests:
            end_time = request["end_time"]
            start_time = request["start_time"]
            user_id = request["staff"]
            guild_id = request["guild_id"]
            try:
                user = await self.client.fetch_user(request["staff"])
            except discord.NotFound:
                continue
            reason = request["reason"]

            suspension_records.append(
                {
                    "user": user,
                    "start_time": start_time,
                    "end_time": end_time,
                    "reason": reason,
                }
            )

        if suspension_records:
            embed = discord.Embed(title="Suspensions", color=discord.Color.dark_embed())

            for record in suspension_records:
                user = record["user"]
                start_time = record["start_time"]
                end_time = record["end_time"]
                reason = record["reason"]

                embed.add_field(
                    name=f"<:Infraction:1223063128275943544>{user.name.capitalize()}",
                    value=f"{arrow}**Start Date:** <t:{int(start_time.timestamp())}:f>\n{arrow}**End Date:** <t:{int(end_time.timestamp())}:f>\n{arrow}**Reason:** {reason}",
                    inline=False,
                )

            embed.set_thumbnail(url=ctx.guild.icon)
            embed.set_author(icon_url=ctx.guild.icon, name=ctx.guild.name)

            view = SuspensionPanel(staff, ctx.author)
            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(
                f"  **{ctx.author.display_name}**, No suspensions found for this user.",
            )


class Suspension(discord.ui.RoleSelect):
    def __init__(self, user, author, reason, end_time, start_time, notes):
        super().__init__(placeholder="Removed Roles", max_values=10)
        self.user = user
        self.author = author
        self.reason = reason
        self.end_time = end_time
        self.start_time = start_time
        self.notes = notes

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        SelectedRoleIds = [role.id for role in self.values]
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            return await interaction.response.send_message(
                f"  **{interaction.user.display_name}**, you need to select at least one role.",
                ephemeral=True,
            )
        ChannelID = config.get("Suspension", {}).get("channel") or config.get(
            "Infraction", {}
        ).get("channel")
        Channel = None

        if ChannelID:
            try:
                Channel = await interaction.guild.fetch_channel(ChannelID)
            except (discord.NotFound, discord.HTTPException):
                pass

        if not Channel:
            return await interaction.followup.send(
                embed=ChannelNotFound(),
                view=Support(),
                ephemeral=True,
            )
        member = await interaction.guild.fetch_member(interaction.client.user.id)
        if not Channel.permissions_for(member).send_messages:
            return await interaction.followup.send(
                embed=NoPermissionChannel(Channel),
                view=Support(),
                ephemeral=True,
            )

        RESULT = {
            "guild_id": interaction.guild.id,
            "management": interaction.user.id,
            "staff": self.user.id,
            "action": "Suspension",
            "start_time": self.start_time,
            "end_time": self.end_time,
            "roles_removed": SelectedRoleIds,
            "reason": self.reason,
            "active": True,
            "notes": self.notes if self.notes else "N/A",
        }
        RESULT = await interaction.client.db["Suspensions"].insert_one(RESULT)
        interaction.client.dispatch(
            "infraction", RESULT.inserted_id, config, None, "Suspension"
        )
        await interaction.edit_original_response(
            content=f"  **{interaction.user.display_name},** I've successfully suspended **{self.user.display_name}** for <t:{int(self.start_time.timestamp())}:f> - <t:{int(self.end_time.timestamp())}:f>",
            view=None,
            embed=None,
        )
        try:
            member = await interaction.guild.fetch_member(self.user.id)
            if not member:
                return
            roles = [role for role in self.values if role in member.roles]
            await member.remove_roles(*roles)
        except:
            pass


class RoleTakeAwayYesOrNo(discord.ui.View):
    def __init__(self, user, author, reason, end_time, start_time, notes):
        super().__init__(timeout=360)
        self.user = user
        self.author = author
        self.reason = reason
        self.end_time = end_time
        self.start_time = start_time
        self.notes = notes

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def Yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        view = RoleTakeAwayView(
            self.user,
            self.author,
            self.reason,
            self.end_time,
            self.start_time,
            self.notes,
        )
        await interaction.response.edit_message(
            content="<:Role:1223077527984144474> Select the **roles** that will be removed & then given back after the suspension is over.",
            embed=None,
            view=view,
        )

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def No(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your view",
                color=discord.Colour.dark_embed(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            return await interaction.response.send_message(
                embed=BotNotConfigured(),
                ephemeral=True,
            )
        ChannelID = config.get("Suspension", {}).get("channel") or config.get(
            "Infraction", {}
        ).get("channel")
        Channel = None

        if ChannelID:
            try:
                Channel = await interaction.guild.fetch_channel(ChannelID)
            except (discord.NotFound, discord.HTTPException):
                pass

        if not Channel:
            return await interaction.followup.send(
                embed=ChannelNotFound(),
                view=Support(),
                ephemeral=True,
            )
        member = await interaction.guild.fetch_member(interaction.client.user.id)
        if not Channel.permissions_for(member).send_messages:
            return await interaction.followup.send(
                embed=NoPermissionChannel(Channel),
                view=Support(),
                ephemeral=True,
            )
        Suspension = {
            "guild_id": interaction.guild.id,
            "management": interaction.user.id,
            "staff": self.user.id,
            "action": "Suspension",
            "start_time": self.start_time,
            "end_time": self.end_time,
            "reason": self.reason,
            "active": True,
            "notes": self.notes if self.notes else "N/A",
        }
        RESULT = await interaction.client.db["Suspensions"].insert_one(Suspension)
        interaction.client.dispatch(
            "infraction", RESULT.inserted_id, config, None, "Suspension"
        )
        await interaction.edit_original_response(
            content=f"  **{interaction.user.display_name},** I've successfully suspended **{self.user.display_name}** for <t:{int(self.start_time.timestamp())}:f> - <t:{int(self.end_time.timestamp())}:f>",
            view=None,
            embed=None,
        )


class RoleTakeAwayView(discord.ui.View):
    def __init__(self, user, author, reason, end_time, start_time, notes):
        super().__init__()
        self.user = user
        self.author = author
        self.reason = reason
        self.end_time = end_time
        self.start_time = start_time
        self.add_item(
            Suspension(
                self.user,
                self.author,
                self.reason,
                self.end_time,
                self.start_time,
                notes,
            )
        )


class SuspensionPanel(discord.ui.View):
    def __init__(self, user, author):
        super().__init__(timeout=360)
        self.user = user
        self.author = author

    @discord.ui.button(
        label="Suspension Void",
        style=discord.ButtonStyle.grey,
        emoji="<:Exterminate:1223063042246443078>",
    )
    async def SuspensionVoid(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.mention},** this is not your view.",
                color=discord.Colour.dark_grey(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        suspension_record = await interaction.client.db["Suspensions"].find_one(
            {"guild_id": interaction.guild.id, "staff": self.user.id}
        )
        if suspension_record:
            roles_removed = suspension_record.get("roles_removed", [])
            if roles_removed:
                roles_to_return = [
                    discord.utils.get(interaction.guild.roles, id=role_id)
                    for role_id in roles_removed
                ]
                try:
                    member = await interaction.guild.fetch_member(self.user.id)
                except:
                    member = None

                print(f"roles_removed: {roles_removed}")
                print(f"roles_to_return: {roles_to_return}")

                if roles_to_return and member:
                    await interaction.response.defer()
                    await interaction.edit_original_response(
                        content="<a:Loading:1167074303905386587> Loading...",
                        embed=None,
                        view=None,
                    )
                    try:
                        await member.add_roles(*roles_to_return)
                        await interaction.edit_original_response(
                            content=f"  Suspension has been voided. Roles have been restored.",
                            view=None,
                            embed=None,
                        )
                        await interaction.client.db["Suspensions"].delete_one(
                            {"guild_id": interaction.guild.id, "staff": self.user.id}
                        )

                    except discord.Forbidden:
                        await interaction.edit_original_response(
                            content=f"  Failed to restore roles due to insufficient permissions.",
                            view=None,
                            embed=None,
                        )
                        return
                    try:
                        await member.send(
                            f"<:bin:1235001855721865347> Your suspension has been voided **@{interaction.guild.name}**"
                        )
                    except discord.Forbidden:
                        print("Failed to send suspension message to user")
                        pass
            else:
                member = await interaction.guild.fetch_member(self.user.id)
                await interaction.client.db["Suspensions"].delete_one(
                    {"guild_id": interaction.guild.id, "staff": self.user.id}
                )
                await interaction.response.edit_message(
                    content=f"  Suspension has been voided.", embed=None, view=None
                )
                try:
                    await member.send(
                        f"<:bin:1235001855721865347> Your suspension has been voided **@{interaction.guild.name}**"
                    )

                except discord.Forbidden:
                    print("Failed to send suspension message to user")

        else:
            await interaction.response.send_message(
                f"  No suspension found.", ephemeral=True
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Suspensions(client))
