import os
import random
import string
from datetime import datetime
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

import core.bot.HelpEmbeds as HelpEmbeds
from core.bot.Checks import EnsureConfig
from core.bot.Module import ModuleIsEnabled
from core.bot.emojis import *
from core.bot.permissions import Permissions
from core.bot.ui import BasicPaginator
from core.format import TimeReformat

environment = os.getenv("ENVIRONMENT")


async def CurrentLOA(
    ctx: commands.Context, loa: dict, user: discord.User = None
) -> discord.Embed:

    if not isinstance(ctx, commands.Context):
        author = ctx.user
    else:
        author = ctx.author
    embed = discord.Embed(color=discord.Color.dark_embed())
    embed.set_author(name="Leave Manage")
    embed.set_footer(text=f"@{author.name}", icon_url=author.display_avatar)

    if not loa:
        return "N/A"

    if not loa.get("start_time"):
        return "N/A"

    if user is None:
        user = ctx.author

    if loa.get("Accepted"):
        A = f"> **Accepted:** by <@{loa.get('Accepted').get('user')}> at <t:{int(loa.get('Accepted').get('time').timestamp())}:R>\n"
    else:
        A = ""

    embed.add_field(
        name="Current LOA",
        value=(
            f"> **Duration:** {await Duration(loa)}\n"
            f"> **Reason:** {loa.get('reason')}\n{A}"
        ),
    )
    embed.set_thumbnail(url=user.display_avatar)
    embed.set_footer(text=f"@{user.name}", icon_url=user.display_avatar)
    return embed


async def Duration(loa: dict, Format: str = "d - d") -> str:
    if not loa:
        return "N/A"

    Added = 0
    if loa.get("AddedTime") is not None:
        Added = int(loa["AddedTime"].get("Time", 0))

    Removed = 0
    if loa.get("RemovedTime") is not None and loa["RemovedTime"].get("Time", 0) > 0:
        Removed = int(loa["RemovedTime"].get("Time", 0))

    if not loa.get("start_time"):
        return "N/A"
    if Format == "d - d":
        return f"<t:{int(loa.get('start_time').timestamp())}:D> - <t:{int(loa.get('end_time').timestamp()) - (Removed - Added)}:D>"
    elif Format == "end_time":
        return f"<t:{int(loa.get('end_time').timestamp()) - (Removed - Added)}:D>"


