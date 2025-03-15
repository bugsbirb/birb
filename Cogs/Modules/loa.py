import discord
from discord.ext import commands
from datetime import timedelta
from discord import app_commands
from discord.ext import tasks
from utils.emojis import *
import os
from dotenv import load_dotenv

from datetime import datetime
import re
from utils.Module import ModuleCheck

load_dotenv()

from utils.HelpEmbeds import (
    BotNotConfigured,
    NoPermissionChannel,
    ChannelNotFound,
    ModuleNotEnabled,
    NoChannelSet,
    Support,
    ModuleNotSetup,
)

from utils.permissions import has_admin_role, has_staff_role

environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")


class LOA(discord.ui.Modal, title="Create Leave Of Absence"):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author

    Duration = discord.ui.TextInput(
        label="Duration",
        placeholder="e.g 1w (m/h/d/w)",
    )

    reason = discord.ui.TextInput(label="Reason", placeholder="Reason for their loa")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            duration = self.Duration.value
            reason = self.reason.value
            if interaction.user.id != self.author.id:
                embed = discord.Embed(
                    description=f"**{interaction.user.display_name},** this is not your view",
                    color=discord.Colour.dark_embed(),
                )
                return await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )
            if not re.match(r"^\d+[smhdw]$", duration):
                await interaction.response.send_message(
                    f"  **{interaction.user.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.",
                    ephemeral=True,
                )
                return
            duration_value = int(duration[:-1])
            duration_unit = duration[-1]
            duration_seconds = duration_value
            if duration_unit == "s":
                duration_seconds *= 1
            elif duration_unit == "m":
                duration_seconds *= 60
            elif duration_unit == "h":
                duration_seconds *= 3600
            elif duration_unit == "d":
                duration_seconds *= 86400
            elif duration_unit == "w":
                duration_seconds *= 604800

            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=duration_seconds)

            Config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            if not Config:
                return await interaction.response.send_message(
                    embed=BotNotConfigured(), ephemeral=True, view=Support()
                )
            if not Config.get("LOA"):
                return await interaction.response.send_message(
                    embed=ModuleNotSetup(), ephemeral=True, view=Support()
                )
            if not Config.get("LOA", {}).get("channel"):
                return await interaction.response.send_message(
                    embed=NoChannelSet(), ephemeral=True, view=Support()
                )
            channel_id = Config.get("LOA", {}).get("channel")
            channel = await interaction.guild.fetch_channel(channel_id)
            if not channel:
                return await interaction.response.send_message(
                    embed=NoChannelSet(), ephemeral=True, view=Support()
                )
            embed = discord.Embed(
                title="LOA Created",
                description=f"* **User:** {self.user.mention}\n* **Start Date**: <t:{int(start_time.timestamp())}:f>\n* **End Date:** <t:{int(end_time.timestamp())}:f>\n* **Reason:** {self.reason}",
                color=discord.Color.dark_embed(),
            )
            embed.set_author(
                icon_url=self.user.display_avatar, name=self.user.display_name
            )
            embed.set_thumbnail(url=self.user.display_avatar)
            loadata = {
                "guild_id": interaction.guild.id,
                "user": self.user.id,
                "start_time": start_time,
                "end_time": end_time,
                "reason": reason,
                "active": True,
            }
            if Config.get("LOA", {}).get("role"):
                role = discord.utils.get(
                    interaction.guild.roles, id=Config.get("LOA", {}).get("role")
                )
                if role:
                    try:
                        await self.user.add_roles(role)
                    except discord.Forbidden:
                        await interaction.response.edit_message(
                            content=f"  I don't have permission to add roles."
                        )
                        return
            try:
                await channel.send(
                    f"<:Add:1163095623600447558> LOA was created by **@{interaction.user.display_name}**",
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(
                        users=True,
                        everyone=False,
                        roles=False,
                        replied_user=False,
                    ),
                )
            except discord.Forbidden:
                await interaction.response.edit_message(
                    content=f"  I don't have permission to view that channel."
                )
                return
            await interaction.response.edit_message(
                content=f"  Created LOA for **@{self.user.display_name}**",
                embed=embed,
                view=None,
            )
            await interaction.client.db["loa"].insert_one(loadata)

            try:
                await self.user.send(
                    f"<:Add:1163095623600447558> A LOA was created for you **@{interaction.guild.name}**",
                    embed=embed,
                )
            except discord.Forbidden:
                pass
        except Exception as e:
            print(e)
            await interaction.response.send_message(
                f"  error error big massive error: {e}"
            )
            return


