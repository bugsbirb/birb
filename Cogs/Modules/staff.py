import discord
from discord import app_commands
from discord.ext import commands
import discord.http
import pymongo
from utils.emojis import *
import os
import string
from typing import Literal
import random
from utils.format import IsSeperateBot, PaginatorButtons

from utils.Module import ModuleCheck
from datetime import datetime
import re


from utils.permissions import has_admin_role, has_staff_role
from utils.Module import ModuleCheck
from utils.format import ordinal
from utils.permissions import check_admin_and_staff


environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")


from utils.HelpEmbeds import BotNotConfigured, ModuleNotEnabled, Support, ModuleNotSetup


class SetMessages(discord.ui.Modal, title="Set Message Count"):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    message_count = discord.ui.TextInput(
        label="Message Count",
        placeholder="Set the message count for this user",
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            message_count_value = int(self.message_count.value)
        except ValueError:
            await interaction.response.send_message(
                f"  Invalid input. Please enter a valid number for the message count.",
                ephemeral=True,
            )
            return

        guild_id = interaction.guild.id

        filter = {"guild_id": guild_id, "user_id": self.user_id}
        update_data = {"$set": {"message_count": message_count_value}}
        await interaction.client.qdb["messages"].update_one(
            filter, update_data, upsert=True
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name}**, I've set the users messages as `{message_count_value}`.",
            embed=None,
            view=None,
        )


class AddMessage(discord.ui.Modal, title="Add Messages"):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    message_count = discord.ui.TextInput(
        label="Added Message Count",
        placeholder="Will add onto their current message count",
    )

    async def on_submit(self, interaction: discord.Interaction):
        result = await interaction.client.qdb["messages"].find_one(
            {"guild_id": interaction.guild.id, "user_id": self.user_id}
        )
        message_count_value = int(self.message_count.value)
        guild_id = interaction.guild.id
        if result:
            message_count = int(result["message_count"]) + message_count_value
            filter = {"guild_id": guild_id, "user_id": self.user_id}
            await interaction.client.qdb["messages"].update_one(
                filter, {"$set": {"message_count": message_count}}
            )
            await interaction.response.edit_message(
                content=f"  **{interaction.user.display_name}**, I have added `{message_count_value}` messages to the staff member.",
                embed=None,
                view=None,
            )
        else:
            message_count = message_count_value
            await interaction.client.qdb["messages"].insert_one(
                {
                    "guild_id": guild_id,
                    "user_id": self.user_id,
                    "message_count": message_count,
                }
            )


class RemovedMessage(discord.ui.Modal, title="Remove Messages"):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    message_count = discord.ui.TextInput(
        label="Removed Message Count",
        placeholder="Will remove from their current message count",
    )

    async def on_submit(self, interaction: discord.Interaction):
        result = await interaction.client.qdb["messages"].find_one(
            {"guild_id": interaction.guild.id, "user_id": self.user_id}
        )
        message_count_value = int(self.message_count.value)
        guild_id = interaction.guild.id
        if result:
            message_count = int(result["message_count"]) - message_count_value
            filter = {"guild_id": guild_id, "user_id": self.user_id}
            await interaction.client.qdb["messages"].update_one(
                filter, {"$set": {"message_count": message_count}}
            )
            await interaction.response.edit_message(
                content=f"  **{interaction.user.display_name}**, I have added `{message_count_value}` messages to the staff member.",
                embed=None,
                view=None,
            )
        else:
            message_count = message_count_value
            await interaction.client.qdb["messages"].insert_one(
                {"guild_id": guild_id, "user_id": self.user_id, "message_count": 0}
            )


