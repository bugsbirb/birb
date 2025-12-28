import discord
from discord.ext import commands
from bson import ObjectId
from utils.emojis import *
from utils import HelpEmbeds
from datetime import datetime
from Cogs.Modules.leaves import Duration
from utils.permissions import has_admin_role


class on_leave(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_leave_request(self, _id: ObjectId):
        L = await self.client.db["loa"].find_one({"_id": _id})
        if L is None:
            return
        G = self.client.get_guild(L.get("guild_id"))
        if not G:
            return
        C = await self.client.db["Config"].find_one({"_id": G.id})
        if not C:
            return
        if not C.get("LOA", None):
            return
        if not C.get("LOA", {}).get("channel", None):
            return
        try:
            CH = await G.fetch_channel(int(C.get("LOA", {}).get("channel", 0)))
        except (discord.NotFound, discord.HTTPException):
            return

        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="Leave Request",
            value=f"> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(L.get('start_time').timestamp())}>\n> **End Date:** <t:{int(L.get('end_time').timestamp())}>\n> **Reason:** {L.get('reason')}",
        )
        embed.set_author(
            name=f"@{L.get('ExtendedUser', {}).get('name')}",
            icon_url=L.get("ExtendedUser", {}).get("thumbnail"),
        )
        embed.set_thumbnail(url=L.get("ExtendedUser", {}).get("thumbnail"))
        embed.set_footer(text=L.get("LoaID"))

        try:
            CM = await CH.send(embed=embed, view=PendingActions())
        except (discord.HTTPException, discord.Forbidden):
            return

        await self.client.db["loa"].update_one(
            {"_id": L.get("_id")},
            {
                "$set": {
                    "messageid": CM.id,
                    "channel_id": CH.id,
                }
            },
        )

    @commands.Cog.listener()
    async def on_ready(self):
        self.client.add_view(PendingActions())
        self.client.add_view(ExtRequest())

    @commands.Cog.listener()
    async def on_leave_start(self, _id: ObjectId):
        L = await self.client.db["loa"].find_one({"_id": _id})
        if L is None:
            return
        G = self.client.get_guild(L.get("guild_id"))
        if not G:
            return
        C = await self.client.db["Config"].find_one({"_id": G.id})
        if not C:
            return
        if not C.get("LOA", None):
            return
        try:
            Member = await G.fetch_member(L.get("user"))
        except (discord.NotFound, discord.HTTPException):
            Member = None
        if not Member:
            return

        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="Leave Started",
            value=f"> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(L.get('start_time').timestamp())}>\n> **End Date:** <t:{int(L.get('end_time').timestamp())}>\n> **Reason:** {L.get('reason')}",
        )
        embed.set_author(
            name=f"@{L.get('ExtendedUser', {}).get('name')}",
            icon_url=L.get("ExtendedUser", {}).get("thumbnail"),
        )
        embed.set_footer(text=L.get("LoaID"))
        if Member:
            try:
                await Member.send(
                    embed=embed,
                )
            except (discord.Forbidden, discord.HTTPException):
                return
            if C.get("LOA", {}).get("role", None):
                try:
                    role = G.get_role(int(C.get("LOA", {}).get("role", 0)))
                    if role:
                        await Member.add_roles(role, reason="Leave Started")
                except (discord.NotFound, discord.HTTPException):
                    pass

    @commands.Cog.listener()
    async def on_leave_end(self, _id: ObjectId):
        L = await self.client.db["loa"].find_one({"_id": _id})
        if L is None:
            return
        G = self.client.get_guild(L.get("guild_id"))
        if not G:
            return
        C = await self.client.db["Config"].find_one({"_id": G.id})
        if not C:
            return
        if not C.get("LOA", None):
            return
        if not C.get("LOA", {}).get("channel", None):
            return
        try:
            CH = await G.fetch_channel(int(C.get("LOA", {}).get("channel", 0)))
        except (discord.NotFound, discord.HTTPException):
            return
        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="Leave Ended",
            value=f"> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(L.get('start_time').timestamp())}>\n> **End Date:** {await Duration(L, 'end_time')}\n> **Reason:** {L.get('reason')}",
        )
        embed.set_author(
            name=f"@{L.get('ExtendedUser', {}).get('name')}",
            icon_url=L.get("ExtendedUser", {}).get("thumbnail"),
        )
        embed.set_thumbnail(url=L.get("ExtendedUser", {}).get("thumbnail"))
        embed.set_footer(text=L.get("LoaID"))
        try:
            CM = await CH.fetch_message(L.get("messageid"))
            await CM.reply(embed=embed)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            return
        try:
            member = await G.fetch_member(L.get("user"))
        except (discord.NotFound, discord.HTTPException):
            member = None
        if member:
            try:

                if C.get("LOA", {}).get("role", None):
                    try:
                        role = G.get_role(int(C.get("LOA", {}).get("role", 0)))
                        if role and member:
                            await member.remove_roles(role, reason="Leave Ended")
                    except (discord.NotFound, discord.HTTPException):
                        pass
            except discord.Forbidden:
                pass

            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_leave_log(
        self, _id: ObjectId, action: str, author: discord.User, unmodified: dict = None
    ):

        L = await self.client.db["loa"].find_one({"_id": _id})
        if L is None:
            return
        G = self.client.get_guild(L.get("guild_id"))
        if not G:
            return
        C = await self.client.db["Config"].find_one({"_id": G.id})
        if not C:
            return
        if not C.get("LOA", None):
            return
        if not C.get("LOA", {}).get("LogChannel", None):
            return
        try:
            CH = await G.fetch_channel(int(C.get("LOA", {}).get("LogChannel", 0)))
        except (discord.NotFound, discord.HTTPException):
            return
        embed = discord.Embed()
        color = {
            "ForceEnd": discord.Color.brand_red(),
            "modify": discord.Color.dark_purple(),
        }
        embed.color = color.get(action, discord.Color.dark_embed())
        embed.timestamp = discord.utils.utcnow()
        if author:
            embed.set_footer(text=f"@{author.name}", icon_url=author.display_avatar)
        if action == "modify":
            embed.title = "Leave Modified"
            embed.add_field(
                name="Before",
                value=f"> **ID:** `{L.get('LoaID')}`\n> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(unmodified.get('start_time').timestamp())}>\n> **End Date:** {await Duration(unmodified, 'end_time')}\n> **Reason:** {unmodified.get('reason')}",
            )
            embed.add_field(
                name="After",
                value=f"> **ID:** `{L.get('LoaID')}`\n> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(L.get('start_time').timestamp())}>\n> **End Date:** {await Duration(L, 'end_time')}\n> **Reason:** {L.get('reason')}",
            )

        if action == "ForceEnd":
            embed.title = "Leave Ended"
            embed.description = f"> **ID:** `{L.get('LoaID')}`\n> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(L.get('start_time').timestamp())}>\n> **End Date:** {await Duration(L, 'end_time')}\n> **Reason:** {L.get('reason')}"
        try:
            await CH.send(embed=embed)
        except (discord.HTTPException, discord.Forbidden):
            return

    @commands.Cog.listener()
    async def on_leave_ext_request(self, _id: ObjectId):
        L = await self.client.db["ExtRequests"].find_one({"_id": _id})
        if L is None:
            return
        G = self.client.get_guild(L.get("guild"))
        if not G:
            return
        C = await self.client.db["Config"].find_one({"_id": G.id})
        if not C:
            return
        if not C.get("LOA", None):
            return
        if not C.get("LOA", {}).get("channel", None):
            return
        try:
            CH = await G.fetch_channel(int(C.get("LOA", {}).get("channel", 0)))
        except (discord.NotFound, discord.HTTPException):
            return
        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="Extension Request",
            value=f"> **User:** <@{L.get('user')}>\n> **Extension:** {L.get('durationstr')}\n> **Reason:** {L.get('reason')}",
        )
        embed.set_author(
            name=f"@{L.get('ExtendedUser', {}).get('name')}",
            icon_url=L.get("ExtendedUser", {}).get("thumbnail"),
        )
        embed.set_thumbnail(url=L.get("ExtendedUser", {}).get("thumbnail"))
        embed.set_footer(text=L.get("LoaID"))
        try:
            CM = await CH.send(embed=embed, view=ExtRequest())
        except (discord.HTTPException, discord.Forbidden):
            return
        await self.client.db["ExtRequests"].update_one(
            {"_id": L.get("_id")},
            {
                "$set": {
                    "messageid": CM.id,
                    "channel_id": CH.id,
                }
            },
        )

    @commands.Cog.listener()
    async def on_leave_request_cancel(self, _id: ObjectId):
        L = await self.client.db["loa"].find_one({"_id": _id})
        await self.client.db["loa"].delete_one({"_id": _id})
        if L is None:
            return
        G = self.client.get_guild(L.get("guild_id"))
        if not G:
            return
        C = await self.client.db["Config"].find_one({"_id": G.id})
        if not C:
            return
        if not C.get("LOA", None):
            return
        if not C.get("LOA", {}).get("channel", None):
            return
        try:
            CH = await G.fetch_channel(int(C.get("LOA", {}).get("channel", 0)))
        except (discord.NotFound, discord.HTTPException):
            return
        try:
            CM = await CH.fetch_message(L.get("messageid"))
            await CM.delete()
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            return

    @commands.Cog.listener()
    async def on_leave_ext_update(
        self, _id: ObjectId, status: str, author: discord.User
    ):
        L = await self.client.db["ExtRequests"].find_one({"_id": _id})
        if L is None:
            return
        LOA = await self.client.db["loa"].find_one({"LoaID": L.get("LoaID")})
        if LOA is None:
            return
        G = self.client.get_guild(L.get("guild"))
        if not G:
            return
        C = await self.client.db["Config"].find_one({"_id": G.id})
        if not C:
            return
        if not C.get("LOA", None):
            return
        if not C.get("LOA", {}).get("channel", None):
            return
        try:
            CH = await G.fetch_channel(int(C.get("LOA", {}).get("channel", 0)))
        except (discord.NotFound, discord.HTTPException):
            return

        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="Extension Request",
            value=f"> **User:** <@{L.get('user')}>\n> **Extension:** {L.get('durationstr')}\n> **Reason:** {L.get('reason')}",
        )
        embed.set_author(
            name=f"@{L.get('ExtendedUser', {}).get('name')}",
            icon_url=L.get("ExtendedUser", {}).get("thumbnail"),
        )
        embed.set_thumbnail(url=L.get("ExtendedUser", {}).get("thumbnail"))
        embed.set_footer(text=L.get("LoaID"))
        view = None
        try:
            member = await G.fetch_member(L.get("user"))
        except (discord.NotFound, discord.HTTPException):
            member = None
        if status == "Accepted":
            view = discord.ui.View().add_item(
                discord.ui.Button(
                    label="Accepted", style=discord.ButtonStyle.green, disabled=True
                )
            )
            await self.client.db["loa"].update_one(
                {
                    "_id": ObjectId(LOA.get("_id")),
                },
                {
                    "$set": {
                        "AddedTime.Time": LOA.get("AddedTime", {}).get("Time", 0)
                        + L.get("duration", 0),
                        "AddedTime.Reason": L.get("reason"),
                        "AddedTime.Log": LOA.get("AddedTime", {}).get("Log", [])
                        + [
                            {
                                "time": datetime.now(),
                                "duration": L.get("duration", 0),
                                "user": author.id,
                                "reason": L.get("reason"),
                            }
                        ],
                    }
                },
            )
            await self.client.db["ExtRequests"].update_one(
                {"_id": L.get("_id")},
                {
                    "$set": {
                        "Accepted": {
                            "user": author.id,
                            "time": datetime.now(),
                            "reason": L.get("reason"),
                        },
                        "status": "Accepted",
                    }
                },
            )
            embed.color = discord.Color.brand_green()
            embed.set_footer(
                text=f"{L.get('LoaID') } | Accepted By @{author.name}",
                icon_url=author.display_avatar,
            )
            if member:
                try:
                    await member.send(
                        embed=discord.Embed(
                            color=discord.Color.brand_green(),
                        )
                        .set_author(name="Extension Accepted")
                        .add_field(
                            name="LOA",
                            value=f"> **User:** <@{L.get('user')}>\n> **Extension:** {L.get('durationstr')}\n> **Reason:** {L.get('reason')}",
                        )
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
        elif status == "Declined":
            view = discord.ui.View().add_item(
                discord.ui.Button(
                    label="Declined", style=discord.ButtonStyle.red, disabled=True
                )
            )
            embed.color = discord.Color.brand_red()
            embed.set_footer(
                text=f"{L.get('LoaID') } | Declined By @{author.name}",
                icon_url=author.display_avatar,
            )
            await self.client.db["ExtRequests"].update_one(
                {"_id": L.get("_id")},
                {
                    "$set": {
                        "Declined": {
                            "user": author.id,
                            "time": datetime.now(),
                            "reason": L.get("reason"),
                        },
                        "status": "Declined",
                    }
                },
            )
            if member:
                try:

                    await member.send(
                        embed=discord.Embed(
                            color=discord.Color.brand_red(),
                        )
                        .set_author(name="Extension Declined")
                        .add_field(
                            name="LOA",
                            value=f"> **User:** <@{L.get('user')}>\n> **Extension:** {L.get('durationstr')}\n> **Reason:** {L.get('reason')}",
                        )
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

        try:
            CM = await CH.fetch_message(L.get("messageid"))
            await CM.edit(embed=embed, view=view)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            return

    @commands.Cog.listener()
    async def on_leave_create(self, _id: ObjectId):
        L = await self.client.db["loa"].find_one({"_id": _id})
        if L is None:
            return
        G = self.client.get_guild(L.get("guild_id"))
        if not G:
            return
        C = await self.client.db["Config"].find_one({"_id": G.id})
        if not C:
            return
        if not C.get("LOA", None):
            return
        if not C.get("LOA", {}).get("channel", None):
            return
        try:
            CH = await G.fetch_channel(int(C.get("LOA", {}).get("channel", 0)))
        except (discord.NotFound, discord.HTTPException):
            return

        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.add_field(
            name="Leave Created",
            value=f"> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(L.get('start_time').timestamp())}>\n> **End Date:** <t:{int(L.get('end_time').timestamp())}>\n> **Reason:** {L.get('reason')}",
        )
        embed.set_author(
            name=f"@{L.get('ExtendedUser', {}).get('name')}",
            icon_url=L.get("ExtendedUser", {}).get("thumbnail"),
        )
        embed.set_thumbnail(url=L.get("ExtendedUser", {}).get("thumbnail"))
        embed.set_footer(
            text=f"{L.get('LoaID')} | Created by @{L.get('Created').get('name')}",
            icon_url=L.get("Created").get("thumbnail"),
        )

        try:
            CM = await CH.send(embed=embed)
        except (discord.HTTPException, discord.Forbidden):
            return

        await self.client.db["loa"].update_one(
            {"_id": L.get("_id")},
            {
                "$set": {
                    "messageid": CM.id,
                    "channel_id": CH.id,
                }
            },
        )

    @commands.Cog.listener()
    async def on_leave_update(self, _id: ObjectId, status: str, author: discord.User):
        L = await self.client.db["loa"].find_one({"_id": _id})
        if L is None:
            return
        G = self.client.get_guild(L.get("guild_id"))
        if not G:
            return
        C = await self.client.db["Config"].find_one({"_id": G.id})
        if not C:
            return
        if not C.get("LOA", None):
            return
        if not C.get("LOA", {}).get("channel", None):
            return
        try:
            CH = await G.fetch_channel(int(C.get("LOA", {}).get("channel", 0)))
        except (discord.NotFound, discord.HTTPException):
            return

        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.set_author(
            name=f"@{L.get('ExtendedUser', {}).get('name')}",
            icon_url=L.get("ExtendedUser", {}).get("thumbnail"),
        )
        embed.set_thumbnail(url=L.get("ExtendedUser", {}).get("thumbnail"))

        embed.set_footer(text=L.get("LoaID"))
        view = None
        try:
            member = await G.fetch_member(L.get("user"))
        except (discord.HTTPException, discord.NotFound):
            member = None
        if status == "Accepted":
            view = discord.ui.View().add_item(
                discord.ui.Button(
                    label="Accepted", style=discord.ButtonStyle.green, disabled=True
                )
            )
            embed.add_field(
                name="Leave Accepted",
                value=f"> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(L.get('start_time').timestamp())}>\n> **End Date:** <t:{int(L.get('end_time').timestamp())}>\n> **Reason:** {L.get('reason')}",
            )
            embed.color = discord.Color.brand_green()
            embed.set_footer(
                text=f"{L.get('LoaID') } | Accepted By @{author.name}",
                icon_url=author.display_avatar,
            )
            if member:
                if not L.get("scheduled", False):
                    if C.get("LOA", {}).get("role", None):
                        try:
                            role = G.get_role(int(C.get("LOA", {}).get("role", 0)))

                            if role and member:
                                await member.add_roles(role, reason=f"Leave Accepted initiated by {author.name}")
                        except (discord.NotFound, discord.HTTPException):
                            pass
                try:
                    await member.send(
                        embed=discord.Embed(
                            color=discord.Color.brand_green(),
                        )
                        .set_author(name="Leave Accepted")
                        .add_field(
                            name="LOA",
                            value=f"> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(L.get('start_time').timestamp())}>\n> **End Date:** <t:{int(L.get('end_time').timestamp())}>\n> **Reason:** {L.get('reason')}",
                        )
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
        elif status == "Declined":

            view = discord.ui.View().add_item(
                discord.ui.Button(
                    label="Declined", style=discord.ButtonStyle.red, disabled=True
                )
            )
            embed.add_field(
                name="Leave",
                value=f"> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(L.get('start_time').timestamp())}>\n> **End Date:** <t:{int(L.get('end_time').timestamp())}>\n> **Reason:** {L.get('reason')}",
                inline=False,
            )
            embed.add_field(
                name="Denied",
                value=f"> **Reason:** {L.get('Declined',{}).get('reason', 'N/A')}",
                inline=False,
            )
            embed.color = discord.Color.brand_red()
            embed.set_footer(
                text=f"{L.get('LoaID') } | Declined By @{author.name}",
                icon_url=author.display_avatar,
            )
            if member:
                await member.send(
                    embed=discord.Embed(
                        color=discord.Color.brand_red(),
                    )
                    .set_author(name="Leave Declined")
                    .add_field(
                        name="Leave",
                        value=f"> **User:** <@{L.get('user')}>\n> **Start Date:** <t:{int(L.get('start_time').timestamp())}>\n> **End Date:** <t:{int(L.get('end_time').timestamp())}>\n> **Reason:** {L.get('reason')}",
                        inline=False,
                    )
                    .add_field(
                        name="Denied",
                        value=f"> **Reason:** {L.get('Declined',{}).get('reason', 'N/A')}",
                        inline=False,
                    )
                )

        try:
            CM = await CH.fetch_message(L.get("messageid"))
            await CM.edit(embed=embed, view=view)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            return


class DenialReason(discord.ui.Modal, title="Leave Denial Reason"):
    def __init__(self):
        super().__init__()
        self.reason = discord.ui.TextInput(
            label="Reason",
            style=discord.TextStyle.long,
            placeholder="Enter the reason for denial",
            required=True,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        LOA = await interaction.client.db["loa"].find_one(
            {"messageid": interaction.message.id}
        )
        if LOA is None:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("This isn't a valid LOA Request"),
                ephemeral=True,
            )
            return
        await interaction.client.db["loa"].update_one(
            {
                "messageid": interaction.message.id,
                "guild_id": interaction.guild.id,
            },
            {
                "$set": {
                    "Declined": {
                        "user": interaction.user.id,
                        "time": datetime.now(),
                        "reason": self.reason.value,
                    },
                    "active": False,
                    "request": False,
                }
            },
        )
        interaction.client.dispatch(
            "leave_update",
            LOA.get("_id"),
            "Declined",
            interaction.user,
        )


class ExtRequest(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Accept", style=discord.ButtonStyle.green, row=0, custom_id="accept2"
    )
    async def Accept(self, interaction: discord.Interaction, _):
        if not await has_admin_role(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        LOA = await interaction.client.db["ExtRequests"].find_one(
            {"messageid": interaction.message.id}
        )
        if LOA is None:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("This isn't a valid Extension Request"),
                ephemeral=True,
            )
            return
        interaction.client.dispatch(
            "leave_ext_update",
            LOA.get("_id"),
            "Accepted",
            interaction.user,
        )

    @discord.ui.button(
        label="Decline", style=discord.ButtonStyle.red, row=0, custom_id="decline2"
    )
    async def Decline(self, interaction: discord.Interaction, _):
        if not await has_admin_role(interaction):
            return
        LOA = await interaction.client.db["ExtRequests"].find_one(
            {"messageid": interaction.message.id}
        )
        if LOA is None:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("This isn't a valid Extension Request"),
                ephemeral=True,
            )
            return
        interaction.client.dispatch(
            "leave_ext_update",
            LOA.get("_id"),
            "Declined",
            interaction.user,
        )


class PendingActions(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Accept", style=discord.ButtonStyle.green, row=0, custom_id="accept"
    )
    async def Accept(self, interaction: discord.Interaction, _):
        await interaction.response.defer(ephemeral=True)
        if not await has_admin_role(interaction):
            return
        LOA = await interaction.client.db["loa"].find_one(
            {"messageid": interaction.message.id}
        )
        if LOA is None:
            await interaction.followup.send(
                embed=HelpEmbeds.CustomError("This isn't a valid LOA Request"),
                ephemeral=True,
            )
            return

        Z = await interaction.client.db["loa"].update_one(
            {
                "messageid": interaction.message.id,
                "guild_id": interaction.guild.id,
            },
            {
                "$set": {
                    "Accepted": {
                        "user": interaction.user.id,
                        "time": datetime.now(),
                    },
                    "active": True if LOA.get("scheduled", False) == False else False,
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

    @discord.ui.button(
        label="Decline", style=discord.ButtonStyle.red, row=0, custom_id="decline"
    )
    async def Decline(self, interaction: discord.Interaction, _):
        if not await has_admin_role(interaction):
            return
        await interaction.response.send_modal(DenialReason())


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_leave(client))