class LOAModule(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_group()
    async def loa(self, ctx: commands.Context):
        return

    @loa.command(description="View past leave of absences")
    @Permissions("Staff")
    @ModuleIsEnabled("LOA")
    async def history(self, ctx: commands.Context):
        LOA = (
            await self.client.db["loa"]
            .find(
                {
                    "user": ctx.author.id,
                    "guild_id": ctx.guild.id,
                    "active": False,
                    "request": False,
                    "Declined": {"$exists": False},
                    "LoaID": {"$exists": True},
                }
            )
            .to_list(length=1000)
        )

        if len(LOA) == 0:
            await ctx.send(
                content=f"{no} **{ctx.author.display_name}**, there haven't been any LOAs yet."
            )

            return

        pages = []
        for i in range(0, len(LOA), 10):
            chunk = LOA[i : i + 10]
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_author(name="Past LOAs")
            for loa in chunk:
                if not loa.get("LoaID"):
                    continue
                embed.add_field(
                    name=f"@{loa.get('ExtendedUser').get('name')}",
                    value=(
                        f"> **ID:** `{loa.get('LoaID')}`\n"
                        f"> **Duration:** {await Duration(loa)}\n"
                        f"> **Reason:** {loa.get('reason')}\n"
                    ),
                    inline=False,
                )

            pages.append(embed)

        paginator = BasicPaginator(author=ctx.author, embeds=pages)
        await ctx.send(embed=pages[0], view=paginator)

    @loa.command(description="View active leave of absences")
    @Permissions("Staff")
    @ModuleIsEnabled("LOA")
    async def active(self, ctx: commands.Context):
        LOA = (
            await self.client.db["loa"]
            .find(
                {
                    "guild_id": ctx.guild.id,
                    "request": False,
                    "active": True,
                    "LoaID": {"$exists": True},
                }
            )
            .to_list(length=1000)
        )

        if len(LOA) == 0:
            await ctx.send(
                content=f"{no} **{ctx.author.display_name}**, there aren't any active LOAs."
            )

            return

        pages = []
        for i in range(0, len(LOA), 10):
            chunk = LOA[i : i + 10]
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_author(name="Active LOAs")

            for loa in chunk:
                if not loa.get("LoaID"):
                    continue
                embed.add_field(
                    name=f"@{loa.get('ExtendedUser').get('name')}",
                    value=(
                        f"> **ID:** `{loa.get('LoaID')}`\n"
                        f"> **Duration:** <t:{int(loa.get('start_time').timestamp())}:D> - <t:{int(loa.get('end_time').timestamp())}:D>\n"
                        f"> **Reason:** {loa.get('reason')}\n"
                    ),
                    inline=False,
                )
            pages.append(embed)

        paginator = BasicPaginator(author=ctx.author, embeds=pages)
        await ctx.send(embed=pages[0], view=paginator)

    @loa.command(description="View pending leave of absence requests")
    @Permissions("Staff")
    @ModuleIsEnabled("LOA")
    async def pending(self, ctx: commands.Context):
        LOA = (
            await self.client.db["loa"]
            .find(
                {
                    "guild_id": ctx.guild.id,
                    "request": True,
                    "active": False,
                    "LoaID": {"$exists": True},
                }
            )
            .to_list(length=1000)
        )

        if len(LOA) == 0:
            await ctx.send(
                content=f"{no} **{ctx.author.display_name}**, there aren't any pending LOAs."
            )
            return

        pages = []
        for i in range(0, len(LOA), 1):

            chunk = LOA[i : i + 1]
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_author(name="Pending LOA Requests")
            embed.set_footer(text=f"Page {i // 1 + 1} of {len(LOA) // 1 + 1}")
            for loa in chunk:
                if not loa.get("LoaID"):
                    continue
                embed.add_field(
                    name=f"@{loa.get('ExtendedUser').get('name')}",
                    value=(
                        f"> **ID:** `{loa.get('LoaID')}`\n"
                        f"> **Duration:** <t:{int(loa.get('start_time').timestamp())}:D> - <t:{int(loa.get('end_time').timestamp())}:D>\n"
                        f"> **Reason:** {loa.get('reason')}\n"
                    ),
                    inline=False,
                )
                embed.set_footer(text=loa.get("LoaID"))
            pages.append(embed)

        Act = PendingActions(ctx.author)

        paginator = BasicPaginator(author=ctx.author, embeds=pages)
        paginator.add_item(Act.Accept)
        paginator.add_item(Act.Decline)

        await ctx.send(embed=pages[0], view=paginator)

    @loa.command(description="Request a leave of absence")
    @app_commands.describe(duration="How long do you want the LOA for? (m/h/d/w)")
    @Permissions("Staff")
    @ModuleIsEnabled("LOA")
    async def request(
        self, ctx: commands.Context, duration: str, reason: str, start: str = None
    ):
        await ctx.defer(ephemeral=True)

        LOA = await self.client.db["loa"].find_one(
            {
                "user": ctx.author.id,
                "guild_id": ctx.guild.id,
                "active": True,
                "request": False,
            }
        )
        Also = await self.client.db["loa"].find_one(
            {
                "user": ctx.author.id,
                "guild_id": ctx.guild.id,
                "request": True,
            }
        )
        if LOA or Also:
            await ctx.send(
                content=f"{no} **{ctx.author.display_name},** you already have an active LOA. Please end it before requesting a new one."
            )
            return

        Start = datetime.now()
        try:
            S = False
            if start:
                S = True
                Start = await TimeReformat(start)
                if Start is None:
                    await ctx.send(
                        content=f"{no} **{ctx.author.display_name}**, invalid start time format. (example: 2023-01-01 or 2d = 2 days from now)"
                    )
                    return
            else:
                Start = datetime.now()

            Duration = await TimeReformat(duration, DifferentNow=Start)
        except (ValueError, TypeError, AttributeError):
            await ctx.send(
                content=f"{no} **{ctx.author.display_name}**, invalid duration format. (example: 2d = 2 days, 2m = 2 minutes and etc)"
            )
            return
        except OverflowError:
            await ctx.send(
                content=f"{no} **{ctx.author.display_name}**, the duration is too long."
            )
            return

        if Duration < datetime.now():
            await ctx.send(
                content=f"{no} **{ctx.author.display_name}**, your LOA can't be in the past. On a real note, how did you even manage this?"
            )
            return

        if Duration > datetime.now() + timedelta(days=1000):
            await ctx.send(
                content=f"{no} **{ctx.author.display_name}**, your LOA is wayyy too long."
            )
            return
        if Duration < datetime.now() + timedelta(days=1):
            await ctx.send(
                content=f"{no} **{ctx.author.display_name},** your LOA must atleast be a day long."
            )
            return

        C = await EnsureConfig(ctx, "LOA")
        MSG = await ctx.send(
            f"<a:Loading:1167074303905386587> **{ctx.author.display_name},** requesting LOA..."
        )
        if not C.get("LOA", {}).get("channel"):
            await MSG.edit(
                embed=HelpEmbeds.NoChannelSet(), view=HelpEmbeds.Support(), content=None
            )
            return
        try:
            CH = await self.client.fetch_channel(C.get("LOA", {}).get("channel", 0))
        except (discord.HTTPException, discord.NotFound):
            return await MSG.edit(
                embed=HelpEmbeds.ChannelNotFound(),
                content=None,
                view=HelpEmbeds.Support(),
            )
        client = await ctx.guild.fetch_member(self.client.user.id)
        if (
            CH.permissions_for(client).send_messages is False
            or CH.permissions_for(client).view_channel is None
        ):

            return await MSG.edit(
                content=f"",
                embed=HelpEmbeds.NoPermissionChannel(CH),
            )
        R = await self.client.db["loa"].insert_one(
            {
                "LoaID": "".join(
                    random.choices(string.ascii_letters + string.digits, k=8)
                ),
                "user": ctx.author.id,
                "ExtendedUser": {
                    "id": ctx.author.id,
                    "name": ctx.author.name,
                    "thumbnail": (
                        ctx.author.display_avatar.url
                        if ctx.author.display_avatar
                        else None
                    ),
                },
                "guild_id": ctx.guild.id,
                "start_time": Start,
                "end_time": Duration,
                "reason": reason,
                "active": False,
                "request": True,
                "scheduled": S,
                "AddedTime": {
                    "Time": 0,
                    "Reason": None,
                    "Log": [],
                },
                "RemovedTime": {
                    "Duration": 0,
                    "Log": [],
                },
            }
        )
        if not R.acknowledged:
            await MSG.edit(
                embed=HelpEmbeds.CustomError("Failed to request LOA."),
                content=None,
            )
            return
        self.client.dispatch(
            "leave_request",
            R.inserted_id,
        )
        try:
            await MSG.edit(
                content=(
                    f"{tick} **{ctx.author.display_name},** loa requested. Please wait for a staff member to accept it."
                ),
                embed=None,
            )
        except (discord.HTTPException, discord.Forbidden):
            await ctx.send(
                content=(
                    f"{tick} **{ctx.author.display_name},** loa requested. Please wait for a staff member to accept it."
                ),
                embed=None,
            )

    @loa.command(description="Manage your own leave of absence")
    @Permissions("Staff")
    @ModuleIsEnabled("LOA")
    async def manage(self, ctx: commands.Context):
        ActiveLOA = await self.client.db["loa"].find_one(
            {
                "user": ctx.author.id,
                "guild_id": ctx.guild.id,
                "active": True,
                "request": False,
                "start_time": {"$lt": datetime.now()},
            }
        )
        RequestLOA = await self.client.db["loa"].find_one(
            {
                "user": ctx.author.id,
                "guild_id": ctx.guild.id,
                "active": False,
                "request": True,
            }
        )
        PastLOAs = (
            await self.client.db["loa"]
            .find(
                {
                    "user": ctx.author.id,
                    "guild_id": ctx.guild.id,
                    "active": False,
                    "request": False,
                    "Declined": {"$exists": False},
                }
            )
            .to_list(length=750)
        )

        view = LOAManage(ctx.author, ctx.author, True)
        embed = discord.Embed(color=discord.Color.dark_embed())
        view.PLOA.label = f"Past LOA's ({len(PastLOAs)})"
        if len(PastLOAs) > 0:
            view.PLOA.disabled = False

        if ActiveLOA:
            embed = await CurrentLOA(ctx, ActiveLOA)
            view.remove_item(view.CancelRequest)

        elif RequestLOA:
            embed = await CurrentLOA(ctx, RequestLOA)
            embed.description = (
                "-# This leave is currently being reviewed by staff members"
            )
            view.remove_item(view.RequestExt)
            view.remove_item(view.ReduceT)
            view.remove_item(view.End)

        else:
            embed.add_field(
                name="Current LOA",
                value="> You currently have no active LOA. To request one, use `/loa request`",
            )
            view.remove_item(view.RequestExt)
            view.remove_item(view.ReduceT)
            view.remove_item(view.End)
            view.remove_item(view.CancelRequest)
        view.remove_item(view.CreateLOA)
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_author(name="Leave Manage")
        embed.set_footer(text=f"@{ctx.author.name}", icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed, view=view)

    @loa.command(description="Manage a staff's leave of absence")
    @app_commands.describe(user="The user to manage")
    @Permissions("Admin")
    @ModuleIsEnabled("LOA")
    async def admin(self, ctx: commands.Context, user: discord.User):
        ActiveLOA = await self.client.db["loa"].find_one(
            {
                "user": user.id,
                "guild_id": ctx.guild.id,
                "active": True,
                "request": False,
                "start_time": {"$lt": datetime.now()},
            }
        )
        PastLOAs = (
            await self.client.db["loa"]
            .find(
                {
                    "user": user.id,
                    "guild_id": ctx.guild.id,
                    "active": False,
                    "Declined": {"$exists": False},
                }
            )
            .to_list(length=750)
        )

        view = LOAManage(ctx.author, user)
        embed = discord.Embed(color=discord.Color.dark_embed())

        view.PLOA.label = f"Past LOA's ({len(PastLOAs)})"
        if len(PastLOAs) > 0:
            view.PLOA.disabled = False

        if ActiveLOA:
            embed = await CurrentLOA(ctx, ActiveLOA, user)
            view.remove_item(view.CreateLOA)

        else:
            embed.add_field(
                name="Current LOA",
                value="> They have no active LOA.",
            )

            view.remove_item(view.RequestExt)
            view.remove_item(view.ReduceT)
            view.remove_item(view.End)

        view.remove_item(view.CancelRequest)
        view.RequestExt.label = "Add Time"
        embed.set_thumbnail(url=user.display_avatar)
        embed.set_author(name="Leave Admin")
        embed.set_footer(text=f"@{user.name}", icon_url=user.display_avatar)
        await ctx.send(embed=embed, view=view)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(LOAModule(client))


class LOAManage(discord.ui.View):
    def __init__(
        self,
        author: discord.Member,
        target: discord.User = None,
        ExtRequest: bool = False,
    ):
        super().__init__(timeout=960)
        self.author = author
        self.target = target
        self.ExtRequest = ExtRequest

    @discord.ui.button(label="Cancel Request", style=discord.ButtonStyle.red, row=0)
    async def CancelRequest(self, interaction: discord.Interaction, _):
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                embed=HelpEmbeds.NotYourPanel(), ephemeral=True
            )
            return
        RequestLOA = await interaction.client.db["loa"].find_one(
            {
                "user": interaction.user.id,
                "guild_id": interaction.guild.id,
                "active": False,
                "request": True,
            }
        )
        if not RequestLOA:
            return await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name}**, you have no current active request."
            )

        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name},** successfully cancelled the leave request.",
            view=None,
            embed=None,
        )

        interaction.client.dispatch("leave_request_cancel", RequestLOA.get("_id"))

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green, row=2)
    async def CreateLOA(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                embed=HelpEmbeds.NotYourPanel(), ephemeral=True
            )
            return
        await interaction.response.send_modal(CreateLOA(interaction.user, self.target))

    @discord.ui.button(
        label="Request Extension", style=discord.ButtonStyle.green, row=0
    )
    async def RequestExt(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                embed=HelpEmbeds.NotYourPanel(), ephemeral=True
            )
            return
        await interaction.response.send_modal(
            AddTime(author=self.author, target=self.target, RequestExt=self.ExtRequest)
        )

    @discord.ui.button(label="Reduce Time", style=discord.ButtonStyle.red, row=0)
    async def ReduceT(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                embed=HelpEmbeds.NotYourPanel(), ephemeral=True
            )
            return

        await interaction.response.send_modal(
            RemoveTime(author=self.author, target=self.target)
        )

    @discord.ui.button(label="End", style=discord.ButtonStyle.blurple, row=0)
    async def End(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                ephemeral=True, embed=HelpEmbeds.NotYourPanel()
            )
            return

        await interaction.response.defer(ephemeral=True)
        LOA = await interaction.client.db["loa"].find_one(
            {
                "user": self.target.id,
                "guild_id": interaction.guild.id,
                "active": True,
            }
        )
        if LOA is None:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("You have no active LOA."), ephemeral=True
            )
            return

        Z = await interaction.client.db["loa"].update_one(
            {
                "user": self.target.id,
                "guild_id": interaction.guild.id,
                "active": True,
            },
            {
                "$set": {
                    "end_time": datetime.now(),
                    "active": False,
                }
            },
        )
        if Z.modified_count == 0:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("Failed to end LOA."), ephemeral=True
            )
            return
        interaction.client.dispatch(
            "leave_end",
            LOA.get("_id"),
        )
        interaction.client.dispatch(
            "leave_log", LOA.get("_id"), "ForceEnd", interaction.user
        )

        await interaction.edit_original_response(
            content=(
                f"{tick} **{interaction.user.display_name}**, I've ended `@{self.target.name}'s` LOA."
                if self.target == self.author
                else f"{tick} **{interaction.user.display_name}**, I've ended your LOA."
            ),
            embed=None,
            view=None,
        )

    @discord.ui.button(
        label="Past LOA's (0)", style=discord.ButtonStyle.blurple, disabled=True, row=0
    )
    async def PLOA(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                ephemeral=True, embed=HelpEmbeds.NotYourPanel()
            )
            return

        await interaction.response.defer(ephemeral=True)
        PastLOAs = (
            await interaction.client.db["loa"]
            .find(
                {
                    "user": self.target.id,
                    "guild_id": interaction.guild.id,
                    "active": False,
                    "request": False,
                    "Declined": {"$exists": False},
                }
            )
            .to_list(length=750)
        )
        if len(PastLOAs) == 0:
            await interaction.followup.send("You have no past LOA's.", ephemeral=True)
            return

        pages = []
        for i in range(0, len(PastLOAs), 10):
            chunk = PastLOAs[i : i + 10]
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_thumbnail(url=self.target.display_avatar)
            embed.set_author(name="Leave Manage")
            embed.set_footer(
                text=f"@{self.target.name}", icon_url=self.target.display_avatar
            )
            for loa in chunk:
                A = ""
                if loa.get("Accepted"):
                    A = f"> **Accepted:** by <@{loa.get('Accepted').get('user')}> at <t:{int(loa.get('Accepted').get('time').timestamp())}:R>\n"

                embed.add_field(
                    name=await Duration(loa),
                    value=f"> **Reason:** {loa.get('reason')}\n{A}",
                    inline=False,
                )
            pages.append(embed)

        paginator = BasicPaginator(author=interaction.user, embeds=pages)
        await interaction.followup.send(embed=pages[0], view=paginator, ephemeral=True)