class StaffManage(discord.ui.View):
    def __init__(self, staff_id, author):
        super().__init__(timeout=360)
        self.value = None
        self.staff_id = staff_id
        self.author = author

    @discord.ui.button(
        label="Add Messages",
        style=discord.ButtonStyle.green,
        emoji="<:Add:1163095623600447558>",
        row=1,
    )
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_modal(AddMessage(self.staff_id))

    @discord.ui.button(
        label="Subtract Messages",
        style=discord.ButtonStyle.red,
        emoji="<:Subtract:1229040262161109003>",
        row=1,
    )
    async def subtract(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_modal(RemovedMessage(self.staff_id))

    @discord.ui.button(
        label="Set Messages",
        style=discord.ButtonStyle.blurple,
        row=2,
        emoji="<:Pen:1235001839036923996>",
    )
    async def set(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_modal(SetMessages(self.staff_id))

    @discord.ui.button(
        label="Reset Messages",
        style=discord.ButtonStyle.red,
        row=2,
        emoji="<:bin:1235001855721865347>",
    )
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_id = self.staff_id
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        filter = {"guild_id": interaction.guild.id, "user_id": staff_id}
        update = {"$set": {"message_count": 0}}
        await interaction.client.qdb["messages"].update_one(filter, update)

        await interaction.response.edit_message(
            content=f"**  {interaction.user.display_name}**, I have reset the staff member's ",
            embed=None,
            view=None,
        )


class quota(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_group(name="staff")
    async def staff(self, ctx: commands.Context):
        return

    @commands.hybrid_group(name="quota")
    async def quota(self, ctx: commands.Context):
        return

    @staff.group(name="list")
    async def list(self, ctx: commands.Context):
        pass

    @list.command(description="Add a rank to the staff list")
    async def add(self, ctx: commands.Context, rank: discord.Role, position: int):
        if not await ModuleCheck(ctx.guild.id, "Staff List"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Staff List Permissions"):
            return
        await self.client.db["Staff List"].update_one(
            {"guild_id": ctx.guild.id, "position": position},
            {"$set": {"rank": rank.id}},
            upsert=True,
        )
        await ctx.send(
            f"  **{ctx.author.display_name}**, I have added `@{rank.name}` to the staff list.",
        )

    @list.command(description="Remove a rank from the staff list")
    async def remove(self, ctx: commands.Context, rank: discord.Role):
        if not await ModuleCheck(ctx.guild.id, "Staff List"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Staff List Permissions"):
            return
        await self.client.db["Staff List"].delete_one({"rank": rank.id})
        await ctx.send(
            f"  **{ctx.author.display_name}**, I have removed `@{rank.name}` from the staff list.",
        )

    @list.command(description="Send the staff list")
    async def send(self, ctx: commands.Context):
        if not await ModuleCheck(ctx.guild.id, "Staff List"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Staff List Permissions"):
            return

        results = (
            await self.client.db["Staff List"]
            .find({"guild_id": ctx.guild.id})
            .to_list(length=None)
        )
        if len(results) == 0 or not results:
            return await ctx.send(
                f"  **{ctx.author.display_name}**, there are no ranks in the staff list.\n{replybottom} You can add a rank using `/staff list add <rank> <position>`."
            )
        results = sorted(results, key=lambda x: int(x.get("position", 0)))
        member_roles = {}
        highest_role_seen = {}
        if not ctx.guild.chunked:
            await ctx.guild.chunk()

        for member in ctx.guild.members:
            highest_role = max(
                (
                    role
                    for role in member.roles
                    if any(role.id == result["rank"] for result in results)
                ),
                key=lambda role: role.position,
                default=None,
            )
            member_roles[member] = highest_role
            highest_role_seen[member] = highest_role

        embed = discord.Embed(
            title="Staff Team",
            color=discord.Color.dark_embed(),
            timestamp=datetime.now(),
        )
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        embed.set_footer(text="Last Updated")

        description = ""
        for result in results:
            role = ctx.guild.get_role(result.get("rank"))
            if role is not None:
                members = [
                    member.mention
                    for member in member_roles
                    if member_roles[member] == role
                    and highest_role_seen[member] == role
                ]
                if members:
                    description += (
                        f"### **{role.mention}** ({len(members)})\n\n> "
                        + "\n> ".join(members)
                        + "\n"
                    )
        embed.description = description
        if ctx.interaction:
            msg = await ctx.channel.send(
                embed=embed, allowed_mentions=discord.AllowedMentions().none()
            )
            await ctx.send(f"  successfully sent the staff list.", ephemeral=True)
        else:
            await ctx.message.delete()
            msg = await ctx.send(
                embed=embed, allowed_mentions=discord.AllowedMentions().none()
            )

        await self.client.db["Active Staff List"].update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {"msg": msg.id, "channel_id": ctx.channel.id}},
            upsert=True,
        )

    def GetPlace(self, data, user):
        data = sorted(
            data,
            key=lambda x: int(x.get("message_count", 0))
            + int(x.get("ClaimedTickets", 0)),
            reverse=True,
        )
        for i, user_data in enumerate(data):
            if (
                user_data.get("user_id") == user.id
                or user_data.get("UserID") == user.id
            ):
                return i + 1
        return None

    @quota.group(name="activity")
    async def activity(self, ctx: commands.Context):
        pass

    def FuckOff(self, value):
        try:
            return int(value)
        except ValueError:
            return 0

    @activity.command(name="wave", description="Punish people failing the quota.")
    async def wave(self, ctx: commands.Context):
        if not await ModuleCheck(ctx.guild.id, "Quota") and not await ModuleCheck(
            ctx.guild.id, "Tickets"
        ):
            await ctx.send(embed=ModuleNotEnabled(), view=Support())
            return
        if not await ModuleCheck(ctx.guild.id, "infractions"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Message Quota Permissions"):
            return

        passed, failed, on_loa, failedmembers = [], [], [], []
        Config = await self.client.config.find_one({"_id": ctx.guild.id})
        if not Config:
            await ctx.send(embed=BotNotConfigured(), view=Support())
            return

        if not Config.get("Message Quota") and not Config.get("Tickets"):
            await ctx.send(embed=ModuleNotSetup(), view=Support())
            return
        if Config.get("Infraction", None) is None:
            return await ctx.send(embed=ModuleNotSetup(), view=Support())

        await ctx.defer()

        if IsSeperateBot():
            msg = await ctx.send(
                embed=discord.Embed(
                    description="Loading...", color=discord.Color.dark_embed()
                )
            )

        else:
            msg = await ctx.send(
                embed=discord.Embed(
                    description="<a:astroloading:1245681595546079285>",
                    color=discord.Color.dark_embed(),
                )
            )
        message_users = []
        ticket_users = []
        if Config.get("Message Quota"):
            message_users = (
                await self.client.qdb["messages"]
                .find({"guild_id": ctx.guild.id})
                .sort("message_count", pymongo.DESCENDING)
                .to_list(length=750)
            )
        if Config.get("Tickets"):
            ticket_users = (
                await self.client.db["Ticket Quota"]
                .find({"GuildID": ctx.guild.id})
                .sort("ClaimedTickets", pymongo.DESCENDING)
                .to_list(length=750)
            )
        Users = {}
        for user in message_users + ticket_users:
            user_id = user.get("user_id") or user.get("UserID")
            if user_id not in Users:
                Users[user_id] = user
            else:
                Users[user_id]["message_count"] = int(
                    Users[user_id].get("message_count", 0)
                ) + int(user.get("message_count", 0))
                Users[user_id]["ClaimedTickets"] = int(
                    Users[user_id].get("ClaimedTickets", 0)
                ) + int(user.get("ClaimedTickets", 0))

        Users = sorted(
            Users.values(),
            key=lambda x: (
                int(x.get("message_count", 0)) + int(x.get("ClaimedTickets", 0))
            ),
            reverse=True,
        )

        quota = int(Config.get("Message Quota", {}).get("quota", 0))
        TicketQuota = int(Config.get("Tickets", {}).get("quota", 0))
        loa_role_id = Config.get("LOA", {}).get("role")

        for user in Users:
            member = ctx.guild.get_member(user.get("user_id") or user.get("UserID"))
            if not member:
                try:
                    member = await ctx.guild.fetch_member(
                        user.get("user_id") or user.get("UserID")
                    )
                except (discord.HTTPException, discord.NotFound):
                    continue
            if not member or not await check_admin_and_staff(ctx.guild, member):
                continue

            MessageCount = user.get("message_count", 0)
            TicketCount = user.get("ClaimedTickets", 0)
            Messages = f"• `{MessageCount}` messages" if MessageCount else ""
            Tickets = f"• `{TicketCount}` tickets" if TicketCount else ""

            entry = f"> **{member.name}** {Messages} {Tickets}".strip()

            if loa_role_id and any(role.id == loa_role_id for role in member.roles):
                on_loa.append(entry)
            elif (TicketCount >= TicketQuota if TicketQuota else True) and (
                MessageCount >= quota if quota else True
            ):
                passed.append(entry)
            else:
                failed.append(entry)
                failedmembers.append(member)

        passed.sort(
            key=lambda x: self.FuckOff(
                re.search(r"\d+", x.split("•")[-1].strip()).group()
            ),
            reverse=True,
        )
        failed.sort(
            key=lambda x: self.FuckOff(
                x.split("•")[-1].strip().split(" ")[0].strip("`")
            ),
            reverse=True,
        )

        failedembed = discord.Embed(title="", color=discord.Color.dark_embed())
        failedembed.set_author(name="Failed Users")
        failedembed.set_footer(text="Select the infraction type to infract with.")
        failedembed.set_image(url="https://www.astrobirb.dev/invisble.png")
        if failed:
            failedembed.description = "\n".join(failed)
        else:
            failedembed.description = "> No users failed the quota."
        view = discord.ui.View()
        Types = Config.get("Infraction", {}).get("types", [])

        if not Types or len(Types) == 0:
            from utils.format import DefaultTypes

            Types = DefaultTypes()

        options = [
            discord.SelectOption(label=name[:80], value=name[:80]) for name in Types
        ]
        view.add_item(InfractionTypeSelection(ctx.author, options, failedmembers))

        await msg.edit(embeds=[failedembed], view=view)

    @activity.command(name="view", description="View the activity results.")
    async def view(self, ctx: commands.Context):
        if not await ModuleCheck(ctx.guild.id, "Quota") and not await ModuleCheck(
            ctx.guild.id, "Tickets"
        ):
            await ctx.send(embed=ModuleNotEnabled(), view=Support())
            return

        if not await has_admin_role(ctx, "Message Quota Permissions"):
            return

        passed, failed, on_loa = [], [], []
        Config = await self.client.config.find_one({"_id": ctx.guild.id})
        if not Config:
            await ctx.send(embed=BotNotConfigured(), view=Support())
            return

        if not Config.get("Message Quota") and not Config.get("Tickets"):
            await ctx.send(embed=ModuleNotEnabled(), view=Support())
            return
        await ctx.defer()

        if IsSeperateBot():
            msg = await ctx.send(
                embed=discord.Embed(
                    description="Loading...", color=discord.Color.dark_embed()
                )
            )

        else:
            msg = await ctx.send(
                embed=discord.Embed(
                    description="<a:astroloading:1245681595546079285>",
                    color=discord.Color.dark_embed(),
                )
            )
        message_users = []
        ticket_users = []
        if Config.get("Message Quota"):
            message_users = (
                await self.client.qdb["messages"]
                .find({"guild_id": ctx.guild.id})
                .sort("message_count", pymongo.DESCENDING)
                .to_list(length=750)
            )
        if Config.get("Tickets"):
            ticket_users = (
                await self.client.db["Ticket Quota"]
                .find({"GuildID": ctx.guild.id})
                .sort("ClaimedTickets", pymongo.DESCENDING)
                .to_list(length=750)
            )
        Users = {}
        for user in message_users + ticket_users:
            user_id = user.get("user_id") or user.get("UserID")
            if user_id not in Users:
                Users[user_id] = user
            else:
                Users[user_id]["message_count"] = Users[user_id].get(
                    "message_count", 0
                ) + user.get("message_count", 0)
                Users[user_id]["ClaimedTickets"] = Users[user_id].get(
                    "ClaimedTickets", 0
                ) + user.get("ClaimedTickets", 0)

        Users = sorted(
            Users.values(),
            key=lambda x: int(
                (x.get("message_count", 0)) + int(x.get("ClaimedTickets", 0))
            ),
            reverse=True,
        )

        quota = int(Config.get("Message Quota", {}).get("quota", 0))
        TicketQuota = int(Config.get("Tickets", {}).get("quota", 0))
        loa_role_id = Config.get("LOA", {}).get("role")

        for user in Users:
            member = ctx.guild.get_member(user.get("user_id") or user.get("UserID"))
            if not member:
                try:
                    member = await ctx.guild.fetch_member(
                        user.get("user_id") or user.get("UserID")
                    )
                except (discord.HTTPException, discord.NotFound):
                    continue
            if not member or not await check_admin_and_staff(ctx.guild, member):
                continue

            MessageCount = user.get("message_count", 0)
            TicketCount = user.get("ClaimedTickets", 0)
            Messages = f"• `{MessageCount}` messages" if MessageCount else ""
            Tickets = f"• `{TicketCount}` tickets" if TicketCount else ""

            entry = f"> **{member.name}** {Messages} {Tickets}".strip()

            if loa_role_id and any(role.id == loa_role_id for role in member.roles):
                on_loa.append(entry)
            elif (TicketCount >= TicketQuota if TicketQuota else True) and (
                MessageCount >= quota if quota else True
            ):
                passed.append(entry)
            else:
                failed.append(entry)

        passed.sort(
            key=lambda x: self.FuckOff(
                x.split("•")[-1].strip().split(" ")[0].strip("`")
            ),
            reverse=True,
        )
        failed.sort(
            key=lambda x: self.FuckOff(
                x.split("•")[-1].strip().split(" ")[0].strip("`")
            ),
            reverse=True,
        )
        on_loa.sort(
            key=lambda x: self.FuckOff(
                x.split("•")[-1].strip().split(" ")[0].strip("`")
            ),
            reverse=True,
        )
        passedembed = discord.Embed(title="Passed", color=discord.Color.brand_green())
        passedembed.set_image(url="https://www.astrobirb.dev/invisble.png")
        if passed:
            passedembed.description = "\n".join(passed)
        else:
            passedembed.description = "> No users passed the quota."

        loaembed = discord.Embed(title="On LOA", color=discord.Color.purple())
        loaembed.set_image(url="https://www.astrobirb.dev/invisble.png")
        if on_loa:
            loaembed.description = "\n".join(on_loa)
        else:
            loaembed.description = "> No users on LOA."

        failedembed = discord.Embed(title="Failed", color=discord.Color.brand_red())
        failedembed.set_image(url="https://www.astrobirb.dev/invisble.png")
        if failed:
            failedembed.description = "\n".join(failed)
        else:
            failedembed.description = "> No users failed the quota."

        await msg.edit(embeds=[passedembed, loaembed, failedembed])

    @quota.command(name="manage", description="Manage a staffs messages count.")
    async def manage(self, ctx: commands.Context, staff: discord.Member):
        await ctx.defer()

        if not await ModuleCheck(ctx.guild.id, "Quota"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Message Quota Permissions"):
            return
        MessageData = await self.client.qdb["messages"].find_one(
            {"guild_id": ctx.guild.id, "user_id": staff.id}
        )

        Config = await self.client.config.find_one({"_id": ctx.guild.id})
        if Config is None:

            return await ctx.send(embed=BotNotConfigured(), view=Support())
        if not Config.get("Message Quota"):
            return await ctx.send(embed=ModuleNotEnabled(), view=Support())
        YourEmoji = None
        view = StaffManage(staff.id, ctx.author)
        YouPlace = None
        if MessageData:
            Quota = Config.get("Message Quota", {}).get("quota", 0)
            OnLOA = False
            if Config.get("LOA", {}).get("role"):
                OnLOA = any(
                    role.id == Config.get("LOA", {}).get("role") for role in staff.roles
                )
            YourEmoji = (
                "`LOA`"
                if OnLOA
                else (
                    (
                        "Met"
                        if IsSeperateBot()
                        else "<:status_green:1227365520857104405>"
                    )
                    if MessageData.get("message_count") >= Quota
                    else (
                        "Not Met"
                        if IsSeperateBot()
                        else "<:status_red:1227365495376711700>"
                    )
                )
            )
            users = (
                await self.client.qdb["messages"]
                .find({"guild_id": ctx.guild.id})
                .sort("message_count", pymongo.DESCENDING)
                .to_list(length=None)
            )
            YouPlace = self.GetPlace(users, staff)

        embed = discord.Embed(
            title=f"",
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="<:tablerprogressbolt:1330500442551091210> Manage Messages",
            value=f"> **Messages:** {MessageData.get('message_count', 0) if MessageData else 0} messages\n> **Passed:** {YourEmoji if YourEmoji else 'N/A'}\n> **Place:** {ordinal(YouPlace) if MessageData else 'N/A' if YouPlace else 'N/A'}",
        )
        embed.set_author(name=f"@{staff.name}", icon_url=staff.display_avatar)
        embed.set_thumbnail(url=staff.display_avatar)
        await ctx.send(embed=embed, view=view)

    @quota.command(
        name="messages",
        description="Display the amount the message count of a staff member.",
    )
    async def messages(self, ctx: commands.Context, staff: discord.Member):

        if not await ModuleCheck(ctx.guild.id, "Quota"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_staff_role(ctx, "Message Quota Permissions"):
            return
        await ctx.defer()
        MessageData = await self.client.qdb["messages"].find_one(
            {"guild_id": ctx.guild.id, "user_id": staff.id}
        )
        if not MessageData:
            return await ctx.send(
                f"  **{ctx.author.display_name}**, they haven't sent any messages."
            )
        Config = await self.client.config.find_one({"_id": ctx.guild.id})
        if Config is None:
            return await ctx.send(embed=BotNotConfigured(), view=Support())
        if not Config.get("Message Quota"):
            return await ctx.send(embed=ModuleNotEnabled(), view=Support())
        Quota = Config.get("Message Quota", {}).get("quota", 0)
        YourEmoji = None
        YouPlace = None
        OnLOA = False
        if Config.get("LOA", {}).get("role"):
            OnLOA = any(
                role.id == Config.get("LOA", {}).get("role") for role in staff.roles
            )
        if MessageData:
            YourEmoji = (
                "`LOA`"
                if OnLOA
                else (
                    (
                        "Met"
                        if environment == "custom"
                        else "<:status_green:1227365520857104405>"
                    )
                    if MessageData.get("message_count") >= Quota
                    else (
                        "Not Met"
                        if environment == "custom"
                        else "<:status_red:1227365495376711700>"
                    )
                )
            )

            if MessageData:
                users = (
                    await self.client.qdb["messages"]
                    .find({"guild_id": ctx.guild.id})
                    .sort("message_count", pymongo.DESCENDING)
                    .to_list(length=None)
                )
                YouPlace = self.GetPlace(users, staff)

        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(
            name=f"@{staff.name.capitalize()}",
            icon_url=staff.display_avatar,
        )
        embed.add_field(
            name="<:tablerprogressbolt:1330500442551091210> Progress",
            value=f"> **Messages:** {MessageData.get('message_count')} messages\n> **Passed:** {YourEmoji if YourEmoji else 'N/A'}\n> **Place:** {ordinal(YouPlace) if YouPlace else 'N/A'}",
        )
        await ctx.send(embed=embed)

    @quota.command(description="Export the staff leaderboard to CSV.")
    async def export(self, ctx: commands.Context):
        if not await ModuleCheck(ctx.guild.id, "Quota"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Message Quota Permissions"):
            return
        await ctx.defer(ephemeral=True)
        msg = await ctx.send("<a:Loading:1167074303905386587> Exporting to CSV...")
        users = (
            await self.client.qdb["messages"]
            .find({"guild_id": ctx.guild.id})
            .sort("message_count", pymongo.DESCENDING)
            .to_list(length=None)
        )
        Config = await self.client.config.find_one({"_id": ctx.guild.id})
        if Config is None:
            return await ctx.send(embed=BotNotConfigured(), view=Support())
        if not Config.get("Message Quota"):
            return await ctx.send(embed=ModuleNotEnabled(), view=Support())
        Quota = Config.get("Message Quota", {}).get("quota", 0)

        if not users:
            return await ctx.send(
                f"  **{ctx.author.display_name}**, there are no users in the leaderboard."
            )

        CSV = "User,Messages"
        if Quota:
            CSV += ",Passed"

        for user in users:
            member = ctx.guild.get_member(user.get("user_id"))
            if not member:
                try:
                    member = await ctx.guild.fetch_member(user.get("user_id"))
                except (discord.NotFound, discord.HTTPException):
                    continue

            if member and await check_admin_and_staff(ctx.guild, member):
                passed = (
                    "True"
                    if user.get("message_count") >= Quota
                    else "False" if Quota else ""
                )
                CSV += f"\n{member.name},{user.get('message_count')},{passed}"

        filename = f"staff_leaderboard_{ctx.guild.id}.csv"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(CSV)
        await msg.edit(
            attachments=[discord.File(filename)],
            content=f"  **{ctx.author.display_name}**, here's your CSV file.",
        )
        os.remove(filename)

    @staff.command(
        description="View the staff message leaderboard to see if anyone has passed their quota"
    )
    async def leaderboard(self, ctx: commands.Context):
        if not await ModuleCheck(ctx.guild.id, "Quota") and not await ModuleCheck(
            ctx.guild.id, "Tickets"
        ):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return

        await ctx.defer()
        if IsSeperateBot():
            msg = await ctx.send(
                embed=discord.Embed(
                    description="Loading...", color=discord.Color.dark_embed()
                )
            )

        else:
            msg = await ctx.send(
                embed=discord.Embed(
                    description="<a:astroloading:1245681595546079285>",
                    color=discord.Color.dark_embed(),
                )
            )

        if not await has_staff_role(ctx, "Message Quota Permissions"):
            return
        Config = await self.client.config.find_one({"_id": ctx.guild.id})
        if Config is None:
            return await msg.edit(embed=BotNotConfigured(), view=Support())
        if not Config.get("Message Quota") and not Config.get("Tickets"):
            return await msg.edit(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
        message_users = []
        ticket_users = []
        if Config.get("Message Quota"):
            message_users = (
                await self.client.qdb["messages"]
                .find({"guild_id": ctx.guild.id})
                .sort("message_count", pymongo.DESCENDING)
                .to_list(length=750)
            )
        if Config.get("Tickets"):
            ticket_users = (
                await self.client.db["Ticket Quota"]
                .find({"GuildID": ctx.guild.id})
                .sort("ClaimedTickets", pymongo.DESCENDING)
                .to_list(length=750)
            )
        Users = {}
        for user in message_users + ticket_users:
            user_id = user.get("user_id") or user.get("UserID")
            if user_id not in Users:
                Users[user_id] = user
            else:
                Users[user_id]["message_count"] = Users[user_id].get(
                    "message_count", 0
                ) + user.get("message_count", 0)
                Users[user_id]["ClaimedTickets"] = Users[user_id].get(
                    "ClaimedTickets", 0
                ) + user.get("ClaimedTickets", 0)

        Users = sorted(
            Users.values(),
            key=lambda x: (x.get("message_count", 0) + x.get("ClaimedTickets", 0)),
            reverse=True,
        )

        if len(Users) == 0:
            return await msg.edit(
                content=f"  **{ctx.author.display_name},** there hasn't been any {'messages' if message_users else 'tickets'} sent yet.",
                embed=None,
            )
        YouProgress = next(
            (
                user
                for user in Users
                if user.get("user_id") == ctx.author.id
                or user.get("UserID") == ctx.author.id
            ),
            {},
        )
        YourPlace = self.GetPlace(Users, ctx.author)
        YourMessages = YouProgress.get("message_count") if YouProgress else 0
        YourLOA = any(
            role.id == Config.get("LOA", {}).get("role") for role in ctx.author.roles
        )
        YourMessages = YouProgress.get("message_count", 0) if YouProgress else 0
        YourTickets = YouProgress.get("ClaimedTickets", 0) if YouProgress else 0
        YourEmoji = (
            "`LOA`"
            if YourLOA
            else (
                (
                    "Met"
                    if environment == "custom"
                    else "<:status_green:1227365520857104405>"
                )
                if YourMessages >= int(Config.get("Message Quota", {}).get("quota", 0))
                or (
                    YourTickets >= int(Config.get("Tickets", {}).get("quota", 0))
                    and int(Config.get("Tickets", {}).get("quota", 0)) != 0
                )
                else (
                    "Not Met"
                    if environment == "custom"
                    else "<:status_red:1227365495376711700>"
                )
            )
        )

        if Users is None:
            return await msg.edit(
                content=f"  **{ctx.author.display_name},** there has been no messages sent yet."
            )
        Description = ""
        i = 1
        pages = []

        for staff in Users:
            OnLOA = False
            member = ctx.guild.get_member(staff.get("user_id") or staff.get("UserID"))
            if not member:
                try:
                    member = await ctx.guild.fetch_member(
                        staff.get("user_id") or staff.get("UserID")
                    )
                except (discord.HTTPException, discord.NotFound):
                    continue
            if not member or not await check_admin_and_staff(ctx.guild, member):
                continue

            if Config.get("LOA", {}).get("role"):
                OnLOA = any(
                    role.id == Config.get("LOA", {}).get("role")
                    for role in member.roles
                )

            emoji = (
                "`LOA`"
                if OnLOA
                else (
                    (
                        "Met"
                        if environment == "custom"
                        else "<:status_green:1227365520857104405>"
                    )
                    if (
                        int(staff.get("message_count", 0))
                        >= int(Config.get("Message Quota", {}).get("quota", 0))
                        and Config.get("Message Quota", {}).get("quota", 0) != 0
                    )
                    or (
                        int(staff.get("ClaimedTickets", 0))
                        >= int(Config.get("Tickets", {}).get("quota", 0))
                        and Config.get("Tickets", {}).get("quota", 0) != 0
                    )
                    else (
                        "Not Met"
                        if environment == "custom"
                        else "<:status_red:1227365495376711700>"
                    )
                )
            )
            if (
                staff.get("message_count") is not None
                and staff.get("ClaimedTickets") is not None
            ):
                Description += f"* `{i}` {member.display_name} • {staff.get('message_count', 0)} messages • {staff.get('ClaimedTickets', 0)} tickets\n"
            elif staff.get("message_count") is not None:
                Description += f"* `{i}` {member.display_name} • {staff.get('message_count', 0)} messages\n"
            elif staff.get("ClaimedTickets") is not None:
                Description += f"* `{i}` {member.display_name} • {staff.get('ClaimedTickets', 0)} tickets\n"

            if (
                Config.get("Message Quota", {}).get("quota", 0) != 0
                or Config.get("Tickets", {}).get("quota", 0) != 0
            ):
                Description += f"{replybottom} **Status:** {emoji}\n\n"


            if i % 9 == 0:
                embed = discord.Embed(
                    title="Staff Leaderboard",
                    description=Description,
                    color=discord.Color.dark_embed(),
                )
                embed.set_thumbnail(url=ctx.guild.icon)
                embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
                pages.append(embed)
                Description = ""

            i += 1
        if Description.strip():
            embed = discord.Embed(
                title="Staff Leaderboard",
                description=Description,
                color=discord.Color.dark_embed(),
            )
            embed.set_thumbnail(url=ctx.guild.icon)
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            pages.append(embed)

        if YouProgress:
            for embed in pages:
                embed.add_field(
                    name="<:tablerprogressbolt:1330500442551091210> Your Progress",
                    value=(
                        f"> **Messages:** {YouProgress.get('message_count')} messages\n"
                        if YouProgress.get("message_count")
                        else ""
                    )
                    + (
                        f"> **Tickets:** {YouProgress.get('ClaimedTickets')} tickets\n"
                        if YouProgress.get("ClaimedTickets")
                        else ""
                    )
                    + (
                        f"> **Met:** {YourEmoji if YourEmoji else 'N/A'}\n"
                        f"> **Place:** {ordinal(YourPlace) if YourPlace else 'N/A'}"
                    ),
                )
        paginator = await PaginatorButtons()
        if pages:
            await paginator.start(ctx, pages=pages[:45], msg=msg)
        else:
            await msg.edit(
                content=f"  **{ctx.author.display_name},** there are no pages to display.",
                embed=None,
            )

    @quota.command(name="reset", description="Reset the message quota leaderboard")
    async def ResetQuota(
        self, ctx: commands.Context, quota: Literal["Messages", "Tickets"]
    ):
        await ctx.defer()
        if not await ModuleCheck(ctx.guild.id, "Quota"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Message Quota Permissions"):
            return

        view = ArmFire(ctx.author, quota)
        embed = (
            discord.Embed(
                description=f"By performing this action, you will reset all staff {quota} counts.\n This is **IRREVERSIBLE** and will cause all counts to become 0.",
                color=discord.Color.brand_red(),
            )
            .set_author(
                name="Warning",
                icon_url="https://cdn.discordapp.com/emojis/1123286604849631355.webp?size=96",
            )
            .set_footer(text="Quota Wipe")
        )
        await ctx.send(view=view, embed=embed)

    # Staff Panel ------

    @staff.command(description="Add a staff member to the staff database.")
    @app_commands.describe(
        staff="The staff member to add.",
        rank="The staff member's rank.",
        timezone="The staff member's timezone.",
    )
    async def add(
        self,
        ctx: commands.Context,
        staff: discord.User,
        rank: str,
        timezone: str = None,
    ):
        if not await ModuleCheck(ctx.guild.id, "Staff Database"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Staff Database Permissions"):
            return

        if await self.client.db["staff database"].find_one(
            {"guild_id": ctx.guild.id, "staff_id": staff.id}
        ):
            return await ctx.send(
                f"  **{ctx.author.display_name}**, this user is already a staff member.\n-#{arrow} You can always edit them using </staff edit:1165258229102682124>!"
            )
        try:
            await self.client.db["staff database"].insert_one(
                {
                    "guild_id": ctx.guild.id,
                    "staff_id": staff.id,
                    "name": staff.display_name,
                    "rank": rank,
                    "timezone": timezone,
                    "joinestaff": datetime.now(),
                    "rolename": rank,
                }
            )
        except Exception as e:
            print(e)

        await ctx.send(
            f"  **{ctx.author.display_name},** staff member added successfully.\n-# You should now be able to see them on </staff panel:1165258229102682124>!"
        )

    @staff.command(description="Remove a staff member from the staff database.")
    @app_commands.describe(staff="The staff member to remove.")
    async def remove(self, ctx: commands.Context, staff: discord.User):
        if not await ModuleCheck(ctx.guild.id, "Staff Database"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Staff Database Permissions"):
            return
        if not await self.client.db["staff database"].find_one(
            {"guild_id": ctx.guild.id, "staff_id": staff.id}
        ):
            return await ctx.send(
                f"  **{ctx.author.display_name}**, this user has not been added to the staff team.\n{arrow} To add someone to the staff database use </staff add:1165258229102682124>!"
            )
        try:
            await self.client.db["staff database"].delete_one(
                {"guild_id": ctx.guild.id, "staff_id": staff.id}
            )
        except Exception as e:
            print(e)
        await ctx.send(
            f"  **{ctx.author.display_name},** staff member removed successfully."
        )

    @staff.command(description="Edit a staff member's rank. (Staff Database)")
    @app_commands.describe(
        staff="The staff member to edit.",
        rank="The staff member's new rank.",
        timezone="The staff member's new timezone.",
        introduction="The staff member's new introduction.",
    )
    async def edit(
        self,
        ctx: commands.Context,
        staff: discord.User,
        rank: str,
        timezone: str = None,
        *,
        introduction=None,
    ):
        if not await ModuleCheck(ctx.guild.id, "Staff Database"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Staff Database Permissions"):
            return

        if not await self.client.db["staff database"].find_one(
            {"guild_id": ctx.guild.id, "staff_id": staff.id}
        ):
            return await ctx.send(
                f"  **{ctx.author.display_name}**, this user has not been added to the staff team.\n-#{arrow} To add someone to the staff database use </staff add:1165258229102682124>!"
            )
        try:
            await self.client.db["staff database"].update_one(
                {"guild_id": ctx.guild.id, "staff_id": staff.id},
                {
                    "$set": {
                        "rolename": rank,
                        "timezone": timezone or None,
                        "introduction": introduction or None,
                    }
                },
            )
        except Exception as e:
            print(e)
        await ctx.send(
            f"  **{ctx.author.display_name},** staff member edited successfully."
        )

    @staff.command(description="View a staff member's information. (Staff Database)")
    @app_commands.describe(staff="The staff member to view.")
    async def view(self, ctx: commands.Context, staff: discord.User):
        if not await ModuleCheck(ctx.guild.id, "Staff Database"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_staff_role(ctx, "Staff Database Permissions"):
            return
        result = await self.client.db["staff database"].find_one(
            {"guild_id": ctx.guild.id, "staff_id": staff.id}
        )
        if result is None:
            await ctx.send(
                f"  **{ctx.author.display_name}**, this user is not in the staff database."
            )
            return
        timezone = ""
        introduction = ""
        if result.get("introduction", None):
            introduction = f"\n\n**Introduction**\n```{result.get('introduction')}```"
        else:
            introduction = ""
        if result.get("timezone", None):
            timezone = f"\n> **Timezone:** {result.get('timezone')}"
        else:
            timezone = ""

        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="Information",
            value=f"> **Staff:** <@{staff.id}> (`{staff.id}`)\n> **Rank:** {result.get('rolename')}{timezone}\n> **Joined Staff:** <t:{int(result.get('joinestaff').timestamp())}:F>{introduction}",
        )
        if result:
            embed = discord.Embed(
                title=staff.display_name,
                color=discord.Color.dark_embed(),
            )
            embed.set_thumbnail(url=staff.display_avatar)
            embed.set_author(name=staff.name, icon_url=staff.display_avatar)
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                f"{ctx.author.display_name}, I couldn't find this user on the staff database.."
            )

    @staff.command(description="Give yourself an introduction (Staff Database)")
    @app_commands.describe(
        introduction="The introduction you want to add to your staff profile."
    )
    async def introduction(self, ctx: commands.Context, *, introduction):
        if not await ModuleCheck(ctx.guild.id, "Staff Database"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        result = await self.client.db["staff database"].find_one(
            {"guild_id": ctx.guild.id, "staff_id": ctx.author.id}
        )
        if not result:
            return await ctx.send(
                f"  **{ctx.author.display_name}**, you are not in the staff database."
            )

        await self.client.db["staff database"].update_one(
            {"guild_id": ctx.guild.id, "staff_id": ctx.author.id},
            {"$set": {"introduction": introduction}},
        )
        await ctx.send(
            f"  **{ctx.author.display_name}**, your introduction has been updated."
        )

    @staff.command(
        description="Send a panel that shows all staff members. (Staff Database)"
    )
    async def panel(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        if not await has_admin_role(ctx, "Staff Database Permissions"):
            return
        if not await ModuleCheck(ctx.guild.id, "Staff Database"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return

        custom = await self.client.db["Customisation"].find_one(
            {"guild_id": ctx.guild.id, "name": "Staff Panel"}
        )

        embed = discord.Embed(
            title="Staff Panel",
            description="Select a staff member to view their information.",
            color=discord.Color.dark_embed(),
        )
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        if custom and custom.get("embed"):
            from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed

            embed = await DisplayEmbed(custom, ctx.author)
        People = (
            await self.client.db["staff database"]
            .find({"guild_id": ctx.guild.id})
            .to_list(length=None)
        )
        options = []
        Added = set()
        for person in People:
            member = ctx.guild.get_member(person.get("staff_id"))
            if not member:
                try:
                    member = await ctx.guild.fetch_member(person.get("staff_id"))
                except (discord.HTTPException, discord.NotFound):
                    continue
            if member.id in Added:
                continue
            options.append(
                discord.SelectOption(
                    label=member.display_name,
                    value=str(member.id),
                    description=person.get("rolename"),
                    emoji="<:staff:1206248655359840326>",
                )
            )
            Added.add(member.id)

            if len(options) == 24:
                options.append(
                    discord.SelectOption(
                        label="View More",
                        value="more",
                        emoji="<:List:1223063187063308328>",
                        description="View more staff members.",
                    )
                )
                break
        view = Staffview(options=options)

        try:
            msg = await ctx.channel.send(embed=embed, view=view)
            await ctx.send(
                f"  **{ctx.author.display_name},** staff panel sent successfully.",
                ephemeral=True,
            )
        except discord.errors.Forbidden:
            await ctx.send(
                f"  **{ctx.author.display_name}**, I don't have permission to send messages in that channel.",
            )
            return
        except discord.errors.HTTPException:
            await ctx.send(
                f"  **{ctx.author.display_name}**, there is an error with the message. Make sure the embed/message is formed correctly.",
            )
            return
        await self.client.db["Views"].insert_one(
            {"_id": msg.id, "type": "staff", "guild": ctx.guild.id}
        )


class InfractionTypeSelection(discord.ui.Select):
    def __init__(
        self, author: discord.Member, options: list, failures: list[discord.Member]
    ):
        super().__init__(placeholder="Infraction Type", options=options)
        self.failures = failures
        self.author = author

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(
                embed=discord.Embed(
                    description=f"  **{interaction.user.display_name},** this is not your panel!",
                    color=discord.Colour.brand_red(),
                ),
                ephemeral=True,
            )
        await interaction.response.defer(ephemeral=True)
        action = self.values[0]
        reason = "Failed to meet the quota."
        notes = None
        expiration = None
        anonymous = True
        TypeActions = await interaction.client.db["infractiontypeactions"].find_one(
            {"guild_id": interaction.guild.id, "name": action}
        )
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            return await interaction.followup.send(
                f"  **{interaction.user.display_name}**, the bot isn't setup you can do that in /config.",
                ephemeral=True,
            )
        if not Config.get("Infraction", None):
            return await interaction.followup.send(
                f"  **{interaction.user.display_name}**, the infraction module is not setup you can do that in /config.",
                ephemeral=True,
            )
        try:
            channel = await interaction.client.fetch_channel(
                Config.get("Infraction", {}).get("channel", None)
            )
        except (discord.NotFound, discord.HTTPException):
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** hey I can't find your infraction channel it is configured but I can't find it?",
                ephemeral=True,
            )
        if not channel:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** hey I can't find your infraction channel it is configured but I can't find it?",
                ephemeral=True,
            )
        client = await interaction.guild.fetch_member(interaction.client.user.id)
        if channel.permissions_for(client).send_messages is False:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** oi I can't send messages in the infraction channel!!",
                ephemeral=True,
            )
        if expiration and not re.match(r"^\d+[mhdws]$", expiration):
            await interaction.response.send_message(
                f"  **{interaction.user.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.",
                ephemeral=True,
            )
            return
        from utils.format import strtotime

        if expiration:
            expiration = await strtotime(expiration)
        for user in self.failures:

            random_string = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )

            InfractionResult = await interaction.client.db["infractions"].insert_one(
                {
                    "guild_id": interaction.guild.id,
                    "staff": user.id,
                    "management": interaction.user.id,
                    "action": action,
                    "reason": reason,
                    "notes": notes,
                    "expiration": expiration,
                    "random_string": random_string,
                    "annonymous": anonymous,
                    "timestamp": datetime.now(),
                }
            )
            if not InfractionResult.inserted_id:
                await interaction.response.send_message(
                    content=f"  **{interaction.user.display_name},** hi I had a issue submitting this infraction please head to support!",
                    ephemeral=True,
                )
                return
            interaction.client.dispatch(
                "infraction", InfractionResult.inserted_id, Config, TypeActions
            )

        await interaction.edit_original_response(
            embed=None,
            content=f"  **{interaction.user.display_name},** succesfully punished all the failures.",
            view=None,
        )


class Staffview(discord.ui.View):
    def __init__(self, options: list = None):
        super().__init__(timeout=None)
        self.add_item(StaffPanel(options))


class StaffPanel(discord.ui.Select):
    def __init__(self, options: list = None):
        options = options or []
        super().__init__(
            placeholder="Select a staff member", options=options, custom_id="StaffPanel"
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "more":
            people = (
                await interaction.client.db["staff database"]
                .find({"guild_id": interaction.guild.id})
                .to_list(length=None)
            )
            options = []
            Existing = {
                int(option.value) for option in self.options if option.value.isdigit()
            }
            Added = set()
            for person in people:
                if person.get("staff_id") in Existing:
                    continue
                if person.get("staff_id") in Added:
                    continue
                member = interaction.guild.get_member(person.get("staff_id"))
                if not member:
                    try:
                        member = await interaction.guild.fetch_member(
                            person.get("staff_id")
                        )
                    except (discord.HTTPException, discord.NotFound):
                        continue
                options.append(
                    discord.SelectOption(
                        label=member.display_name,
                        value=str(member.id),
                        description=person.get("rolename"),
                        emoji="<:staff:1206248655359840326>",
                    )
                )
                Existing.add(member.id)
                Added.add(member.id)
                if len(options) == 25:
                    break
            self.options = options
            await interaction.response.send_message(
                view=self.view,
                ephemeral=True,
                content=f"<:List:1223063187063308328> **{interaction.user.display_name},** heres more people to view.",
            )
            return
        member = interaction.guild.get_member(int(self.values[0]))
        if not member:
            try:
                member = await interaction.guild.fetch_member(int(self.values[0]))
            except (discord.NotFound, discord.HTTPException):
                return await interaction.response.send_message(
                    content=f"  **{interaction.user.display_name},** I couldn't find that user.",
                    ephemeral=True,
                )
        result = await interaction.client.db["staff database"].find_one(
            {"guild_id": interaction.guild.id, "staff_id": member.id}
        )
        if not result:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** this user is not in the staff database.",
                ephemeral=True,
            )
        timezone = ""
        introduction = ""
        if result.get("introduction", None):
            introduction = f"\n\n**Introduction**\n```{result.get('introduction')}```"
        else:
            introduction = ""
        if result.get("timezone", None):
            timezone = f"\n> **Timezone:** {result.get('timezone')}"
        else:
            timezone = ""

        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="Information",
            value=f"> **Staff:** <@{member.id}> (`{member.id}`)\n> **Rank:** {result.get('rolename')}{timezone}\n> **Joined Staff:** <t:{int(result.get('joinestaff').timestamp())}:F>{introduction}",
        )
        embed.set_author(name=f"@{member.name}", icon_url=member.display_avatar)
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name=member.name, icon_url=member.display_avatar)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ArmFire(discord.ui.View):
    def __init__(self, author: discord.Member, action: str):
        super().__init__(timeout=360)
        self.author = author
        self.action = action

    @discord.ui.button(label="Arm", disabled=False)
    async def Arm(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.Arm.disabled = True
        self.Fire.disabled = False
        self.Arm.label = "Armed"
        self.Arm.style = discord.ButtonStyle.green
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Reset", disabled=True, style=discord.ButtonStyle.red)
    async def Fire(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if self.action == "Messages":
            await interaction.client.qdb["messages"].update_many(
                {"guild_id": interaction.guild.id},
                {"$set": {"message_count": 0}},
            )
        else:
            await interaction.client.db["Ticket Quota"].update_many(
                {"GuildID": interaction.guild.id},
                {"$set": {"ClaimedTickets": 0}},
            )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name}**, I have reset the staff leaderboard.",
            embed=None,
            view=None,
        )


class InfractionIssuer(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(
        label=f"",
        style=discord.ButtonStyle.grey,
        disabled=True,
        emoji="<:flag:1223062579346145402>",
    )
    async def issuer(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass


async def setup(client: commands.Bot) -> None:
    await client.add_cog(quota(client))