class loamodule(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_group()
    async def loa(self, ctx: commands.Context):
        pass

    @loa.command(description="Manage someone leave of Absence")
    @app_commands.describe(user="The user you want to manage LOA for")
    async def manage(self, ctx: commands.Context, user: discord.Member):
        if self.client.loa_maintenance is True:
            await ctx.send(
                f"  **{ctx.author.display_name}**, the loa module is currently under maintenance. Please try again later.",
            )
            return
        if not await ModuleCheck(ctx.guild.id, "LOA"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "LOA Permissions"):
            return

        loas = await self.client.db["loa"].find_one(
            {
                "user": user.id,
                "guild_id": ctx.guild.id,
                "active": True,
                "request": {"$ne": True},
            }
        )
        loainactive = (
            await self.client.db["loa"]
            .find(
                {
                    "user": user.id,
                    "guild_id": ctx.guild.id,
                    "active": False,
                    "request": {"$ne": True},
                }
            )
            .to_list(length=None)
        )
        view = None

        if loas is None:
            description = ""
            for request in loainactive:
                start_time = request["start_time"]
                end_time = request["end_time"]
                reason = request["reason"]
                description += f"> <t:{int(start_time.timestamp())}:f> - <t:{int(end_time.timestamp())}:f> • {reason}\n"
                if len(description) > 1024:
                    description = description[:1021] + "..."
                    break

            embed = discord.Embed(
                title="Leave Of Absense",
                color=discord.Color.dark_embed(),
            )
            embed.set_thumbnail(url=user.display_avatar)
            embed.set_author(icon_url=user.display_avatar, name=user.display_name)
            view = LOACreate(user, ctx.guild, ctx.author)
            embed.add_field(
                name="<:LOA:1223063170856390806> Previous LOAs",
                value=description,
                inline=False,
            )

        else:
            start_time = loas["start_time"]
            end_time = loas["end_time"]
            reason = loas["reason"]

            embed = discord.Embed(
                title="Leave Of Absence",
                color=discord.Color.dark_embed(),
            )
            embed.set_thumbnail(url=user.display_avatar)
            embed.set_author(icon_url=user.display_avatar, name=user.display_name)
            embed.add_field(
                name="<:LOA:1223063170856390806> Current LOA",
                value=f"> **Start Date:** <t:{int(start_time.timestamp())}:f>\n> **End Date:** <t:{int(end_time.timestamp())}:f>\n> **Reason:** {reason}",
            )

            view = LOAPanel(user, ctx.guild, ctx.author)

        await ctx.send(embed=embed, view=view)

    @loa.command(description="View all Leave Of Absence")
    async def active(self, ctx: commands.Context):
        if self.client.loa_maintenance is True:
            await ctx.send(
                f"  **{ctx.author.display_name}**, the loa module is currently under maintenance. Please try again later.",
            )
            return
        if not await ModuleCheck(ctx.guild.id, "LOA"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return

        if not await has_admin_role(ctx, "LOA Permissions"):
            return

        current_time = datetime.now()
        filter = {
            "guild_id": ctx.guild.id,
            "end_time": {"$gte": current_time},
            "active": True,
            "request": {"$ne": True},
        }

        loa_requests = await self.client.db["loa"].find(filter).to_list(length=None)

        if len(loa_requests) == 0:
            await ctx.send(
                f"  **{ctx.author.display_name}**, there aren't any active LOAs in this server.",
            )
        else:
            embed = discord.Embed(title="Active LOAs", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=ctx.guild.icon)
            embed.set_author(icon_url=ctx.guild.icon, name=ctx.guild.name)
            for request in loa_requests:
                user = await self.client.fetch_user(request["user"])
                start_time = request["start_time"]
                end_time = request["end_time"]
                reason = request["reason"]

                embed.add_field(
                    name=f"{loa}{user.name.capitalize()}",
                    value=f"{arrow}**Start Date:** <t:{int(start_time.timestamp())}:f>\n{arrow}**End Date:** <t:{int(end_time.timestamp())}:f>\n{arrow}**Reason:** {reason}",
                    inline=False,
                )

            await ctx.send(embed=embed)

    @loa.command(description="Request a Leave Of Absence")
    @app_commands.describe(
        duration="How long do you want the LOA for? (m/h/d/w)",
        reason="What is the reason for this LOA?",
        start="When do you want this loa to start? (m/h/d/w)",
    )
    async def request(
        self,
        ctx: commands.Context,
        duration: discord.ext.commands.Range[str, 1, 20],
        *,
        reason: discord.ext.commands.Range[str, 1, 2000],
        start: str = None,
    ):
        await ctx.defer(ephemeral=True)

        if self.client.loa_maintenance is True:
            await ctx.send(
                f"  **{ctx.author.display_name}**, the loa module is currently under maintenance. Please try again later.",
            )
            return

        if not await ModuleCheck(ctx.guild.id, "LOA"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_staff_role(ctx, "LOA Permissions"):
            return
        if not re.match(r"^\d+[smhdw]$", duration):
            await ctx.send(
                f"  **{ctx.author.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.",
            )
            return
        LOA = await self.client.db["loa"].find_one(
            {"guild_id": ctx.guild.id, "user": ctx.author.id, "active": True}
        )
        if LOA:
            await ctx.send(
                f"  **{ctx.author.display_name}**, you already have an active LOA.",
            )
            return
        Config = await self.client.config.find_one({"_id": ctx.guild.id})
        if not Config:
            return await ctx.send(
                embed=BotNotConfigured(),
                view=Support(),
            )
        if not Config.get("LOA"):
            return await ctx.send(
                embed=ModuleNotSetup(),
                view=Support(),
            )
        if not Config.get("LOA", {}).get("channel"):
            return await ctx.send(
                embed=NoChannelSet(),
                view=Support(),
            )

        duration_value = int(duration[:-1])
        duration_unit = duration[-1]
        duration_seconds = duration_value

        if duration_unit == "m":
            duration_seconds *= 60
        elif duration_unit == "s":
            duration_seconds *= 1
        elif duration_unit == "h":
            duration_seconds *= 3600
        elif duration_unit == "d":
            duration_seconds *= 86400
        elif duration_unit == "w":
            duration_seconds *= 604800
        if start:
            if not re.match(r"^\d+[smhdw]$", start):
                await ctx.send(
                    f"  **{ctx.author.display_name}**, invalid start time format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.",
                )
                return

            start_value = int(start[:-1])
            start_unit = start[-1]
            start_time = datetime.now()

            if start_unit == "m":
                start_time += timedelta(minutes=start_value)
            elif start_unit == "s":
                start_time += timedelta(seconds=start_value)
            elif start_unit == "h":
                start_time += timedelta(hours=start_value)
            elif start_unit == "d":
                start_time += timedelta(days=start_value)
            elif start_unit == "w":
                start_time += timedelta(weeks=start_value)
        else:
            start_time = datetime.now()

        end_time = start_time + timedelta(seconds=duration_seconds)
        embed = discord.Embed(
            title="LOA Request - Pending",
            description=f"* **User:** {ctx.author.mention}\n* **Start Date**: <t:{int(start_time.timestamp())}:f>\n* **End Date:** <t:{int(end_time.timestamp())}:f>\n* **Reason:** {reason}",
            color=discord.Color.dark_embed(),
        )
        if start:
            embed.title = "(Scheduled) LOA Request - Pending"
        embed.set_author(
            icon_url=ctx.author.display_avatar, name=ctx.author.display_name
        )
        embed.set_thumbnail(url=ctx.author.display_avatar)
        past_loas = await self.client.db["loa"].count_documents(
            {
                "guild_id": ctx.guild.id,
                "user": ctx.author.id,
                "request": {"$ne": True},
                "active": False,
            }
        )
        view = Confirm()
        if past_loas == 0:
            view.loacount.disabled = True
        try:
            channel = await ctx.guild.fetch_channel(
                Config.get("LOA", {}).get("channel")
            )
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            return await ctx.send(
                embed=ChannelNotFound(),
                view=Support(),
            )
        if not channel:
            return await ctx.send(
                embed=ChannelNotFound(),
                view=Support(),
            )

        view.loacount.label = f"Past LOAs  |  {past_loas}"
        try:
            msg = await channel.send(embed=embed, view=view)
            loadata = {
                "guild_id": ctx.guild.id,
                "user": ctx.author.id,
                "start_time": start_time,
                "end_time": end_time,
                "reason": reason,
                "messageid": msg.id,
                "request": True,
                "active": False,
                "scheduled": True if start else False,
            }
            await self.client.db["loa"].insert_one(loadata)
            await ctx.send(f"  LOA Request sent", ephemeral=True)
            print(f"[LOA] LOA Request @{ctx.guild.name} pending")
        except discord.Forbidden:
            return await ctx.send(
                embed=NoPermissionChannel(channel),
                view=Support(),
            )


class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.green,
        custom_id="persistent_view:confirm",
        row=0,
        emoji="<:whitecheck:1223062421212631211>",
    )
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.client.loa_maintenance is True:
            await interaction.response.send_message(
                f"  **{interaction.user.display_name}**, the loa module is currently under maintenance. Please try again later.",
                ephemeral=True,
            )
            return

        if not await has_admin_role(interaction):
            return
        await interaction.response.defer()
        loa_data = await interaction.client.db["loa"].find_one(
            {"messageid": interaction.message.id}
        )
        if loa_data:
            try:
                self.user = await interaction.guild.fetch_member(loa_data["user"])
            except (discord.HTTPException, discord.NotFound):
                await interaction.followup.send(
                    content=f"  **{interaction.user.display_name}**, I can't find this user.",
                    ephemeral=True,
                )

                return

        else:
            await interaction.followup.send(
                content=f"  **{interaction.user.display_name}**, I can't find this LOA.",
                ephemeral=True,
            )
            return
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            await interaction.followup.send(
                embed=BotNotConfigured(),
                ephemeral=True,
                view=Support(),
            )
            return
        if not config.get("LOA"):
            await interaction.followup.send(
                embed=ModuleNotSetup(),
                ephemeral=True,
                view=Support(),
            )
            return
        user = self.user
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_green()
        embed.title = f"  LOA Request - Accepted"
        embed.set_footer(
            text=f"Accepted by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar,
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.client.db["loa"].update_one(
            {
                "guild_id": interaction.guild.id,
                "messageid": interaction.message.id,
                "user": user.id,
            },
            {"$set": {"active": True, "request": False}},
        )
        LOARole = config.get("LOA", {}).get("role")
        if loa_data.get("scheduled", False) is not True:
            if LOARole:
                try:
                    role = discord.utils.get(interaction.guild.roles, id=LOARole)
                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                    print(f"[LOA] Failed to get role {LOARole}. Continuing...")
                    pass
                if role:
                    try:
                        await user.add_roles(role)
                    except discord.Forbidden:
                        print(
                            f"[LOA] Failed to add role {LOARole} to user {user.id}. Continuing..."
                        )
                        pass

        loanotification = await interaction.client.db["consent"].find_one(
            {"user_id": self.user.id}
        )
        if loanotification and loanotification.get("LOAAlerts", "Enabled") == "Enabled":

            try:
                embed.remove_footer()
                embed.remove_author()
                await self.user.send(embed=embed)
            except discord.Forbidden:
                print(
                    f"[LOA] Failed to send a DM to user {self.user.id}. Continuing..."
                )
                pass

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.red,
        custom_id="persistent_view:cancel",
        row=0,
        emoji="<:whitex:1190819175447408681>",
    )
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if interaction.client.loa_maintenance is True:
            await interaction.response.send_message(
                f"  **{interaction.user.display_name}**, the loa module is currently under maintenance. Please try again later.",
                ephemeral=True,
            )
            return

        if not await has_admin_role(interaction):
            await interaction.followup.send(
                content=f"  **{interaction.user.display_name}**, you don't have permission to accept this LOA.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`",
                ephemeral=True,
            )
            return
        loa_data = await interaction.client.db["loa"].find_one(
            {"messageid": interaction.message.id}
        )
        if loa_data:
            try:
                self.user = await interaction.guild.fetch_member(loa_data["user"])
            except (discord.HTTPException, discord.NotFound):
                await interaction.followup.send(
                    content=f"  **{interaction.user.display_name}**, I can't find this user.",
                    ephemeral=True,
                )
                return
        else:

            await interaction.followup.send(
                content=f"  **{interaction.user.display_name}**, I can't find this LOA.",
                ephemeral=True,
            )
            return

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_red()
        embed.title = f"  LOA Request - Denied"
        embed.set_footer(
            text=f"Denied by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar,
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.client.db["loa"].delete_one(
            {
                "guild_id": interaction.guild.id,
                "user": self.user.id,
                "messageid": interaction.message.id,
            }
        )
        print(f"LOA Request @{interaction.guild.name} denied")
        loanotification = await interaction.client.db["consent"].find_one(
            {"user_id": self.user.id}
        )
        if loanotification and loanotification.get("LOAAlerts", "Enabled") == "Enabled":
            try:

                await self.user.send(
                    f"  **{self.user.display_name}**, your LOA **@{interaction.guild.name}** has been denied."
                )
            except discord.Forbidden:
                print(f"Failed to send a DM to user {self.user.id}. Continuing...")
                pass

    @discord.ui.button(
        label="Past LOAs | 0",
        style=discord.ButtonStyle.grey,
        custom_id="persistent_view:loacount",
        row=0,
        emoji="<:case:1214629776606887946>",
    )
    async def loacount(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        loa_data = await interaction.client.db["loa"].find_one(
            {"messageid": interaction.message.id}
        )
        if loa_data:

            try:
                self.user = await interaction.guild.fetch_member(loa_data["user"])
            except (discord.HTTPException, discord.NotFound):
                await interaction.response.send_message(
                    content=f"  **{interaction.user.display_name}**, I can't find this user.",
                    ephemeral=True,
                )
                return
        else:
            await interaction.response.send_message(
                content=f"  **{interaction.user.display_name}**, I can't find this LOA.",
                ephemeral=True,
            )
            return
        user = self.user
        loainactive = (
            await interaction.client.db["loa"]
            .find(
                {
                    "guild_id": interaction.guild.id,
                    "request": {"$ne": True},
                    "user": user.id,
                    "active": False,
                }
            )
            .sort("start_time", -1)
            .to_list(length=None)
        )
        description = []
        for request in loainactive:
            start_time = request["start_time"]
            end_time = request["end_time"]
            reason = request["reason"]
            description.append(
                f"<t:{int(start_time.timestamp())}:f> - <t:{int(end_time.timestamp())}:f> • {reason}"
            )
        embed = discord.Embed(
            title="Past LOAs",
            description="\n".join(description),
            color=discord.Color.dark_embed(),
        )
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class LOAPanel(discord.ui.View):
    def __init__(
        self, user: discord.Member, guild: discord.Guild, author: discord.User
    ):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(
        label="Void LOA",
        style=discord.ButtonStyle.grey,
        custom_id="persistent_view:cancel",
        emoji="<:Exterminate:1223063042246443078>",
    )
    async def End(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.user
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        loa = await interaction.client.db["loa"].find_one(
            {"user": self.user.id, "guild_id": interaction.guild.id, "active": True}
        )
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config:
            LOARole = config.get("LOA", {}).get("role")
            if LOARole:
                try:
                    role = discord.utils.get(interaction.guild.roles, id=LOARole)
                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                    print(f"Failed to get role {LOARole}. Continuing...")
                    pass
                if role:
                    try:
                        await user.remove_roles(role)
                    except discord.Forbidden:
                        print(
                            f"Failed to remove role {LOARole} from user {user.id}. Continuing..."
                        )
                        pass

        await interaction.client.db["loa"].update_many(
            {"guild_id": interaction.guild.id, "user": user.id},
            {"$set": {"active": False}},
        )
        await interaction.response.edit_message(
            embed=None,
            content=f"  Succesfully ended **@{user.display_name}'s** LOA",
            view=None,
        )
        try:
            loanotification = await interaction.client.db["consent"].find_one(
                {"user_id": self.user.id}
            )
            if (
                loanotification
                and loanotification.get("LOAAlerts", "Enabled") == "Enabled"
            ):
                await user.send(
                    f"<:bin:1235001855721865347> Your LOA **@{self.guild.name}** has been voided."
                )
        except discord.Forbidden:
            print("Failed to send a DM to user. Continuing... (LOA Manage)")
            return

    @discord.ui.button(label="Extend", style=discord.ButtonStyle.blurple)
    async def extend(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.user
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.send_modal(ExtendLOA(user, self.guild, author))


class ExtendLOA(discord.ui.Modal):
    def __init__(self, user, guild, author):
        super().__init__(title="Extend LOA")
        self.user = user
        self.guild = guild
        self.author = author
        self.add_item(
            discord.ui.TextInput(
                label="Duration",
                placeholder="1d (1 day), 2h (2 hours), etc.",
                style=discord.TextStyle.short,
                required=True,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user.id != self.author:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        duration = self.children[0].value
        if not re.match(r"^\d+[smhdw]$", duration):
            await interaction.followup.send(
                f"  **{interaction.user.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.",
            )
            return

        duration_value = int(duration[:-1])
        duration_unit = duration[-1]
        duration_seconds = duration_value

        if duration_unit == "m":
            duration_seconds *= 60
        elif duration_unit == "s":
            duration_seconds *= 1
        elif duration_unit == "h":
            duration_seconds *= 3600
        elif duration_unit == "d":
            duration_seconds *= 86400
        elif duration_unit == "w":
            duration_seconds *= 604800
        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            await interaction.followup.send(
                f"  **{interaction.user.display_name},** the bot isn't set up. Run `/config` to get started.",
                ephemeral=True,
            )
            return
        if not config.get("LOA"):
            await interaction.followup.send(
                f"  **{interaction.user.display_name},** the LOA module isnt setup. Run `/config` to get started.",
                ephemeral=True,
            )
            return

        loa = await interaction.client.db["loa"].find_one(
            {"user": self.user.id, "guild_id": interaction.guild.id, "active": True}
        )
        if not loa:
            await interaction.followup.send(
                f"  **{interaction.user.display_name}**, this user doesn't have an active LOA.",
            )
            return
        end_time = loa["end_time"] + timedelta(seconds=duration_seconds)
        await interaction.client.db["loa"].update_one(
            {
                "user": self.user.id,
                "guild_id": interaction.guild.id,
                "active": True,
            },
            {"$set": {"end_time": end_time}},
        )
        await interaction.edit_original_response(
            content=f"  Succesfully extended **@{self.user.display_name}'s** LOA",
            embed=None,
            view=None,
        )
        try:
            embed = discord.Embed(
                title="LOA Extended",
                description=f"* **User:** {self.user.mention}\n* **Start Date**: <t:{int(loa.get('start_time').timestamp())}:f>\n* **End Date:** <t:{int(end_time.timestamp())}:f>\n* **Reason:** {loa.get('reason', 'N/A')}",
                color=discord.Color.dark_embed(),
            )
            embed.set_author(
                icon_url=self.user.display_avatar, name=self.user.display_name
            )
            embed.set_thumbnail(url=self.user.display_avatar)
            loanotification = await interaction.client.db["consent"].find_one(
                {"user_id": self.user.id}
            )
            if (
                loanotification
                and loanotification.get("LOAAlerts", "Enabled") == "Enabled"
            ):
                await self.user.send(
                    f"<:suspensions:1234998406938755122> Your LOA **@{self.guild.name}** has been extended.",
                    embed=embed,
                )
        except discord.Forbidden:
            print("Failed to send a DM to user. Continuing... (LOA Manage)")
            return
        try:
            channel = await interaction.guild.fetch_channel(
                config.get("LOA", {}).get("channel")
            )
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            f"  **{interaction.user.display_name},** I can't find where the LOA channel is maybe you should fix that."
            return
        if not channel:
            return await interaction.followup.send(
                f"  **{interaction.user.display_name},** I can't find where the LOA channel is maybe you should fix that."
            )
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            return await interaction.followup.send(
                f"  **{interaction.user.display_name},** I don't have permission to send messages in that channel."
            )


class LOACreate(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=360)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(
        label="Create Leave Of Absence",
        style=discord.ButtonStyle.grey,
        custom_id="persistent_view:cancel",
        emoji="<:Add:1163095623600447558>",
    )
    async def CreateLOA(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_modal(LOA(self.user, self.guild, self.author))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(loamodule(client))