class RemoveTime(discord.ui.Modal):
    def __init__(self, author: discord.Member, target: discord.User = None):
        super().__init__(title="Remove Time")
        self.author = author
        self.target = target

        self.duration = discord.ui.TextInput(
            label="Duration",
            placeholder="1d 2h 30m",
            required=True,
            max_length=20,
        )
        self.add_item(self.duration)

    async def on_submit(self, interaction: discord.Interaction):

        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                embed=HelpEmbeds.NotYourPanel(), ephemeral=True
            )
            return

        if self.target is None:
            self.target = interaction.user
        try:
            Duration = await TimeReformat(self.duration.value, Interger=True)
        except (ValueError, TypeError, AttributeError):
            await interaction.response.send_message(
                embed=HelpEmbeds.CustomError("Invalid duration format."), ephemeral=True
            )
        except OverflowError:
            await interaction.response.send_message(
                embed=HelpEmbeds.CustomError("The duration is too long."),
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        LOA = await interaction.client.db["loa"].find_one(
            {
                "user": self.target.id,
                "guild_id": interaction.guild.id,
                "active": True,
            }
        )
        Org = LOA.copy()
        Z = await interaction.client.db["loa"].update_one(
            {
                "user": self.target.id,
                "guild_id": interaction.guild.id,
                "active": True,
            },
            {
                "$set": {
                    "RemovedTime.Time": LOA.get("RemovedTime", {}).get("Time", 0)
                    + Duration,
                    "RemovedTime.Log": LOA.get("RemovedTime", {}).get("Log", [])
                    + [
                        {
                            "time": datetime.now(),
                            "duration": Duration,
                            "user": interaction.user.id,
                        }
                    ],
                }
            },
        )
        if Z.modified_count == 0:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("Failed to add time."), ephemeral=True
            )
            return

        await interaction.followup.send(
            content=(
                f"{tick} **{interaction.user.display_name}**, I've removed `{self.duration.value}` from `@{self.target.name}'s` LOA."
                if self.target == self.author
                else f"{tick} **{interaction.user.display_name}**, I've added `{self.duration.value}` to your LOA."
            ),
            ephemeral=True,
        )
        LOA = await interaction.client.db["loa"].find_one(
            {
                "user": self.target.id,
                "guild_id": interaction.guild.id,
                "active": True,
            }
        )
        interaction.client.dispatch(
            "leave_log", LOA.get("_id"), "modify", interaction.user, Org
        )
        await interaction.edit_original_response(
            embed=await CurrentLOA(ctx=interaction, loa=LOA, user=self.target),
        )


class AddTime(discord.ui.Modal):
    def __init__(
        self, author: discord.Member, target: discord.User = None, RequestExt=False
    ):
        super().__init__(title="Add Time" if not RequestExt else "Request Extension")
        self.author = author
        self.target = target
        self.RequestExt = RequestExt

        self.duration = discord.ui.TextInput(
            label="Duration",
            placeholder="1d 2h 30m",
            required=True,
            max_length=20,
        )
        self.add_item(self.duration)

        if RequestExt:
            self.reason = discord.ui.TextInput(
                label="Reason",
                placeholder="Why are you requesting this extension?",
                required=True,
                max_length=200,
            )
            self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                embed=HelpEmbeds.NotYourPanel(), ephemeral=True
            )
            return

        if self.target is None:
            self.target = interaction.user
        try:
            Duration = await TimeReformat(self.duration.value, Interger=True)
        except (ValueError, TypeError, AttributeError):
            await interaction.response.send_message(
                embed=HelpEmbeds.CustomError("Invalid duration format."), ephemeral=True
            )
            return
        except OverflowError:
            await interaction.response.send_message(
                embed=HelpEmbeds.CustomError("The duration is too long."),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        LOA = await interaction.client.db["loa"].find_one(
            {
                "user": self.target.id,
                "guild_id": interaction.guild.id,
                "active": True,
            }
        )
        Org = LOA.copy()

        if self.RequestExt:
            C = await interaction.client.db["Config"].find_one(
                {"_id": interaction.guild.id}
            )
            if not C:
                await interaction.followup.send(
                    embed=HelpEmbeds.BotNotConfigured(),
                    view=HelpEmbeds.Support(),
                    ephemeral=True,
                )
                return
            if not C.get("LOA", {}):
                await interaction.followup.send(
                    embed=HelpEmbeds.ModuleNotEnabled(),
                    view=HelpEmbeds.Support(),
                    ephemeral=True,
                )
                return
            if not C.get("LOA", {}).get("channel"):
                await interaction.followup.send(
                    embed=HelpEmbeds.NoChannelSet(),
                    view=HelpEmbeds.Support(),
                    ephemeral=True,
                )
                return
            try:
                CH = await interaction.client.fetch_channel(
                    C.get("LOA", {}).get("channel", 0)
                )
            except (discord.HTTPException, discord.NotFound):
                await interaction.followup.send(
                    embed=HelpEmbeds.ChannelNotFound(), ephemeral=True
                )
                return
            client = await interaction.guild.fetch_member(interaction.client.user.id)
            if (
                CH.permissions_for(client).send_messages is False
                or CH.permissions_for(client).view_channel is None
            ):
                await interaction.followup.send(
                    embed=HelpEmbeds.NoPermissionChannel(CH), ephemeral=True
                )
                return
            Z = await interaction.client.db["ExtRequests"].insert_one(
                {
                    "LoaID": LOA.get("LoaID"),
                    "user": self.target.id,
                    "guild": interaction.guild.id,
                    "reason": self.reason.value,
                    "duration": Duration,
                    "durationstr": self.duration.value,
                    "requested_by": interaction.user.id,
                    "requested_at": datetime.now(),
                    "status": "Pending",
                    "Accepted": None,
                    "Declined": None,
                    "ExtendedUser": {
                        "id": self.target.id,
                        "name": self.target.name,
                        "thumbnail": (
                            self.target.display_avatar.url
                            if self.target.display_avatar
                            else None
                        ),
                    },
                }
            )
            interaction.client.dispatch("leave_ext_request", Z.inserted_id)
            await interaction.followup.send(
                content=f"{tick} **{interaction.user.display_name}**, I've requested an extension for `{self.duration.value}` on your LOA.",
                ephemeral=True,
            )
            return
        else:
            interaction.client.dispatch(
                "leave_log", LOA.get("_id"), "modify", interaction.user, Org
            )
            LOA = await interaction.client.db["loa"].find_one(
                {
                    "user": self.target.id,
                    "guild_id": interaction.guild.id,
                    "active": True,
                }
            )

            Z = await interaction.client.db["loa"].update_one(
                {
                    "user": self.target.id,
                    "guild_id": interaction.guild.id,
                    "active": True,
                },
                {
                    "$set": {
                        "AddedTime.Time": LOA.get("AddedTime", {}).get("Time", 0)
                        + Duration,
                        "AddedTime.Reason": (
                            self.reason.value if hasattr(self, "reason") else None
                        ),
                        "AddedTime.RequestExt": (
                            {
                                "status": "Pending",
                                "acceptedBy": None,
                                "AcceptedAt": None,
                            }
                            if self.RequestExt
                            else None
                        ),
                        "AddedTime.Log": LOA.get("AddedTime", {}).get("Log", [])
                        + [
                            {
                                "time": datetime.now(),
                                "duration": Duration,
                                "user": interaction.user.id,
                                "reason": (
                                    self.reason.value
                                    if hasattr(self, "reason")
                                    else None
                                ),
                            }
                        ],
                    }
                },
            )
            if Z.modified_count == 0:
                await interaction.followup.send(
                    embed=HelpEmbeds.CustomError("Failed to add time."), ephemeral=True
                )
                return

            await interaction.edit_original_response(
                embed=await CurrentLOA(ctx=interaction, loa=LOA, user=self.target),
            )
            await interaction.followup.send(
                content=(
                    f"{tick} **{interaction.user.display_name}**, I've added `{self.duration.value}` to `@{self.target.name}'s` LOA."
                    if self.target == self.author
                    else f"{tick} **{interaction.user.display_name}**, I've added `{self.duration.value}` to your LOA."
                ),
                ephemeral=True,
            )


class CreateLOA(discord.ui.Modal):
    def __init__(self, author: discord.Member, target: discord.Member):
        super().__init__(title="Create LOA")
        self.author = author
        self.target = target

        self.duration = discord.ui.TextInput(
            label="Duration",
            placeholder="1d 2h 30m",
            required=True,
            max_length=20,
        )
        self.add_item(self.duration)

        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Why are you creating this LOA?",
            required=True,
            max_length=200,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                embed=HelpEmbeds.NotYourPanel(), ephemeral=True
            )
            return

        try:
            Duration = await TimeReformat(self.duration.value)
        except (ValueError, TypeError, AttributeError):
            await interaction.response.send_message(
                embed=HelpEmbeds.CustomError("Invalid duration format."), ephemeral=True
            )
            return
        except OverflowError:
            await interaction.response.send_message(
                embed=HelpEmbeds.CustomError("The duration is too long."),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        Start = datetime.now()

        LOA = await interaction.client.db["loa"].insert_one(
            {
                "LoaID": "".join(
                    random.choices(string.ascii_letters + string.digits, k=8)
                ),
                "user": self.target.id,
                "ExtendedUser": {
                    "id": self.target.id,
                    "name": self.target.name,
                    "thumbnail": (
                        self.target.display_avatar.url
                        if self.target.display_avatar
                        else None
                    ),
                },
                "Created": {
                    "id": self.author.id,
                    "name": self.author.name,
                    "thumbnail": (
                        self.author.display_avatar.url
                        if self.author.display_avatar
                        else None
                    ),
                },
                "guild_id": interaction.guild.id,
                "start_time": Start,
                "end_time": Duration,
                "reason": self.reason.value,
                "active": True,
                "request": False,
                "AddedTime": {
                    "Time": 0,
                    "Reason": None,
                    "Log": [],
                },
                "RemovedTime": {
                    "Duration": 0,
                    "Log": [],
                },
            }
        )

        if not LOA.acknowledged:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("Failed to create LOA."),
                ephemeral=True,
            )
            return

        interaction.client.dispatch("leave_start", LOA.inserted_id)
        interaction.client.dispatch("leave_create", LOA.inserted_id)

        await interaction.edit_original_response(
            content=f"{tick} **{interaction.user.display_name}**, the LOA has been created.",
            embed=None,
            view=None,
        )


class PendingActions(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=960)
        self.author = author

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, row=0)
    async def Accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                embed=HelpEmbeds.NotYourPanel(), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        embed = interaction.message.embeds[0]

        LOA = await interaction.client.db["loa"].find_one(
            {
                "LoaID": embed.footer.text,
            }
        )
        if LOA is None:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("This isn't a valid LOA Request"),
                ephemeral=True,
            )
            return

        Z = await interaction.client.db["loa"].update_one(
            {
                "LoaID": embed.footer.text,
                "guild_id": interaction.guild.id,
                "active": False,
                "request": True,
            },
            {
                "$set": {
                    "Accepted": {
                        "user": interaction.user.id,
                        "time": datetime.now(),
                    },
                    "active": not LOA.get("scheduled"),
                    "request": False,
                }
            },
        )
        if Z.modified_count == 0:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("Failed to accept LOA."), ephemeral=True
            )
            return
        interaction.client.dispatch(
            "leave_update",
            LOA.get("_id"),
            "Accepted",
            interaction.user,
        )
        await interaction.edit_original_response(
            content=(
                f"{tick} **{interaction.user.display_name}**, I've accepted `@{LOA.get('ExtendedUser', {}).get('name', 'N/A')}'s` LOA."
            ),
            view=None,
            embed=None,
        )

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, row=0)
    async def Decline(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not interaction.user.id == self.author.id:
            await interaction.response.send_message(
                embed=HelpEmbeds.NotYourPanel(), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        embed = interaction.message.embeds[0]

        LOA = await interaction.client.db["loa"].find_one(
            {
                "LoaID": embed.footer.text,
                "guild_id": interaction.guild.id,
                "active": False,
                "request": True,
            }
        )
        if LOA is None:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("This isn't a valid LOA Request"),
                ephemeral=True,
            )
            return

        Z = await interaction.client.db["loa"].update_one(
            {
                "LoaID": embed.footer.text,
                "guild_id": interaction.guild.id,
                "active": False,
                "request": True,
            },
            {
                "$set": {
                    "Accepted": None,
                    "active": False,
                    "request": False,
                }
            },
        )
        if Z.modified_count == 0:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("Failed to decline LOA."), ephemeral=True
            )
            return
        interaction.client.dispatch(
            "leave_update",
            LOA.get("_id"),
            "Declined",
            interaction.user,
        )
        await interaction.edit_original_response(
            content=(
                f"{tick} **{interaction.user.display_name}**, I've declined `@{LOA.get('ExtendedUser', {}).get('name', 'N/A')}'s` LOA."
            ),
            view=None,
            embed=None,
        )
