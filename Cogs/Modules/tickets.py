from discord.ext import commands
import discord
from datetime import datetime, timedelta
from utils.emojis import *
from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed

import pymongo

import typing
import logging
from Cogs.Events.on_ticket import TicketPermissions
from discord import app_commands
import string
import random
from utils.permissions import has_admin_role, check_admin_and_staff, has_staff_role
import asyncio

logger = logging.getLogger(__name__)
from utils.Module import ModuleCheck
from utils.HelpEmbeds import ModuleNotEnabled, Support, ModuleNotSetup, BotNotConfigured
from utils.autocompletes import CloseReason
from utils.format import ordinal, PaginatorButtons


async def AccessControl(interaction: discord.Interaction, Panel: dict):
    if not Panel:
        return True
    if not Panel.get("AccessControl"):
        return True
    for role in Panel.get("AccessControl"):
        if role in [r.id for r in interaction.user.roles]:
            return True


class ButtonHandler(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def add_buttons(self, buttons: typing.Union[list, dict]):
        if isinstance(buttons, list):
            for button in buttons:
                if isinstance(button, dict):
                    self.add_item(Button(button))

        elif isinstance(buttons, dict):
            self.add_item(Button(buttons))


class TicketForm(discord.ui.Modal):
    def __init__(self, questions: list, data: dict):
        super().__init__(timeout=None, title="Ticket Form")
        self.questions = {}
        for question in questions:
            label = question.get("label")
            TextInput = discord.ui.TextInput(
                placeholder=question.get("placeholder"),
                min_length=question.get("min", 1),
                max_length=question.get("max", 1000),
                label=label,
                required=question.get("required", False),
                default=question.get("default", None),
            )
            self.questions[label] = question.get("question", label)
            self.add_item(TextInput)
        self.data = data

    async def on_submit(self, interaction: discord.Interaction):
        responses = {
            self.questions[item.label]: item.value
            for item in self.children
            if isinstance(item, discord.ui.TextInput)
        }

        self.data["responses"] = responses
        t = await interaction.client.db["Tickets"].insert_one(self.data)
        interaction.client.dispatch(
            "pticket_open", t.inserted_id, self.data.get("panel")
        )

        await interaction.response.defer()
        TMSG: discord.Message = await interaction.followup.send(
            content=f"<a:Loading:1167074303905386587> **{interaction.user.display_name}**, hold on while I open the ticket.",
            ephemeral=True,
        )

        await TicketError(interaction, t, TMSG)


class Button(discord.ui.Button):
    def __init__(self, button: dict):
        custom_id = button.get("custom_id")
        Styles = {
            "Grey": discord.ButtonStyle.grey,
            "Blurple": discord.ButtonStyle.blurple,
            "Green": discord.ButtonStyle.green,
            "Red": discord.ButtonStyle.red,
            "Secondary": discord.ButtonStyle.secondary,
        }

        style = Styles.get(button.get("style"), discord.ButtonStyle.secondary)
        emoji = button.get("emoji")
        if emoji:
            emoji = discord.PartialEmoji.from_str(emoji)
            if emoji.id is None:
                emoji = None
            else:
                emoji = button.get("emoji")

        super().__init__(
            label=button.get("label"),
            style=style,
            emoji=emoji,
            url=button.get("url"),
            custom_id=custom_id,
        )
        self.custom_id = custom_id

    async def callback(self, interaction: discord.Interaction):

        AlreadyOpen = await interaction.client.db["Tickets"].count_documents(
            {
                "UserID": interaction.user.id,
                "GuildID": interaction.guild.id,
                "closed": None,
                "panel": {"$exists": True},
            }
        )
        Blacklisted = await interaction.client.db["Ticket Blacklists"].find_one(
            {"user": interaction.user.id, "guild": interaction.guild.id}
        )
        if Blacklisted:
            return await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name}**, you're blacklisted from this servers tickets.",
                ephemeral=True,
            )
        Cli = await interaction.guild.fetch_member(interaction.client.user.id)
        if not Cli.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name}**, I don't have permission to manage channels.",
                ephemeral=True,
            )
        if AlreadyOpen > 5:
            return await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name}**, you already have a max of 5 tickets open! If this is a mistake contact a developer.\n-# If this is a mistake (actually a mistake) press the debug button. (Abusing it'll can lead to a blacklist)",
                ephemeral=True,
                view=Debug(),
            )

        TPanel = None
        panel = (
            await interaction.client.db["Panels"]
            .find({"guild": interaction.guild.id})
            .to_list(length=None)
        )
        for p in panel:
            button = p.get("Button")
            if button:
                if button.get("custom_id") == self.custom_id:
                    TPanel = p
                    break
        if not await AccessControl(interaction, TPanel):
            return await interaction.response.send_message(
                content=f"{no} **{interaction.user.display_name}**, you don't have permission to use this panel.",
                ephemeral=True,
            )

        Dict = {
            "_id": "".join(random.choices(string.ascii_letters + string.digits, k=10)),
            "GuildID": interaction.guild.id,
            "UserID": interaction.user.id,
            "opened": interaction.created_at.timestamp(),
            "closed": None,
            "claimed": {"claimer": None, "claimedAt": None},
            "transcript": [],
            "type": self.type,
            "panel": TPanel.get("name"),
            "panel_id": self.custom_id,
            "lastMessageSent": datetime.utcnow(),
        }
        if TPanel.get("Questions") and len(TPanel.get("Questions")) > 0:
            return await interaction.response.send_modal(
                TicketForm(TPanel.get("Questions"), Dict)
            )
        await interaction.response.defer()
        if TPanel:
            t = await interaction.client.db["Tickets"].insert_one(Dict)
            interaction.client.dispatch(
                "pticket_open", t.inserted_id, TPanel.get("name")
            )
            TMSG: discord.Message = await interaction.followup.send(
                content=f"<a:Loading:1167074303905386587> **{interaction.user.display_name}**, hold on while I open the ticket.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                content=f"{crisis} **{interaction.user.display_name}**, no matching panel found for the given custom ID.",
                ephemeral=True,
                view=Debug(),
            )
        await TicketError(interaction, t, TMSG)


async def TicketError(interaction: discord.Interaction, t: dict, tmsg: discord.Message):
    attempts = 10
    while True:
        attempts -= 1
        await asyncio.sleep(3)
        result = await interaction.client.db["Tickets"].find_one({"_id": t.inserted_id})
        if not result:
            continue

        if result.get("error"):
            embed = discord.Embed(
                description=f"An error occured while trying to open the ticket.\n```{result.get('error', {}).get('message')}```",
                color=discord.Color.red(),
            )
            try:
                await interaction.followup.edit_message(
                    tmsg.id,
                    content=None,
                    embed=embed,
                    view=Support(),
                )
                await interaction.client.db["Tickets"].delete_one(
                    {"_id": t.inserted_id}
                )
                break
            except discord.NotFound:

                pass
        if result.get("ChannelID", None):
            try:
                url = f"https://discord.com/channels/{interaction.guild.id}/{result.get('ChannelID')}"
                await interaction.followup.edit_message(
                    tmsg.id,
                    content=f"{tick} **{interaction.user.display_name}**, your ticket has been successfully opened!",
                    view=discord.ui.View().add_item(
                        discord.ui.Button(
                            label="Jump To", style=discord.ButtonStyle.link, url=url
                        )
                    ),
                )
                break
            except discord.NotFound:
                pass
        if attempts > 20:
            await interaction.followup.edit_message(
                tmsg.id,
                content=f"{crisis} **{interaction.user.display_name}**, the ticket didn't open.",
                view=Support(),
            )
            break


class Debug(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Debug Issue", style=discord.ButtonStyle.red)
    async def debug(self, interaction: discord.Interaction, button: discord.ui.Button):
        R = await interaction.client.db["Tickets"].find_one(
            {"UserID": interaction.user.id, "closed": None}
        )
        if not R:
            return await interaction.response.send_message(
                f"{no} **{interaction.user.display_name}**, no open ticket found to debug.",
                ephemeral=True,
            )

        view = Debug()
        view.debug.disabled = True
        await interaction.response.edit_message(
            view=view,
            content=f"{tick} **{interaction.user.display_name}**, your ticket has been purged.",
        )
        interaction.client.dispatch(
            "pticket_close",
            R.get("_id"),
            "Ticket Opener hit the debug button",
            interaction.user,
        )
        await asyncio.sleep(10)
        New = await interaction.client.db["Tickets"].find_one(
            {"UserID": interaction.user.id, "closed": None}
        )
        if New:
            logger.debug(f"[Debug Issue] Ticket {R.get('_id')} has been purged.")
            await interaction.client.db["Tickets"].delete_one({"_id": R.get("_id")})


class TicketsPub(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    tickets = app_commands.Group(name="ticket", description="Ticket Commands")

    async def PanelAutoComplete(
        ctx: commands.Context, interaction: discord.Interaction, current: str
    ) -> typing.List[app_commands.Choice[str]]:
        try:
            choices = []
            P = (
                await interaction.client.db["Panels"]
                .find(
                    {"guild": interaction.guild.id, "type": {"$ne": "Welcome Message"}}
                )
                .to_list(length=None)
            )
            for Panel in P:
                choices.append(
                    app_commands.Choice(
                        name=f"{Panel.get('name')} ({'Single' if Panel.get('type') == 'single' else 'Multi'})",
                        value=Panel.get("name"),
                    )
                )
                if len(choices) == 25:
                    break
            return choices

        except (ValueError, discord.HTTPException, discord.NotFound, TypeError):
            return [app_commands.Choice(name="Error", value="Error")]

    @tickets.command(description="Send the panel to a channel.")
    @app_commands.autocomplete(panel=PanelAutoComplete)
    async def panel(self, interaction: discord.Interaction, panel: str):
        await interaction.response.defer()

        if not await has_admin_role(interaction):
            return
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        Panel = await interaction.client.db["Panels"].find_one(
            {
                "guild": interaction.guild.id,
                "name": panel,
                "type": {"$ne": "Welcome Message"},
            }
        )

        if not Panel:
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name},** this panel does not exist!",
                ephemeral=True,
            )

        P = Panel.get("Panel")
        DefaultEmbed = False
        embed = None
        content = None

        if P and P.get("embed"):
            embed = await DisplayEmbed(P)
            content = P.get("content", None)
        elif not P or not P.get("content"):
            embed = discord.Embed(
                description="By clicking a button below, you can open a ticket.",
                color=discord.Color.blurple(),
            ).set_author(
                name=f"{Panel.get('name')}",
                icon_url=(
                    interaction.guild.icon.url if interaction.guild.icon else None
                ),
            )

        buttons = []
        if Panel.get("type") == "multi":
            if not Panel.get("Panels"):
                return await interaction.followup.send(
                    f"{no} **{interaction.user.display_name},** this multi-panel doesn't have any sub-panels.",
                    ephemeral=True,
                )
            for panel_name in Panel.get("Panels"):
                sub = await interaction.client.db["Panels"].find_one(
                    {
                        "guild": interaction.guild.id,
                        "name": panel_name,
                        "type": "single",
                    }
                )
                if not sub:
                    continue
                sub = sub.get("Button")
                if not sub:
                    continue

                buttons.append(
                    {
                        "custom_id": sub.get("custom_id"),
                        "label": sub.get("label"),
                        "style": sub.get("style"),
                        "emoji": sub.get("emoji"),
                    }
                )
                view = ButtonHandler()
                view.add_buttons(buttons)
        else:
            view = ButtonHandler()
            view.add_buttons(Panel.get("Button"))

        if Panel.get("MsgID") and Panel.get("ChannelID"):
            try:
                channel = interaction.guild.get_channel(Panel.get("ChannelID"))
                if channel:
                    last = await channel.fetch_message(Panel.get("MsgID"))
                    await last.delete()
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                pass

        if not P:
            P = {}
        if (
            not P.get("embed")
            or interaction.guild.id == 1092976553752789054
            or not embed
        ):
            if not DefaultEmbed and content:
                embed = None
        try:
            msg = await interaction.channel.send(
                embed=embed,
                view=view,
                content=Panel.get("Panel", {}).get("content", ""),
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name},** I don't have permission to send messages in this channel.",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            C = await self.client.db["Config"].find_one(
                {"_id": interaction.guild.id, "Features": {"$in": ["DEBUG"]}}
            )
            Debug = False
            if C:
                Debug = True

            embed = discord.Embed(
                description=f"```{e}```", color=discord.Color.brand_red()
            )
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name},** I failed to send the panel. Make sure the embed/message is formed correctly.",
                ephemeral=True,
                embed=embed if Debug else None,
            )
        await interaction.followup.send(
            f"{tick} **{interaction.user.display_name},** I've sent the panel.",
            ephemeral=True,
        )

        await interaction.client.db["Panels"].update_one(
            {"guild": interaction.guild.id, "name": panel},
            {"$set": {"MsgID": msg.id, "ChannelID": interaction.channel.id}},
        )

    @tickets.command(description="Rename a ticket.")
    async def rename(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        if not await TicketPermissions(interaction):
            return await interaction.followup.send(
                content=f"{no} You don't have permission to use this command."
            )
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        Result = await interaction.client.db["Tickets"].find_one(
            {"ChannelID": interaction.channel.id}
        )
        if not Result:
            return await interaction.followup.send(
                content=f"{no} This isn't a ticket channel."
            )
        await interaction.client.db["Tickets"].update_one(
            {"ChannelID": interaction.channel.id}, {"$set": {"name": name}}
        )
        try:
            await interaction.channel.edit(name=name)
        except discord.Forbidden:
            return await interaction.followup.send(
                content=f"{no} I don't have permission to rename this ticket."
            )
        await interaction.followup.send(
            content=f"{tick} Successfully renamed ticket to {name}"
        )

    @tickets.command(description="Close a ticket.")
    @app_commands.autocomplete(reason=CloseReason)
    async def close(self, interaction: discord.Interaction, reason: str = None):
        await interaction.response.defer()
        if not await TicketPermissions(interaction):
            return await interaction.followup.send(
                content=f"{no} You don't have permission to use this command."
            )
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        Result = await interaction.client.db["Tickets"].find_one(
            {"ChannelID": interaction.channel.id}
        )
        if not Result:
            return await interaction.followup.send(
                content=f"{no} This isn't a ticket channel."
            )
        self.client.dispatch(
            "pticket_close", Result.get("_id"), reason, interaction.user
        )
        await interaction.followup.send(content=f"{tick} Ticket closed.")

    @tickets.command(description="Blacklist a user from the ticket system.")
    async def blacklist(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        if not await has_admin_role(interaction):
            return
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        await interaction.followup.send(
            content=f"{tick} **{interaction.user.display_name},** you've blacklisted **@{user.display_name}** from the ticket system!"
        )
        await interaction.client.db["Ticket Blacklists"].insert_one(
            {"user": user.id, "guild": interaction.guild.id}
        )

    @tickets.command(description="Unblacklist a user from the ticket system.")
    async def unblacklist(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()

        if not await has_admin_role(interaction):
            return
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        await interaction.followup.send(
            content=f"{tick} **{interaction.user.display_name},** you've unblacklisted **@{user.display_name}** from the ticket system!"
        )
        await interaction.client.db["Ticket Blacklists"].delete_one(
            {"user": user.id, "guild": interaction.guild.id}
        )

    def GetPlace(self, data, user):
        data = sorted(
            data,
            key=lambda x: int(x.get("ClaimedTickets", 0)),
            reverse=True,
        )
        for i, user_data in enumerate(data):
            if user_data.get("UserID") == user.id:
                return i + 1
        return None

    @tickets.command(description="View the claimed tickets leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await has_staff_role(interaction):
            return
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )

        msg = await interaction.followup.send(
            embed=discord.Embed(
                description="<a:astroloading:1245681595546079285>",
                color=discord.Color.dark_embed(),
            )
        )

        ticket_users = (
            await interaction.client.db["Ticket Quota"]
            .find({"GuildID": interaction.guild.id})
            .sort("ClaimedTickets", pymongo.DESCENDING)
            .to_list(length=750)
        )

        if not ticket_users:
            return await msg.edit(
                content=f"{no} **{interaction.user.display_name},** there haven't been any tickets claimed yet.",
                embed=None,
            )

        Config = await self.client.config.find_one({"_id": interaction.guild.id})
        if not Config or not Config.get("Tickets"):
            return await msg.edit(embed=BotNotConfigured(), view=Support())

        quota = int(Config.get("Tickets", {}).get("quota", 0))
        YouProgress = next(
            (
                user
                for user in ticket_users
                if user.get("UserID") == interaction.user.id
            ),
            {},
        )
        YourPlace = self.GetPlace(ticket_users, interaction.user)
        YourTickets = YouProgress.get("ClaimedTickets", 0)
        YourLOA = any(
            role.id == Config.get("LOA", {}).get("role")
            for role in interaction.user.roles
        )
        YourEmoji = (
            "`LOA`" if YourLOA else ("Met" if YourTickets >= quota else "Not Met")
        )

        Description = ""
        pages = []
        i = 1

        for staff in ticket_users:
            member = interaction.guild.get_member(staff.get("UserID"))
            if not member:
                try:
                    member = await interaction.guild.fetch_member(staff.get("UserID"))
                except (discord.HTTPException, discord.NotFound):
                    continue

            if not await check_admin_and_staff(interaction.guild, member):
                continue

            OnLOA = any(
                role.id == Config.get("LOA", {}).get("role") for role in member.roles
            )
            emoji = (
                "`LOA`"
                if OnLOA
                else ("Met" if staff.get("ClaimedTickets", 0) >= quota else "Not Met")
            )

            Description += f"* `{i}` {member.display_name} • {staff.get('ClaimedTickets', 0)} tickets\n"
            if quota != 0:
                Description += f"{replybottom} **Status:** {emoji}\n"
                Description += "\n"

            if i % 9 == 0:
                embed = discord.Embed(
                    title="Ticket Leaderboard",
                    description=Description,
                    color=discord.Color.dark_embed(),
                )
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(
                    name=interaction.guild.name, icon_url=interaction.guild.icon
                )
                pages.append(embed)
                Description = ""

            i += 1

        if Description.strip():
            embed = discord.Embed(
                title="Ticket Leaderboard",
                description=Description,
                color=discord.Color.dark_embed(),
            )
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(
                name=interaction.guild.name, icon_url=interaction.guild.icon
            )
            pages.append(embed)

        if YouProgress:
            for embed in pages:
                embed.add_field(
                    name="<:tablerprogressbolt:1330500442551091210> Your Progress",
                    value=(
                        f"> **Tickets:** {YourTickets} tickets\n"
                        f"> **Met:** {YourEmoji if YourEmoji else 'N/A'}\n"
                        f"> **Place:** {ordinal(YourPlace) if YourPlace else 'N/A'}"
                    ),
                )

        paginator = await PaginatorButtons()
        if pages:
            await paginator.start(interaction, pages=pages[:45], msg=msg)
        else:
            await msg.edit(
                content=f"{no} **{interaction.user.display_name},** there are no pages to display.",
                embed=None,
            )

    @tickets.command(description="Request to close a ticket.")
    @app_commands.autocomplete(reason=CloseReason)
    async def closerequest(self, interaction: discord.Interaction, reason: str = None):
        await interaction.response.defer()
        if not await TicketPermissions(interaction):
            return await interaction.followup.send(
                content=f"{no} You don't have permission to use this command."
            )
        Result = await interaction.client.db["Tickets"].find_one(
            {"ChannelID": interaction.channel.id}
        )

        if not Result:
            return await interaction.followup.send(
                content=f"{no} This isn't a ticket channel."
            )
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        p = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "name": Result.get("panel")}
        )
        try:
            User = await interaction.guild.fetch_member(Result.get("UserID"))
        except (discord.NotFound, discord.HTTPException):
            return await interaction.followup.send(
                content=f"{no} I can't find the user that opened this ticket."
            )
        CS = p.get("Close Request", {})
        embed = None
        if CS.get("embed", None):
            replacements = {
                "{author.mention}": User.mention,
                "{author.name}": User.name,
                "{author.created_at.relative}": f"<t:{int(User.created_at.timestamp())}:R>",
                "{author.created_at.absolute}": f"<t:{int(User.created_at.timestamp())}:F>",
                "{author.joined_at.relative}": f"<t:{int(User.joined_at.timestamp())}:R>",
                "{author.joined_at.absolute}": f"<t:{int(User.joined_at.timestamp())}:F>",
                "{author.id}": str(User.id),
                "{author.avatar}": str(User.avatar.url),
                "{author.display_name}": User.display_name,
                "{guild.name}": interaction.guild.name,
                "{guild.id}": str(interaction.guild.id),
                "{time.relative}": f"<t:{int(datetime.utcnow().timestamp())}:R>",
                "{time.absolute}": f"<t:{int(datetime.utcnow().timestamp())}:F>",
                "{ticket.id}": str(Result.get("_id")),
                "{reason}": reason,
            }
            embed = await DisplayEmbed(
                p.get("Close Request", {}), replacements=replacements
            )
        if not embed:
            embed = discord.Embed(
                title="Close Confirmation",
                description=f"This ticket has been requested to be closed by **{interaction.user.display_name}**. If you have no further questions, please click the button below to close the ticket.\n```\n{reason}\n```",
                color=discord.Color.green(),
            )

        await interaction.followup.send(
            embed=embed, view=CloseRequest(User, reason), content=User.mention
        )

    @tickets.command(description="Add a user to a ticket.")
    async def add(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        if not await TicketPermissions(interaction):
            return await interaction.followup.send(
                content=f"{no} You don't have permission to use this command."
            )
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        Result = await interaction.client.db["Tickets"].find_one(
            {"ChannelID": interaction.channel.id}
        )
        if not Result:
            return await interaction.followup.send(
                content=f"{no} This isn't a ticket channel."
            )
        await interaction.channel.set_permissions(
            user,
            read_messages=True,
            send_messages=True,
            add_reactions=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            external_emojis=True,
            connect=True,
            speak=True,
        )
        await interaction.followup.send(
            content=f"{tick} **{interaction.user.display_name},** you've added **@{user.display_name}** to the ticket!"
        )

    @tickets.command(description="Remove a user from a ticket.")
    async def remove(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        if not await TicketPermissions(interaction):
            return await interaction.followup.send(
                content=f"{no} You don't have permission to use this command."
            )
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        Result = await interaction.client.db["Tickets"].find_one(
            {"ChannelID": interaction.channel.id}
        )
        if not Result:
            return await interaction.followup.send(
                content=f"{no} This isn't a ticket channel."
            )
        try:
            await interaction.channel.set_permissions(user, overwrite=None)
        except discord.Forbidden:
            return await interaction.followup.send(
                content=f"{no} I don't have permission to remove this user from the ticket."
            )
        await interaction.followup.send(
            content=f"{tick} **{interaction.user.display_name},** you've removed **@{user.display_name}** to the ticket!"
        )

    @tickets.command(description="Claim a ticket.")
    async def claim(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not await TicketPermissions(interaction):
            return await interaction.followup.send(
                content=f"{no} You don't have permission to use this command."
            )
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        Result = await interaction.client.db["Tickets"].find_one(
            {"ChannelID": interaction.channel.id}
        )
        if not Result:
            return await interaction.followup.send(
                content=f"{no} This isn't a ticket channel."
            )
        if Result.get("claimed").get("claimer"):
            return await interaction.followup.send(
                content=f"{no} This ticket is already claimed."
            )
        await interaction.client.db["Tickets"].update_one(
            {"ChannelID": interaction.channel.id},
            {
                "$set": {
                    "claimed": {
                        "claimer": interaction.user.id,
                        "claimedAt": interaction.created_at.timestamp(),
                    }
                }
            },
        )
        await interaction.followup.send(
            content=f"{tick} **{interaction.user.display_name},** you've claimed the ticket!"
        )
        self.client.dispatch("pticket_claim", Result.get("_id"), interaction.user)

    @tickets.command(description="Unclaim a ticket.")
    async def unclaim(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not await TicketPermissions(interaction):
            return await interaction.followup.send(
                content=f"{no} You don't have permission to use this command."
            )
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        Result = await interaction.client.db["Tickets"].find_one(
            {"ChannelID": interaction.channel.id}
        )
        if not Result:
            return await interaction.followup.send(
                content=f"{no} This isn't a ticket channel."
            )
        if not Result.get("claimed").get("claimer"):
            return await interaction.followup.send(
                content=f"{no} This ticket isn't claimed."
            )

        await interaction.client.db["Tickets"].update_one(
            {"ChannelID": interaction.channel.id},
            {"$set": {"claimed": {"claimer": None, "claimedAt": None}}},
        )
        await interaction.followup.send(
            content=f"{tick} **{interaction.user.display_name},** you've unclaimed the ticket!"
        )
        self.client.dispatch("unclaim", Result.get("_id"))

    @tickets.command(description="Toggle automations in the ticket.")
    async def automation(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not await TicketPermissions(interaction):
            return await interaction.followup.send(
                content=f"{no} You don't have permission to use this command."
            )
        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        Result = await interaction.client.db["Tickets"].find_one(
            {"ChannelID": interaction.channel.id}
        )
        if not Result:
            return await interaction.followup.send(
                content=f"{no} This isn't a ticket channel."
            )
        Config = await interaction.client.db["Config"].find_one(
            {"_id": interaction.guild.id}
        )
        if not Config:
            return await interaction.followup.send(
                embed=BotNotConfigured(),
                view=Support(),
                ephemeral=True,
            )
        Panel = await interaction.client.db["Panels"].find_one(
            {"guild": interaction.guild.id, "name": Result.get("panel")}
        )
        if not Panel or not Panel.get("Automations", None):
            return await interaction.followup.send(
                content=f"{no} **{interaction.user.display_name}**, automations aren't enabled for this ticket"
            )

        if Result.get("automations", True):
            await interaction.client.db["Tickets"].update_one(
                {"ChannelID": interaction.channel.id}, {"$set": {"automations": False}}
            )
            await interaction.followup.send(
                content=f"{tick} **{interaction.user.display_name}**, I've paused automations in this ticket.",
            )
        else:
            await interaction.client.db["Tickets"].update_one(
                {"ChannelID": interaction.channel.id}, {"$set": {"automations": True}}
            )
            await interaction.followup.send(
                content=f"{tick} **{interaction.user.display_name}**, I've resumed automations in this ticket.",
            )

    @tickets.command(description="View a users ticket stats.", name="stats")
    async def stats(
        self,
        interaction: discord.Interaction,
        user: discord.Member = None,
        time: str = None,
    ):
        await interaction.response.defer()
        from utils.format import strtotime

        if not await ModuleCheck(interaction.guild.id, "Tickets"):
            return await interaction.followup.send(
                embed=ModuleNotEnabled(),
                view=Support(),
                ephemeral=True,
            )
        if not await has_admin_role(interaction):
            return
        if not user:
            user = interaction.user

        Tickets = (
            await interaction.client.db["Tickets"]
            .find({"GuildID": interaction.guild.id})
            .to_list(length=None)
        )
        if time:
            time = await strtotime(time, back=True)
            Tickets = (
                await interaction.client.db["Tickets"]
                .find(
                    {
                        "GuildID": interaction.guild.id,
                        "opened": {"$gte": time.timestamp()},
                    }
                )
                .to_list(length=None)
            )

        if not Tickets:
            return await interaction.followup.send(
                content=f"{no} **{interaction.user.display_name}**, no tickets found for this user.",
            )

        ClaimedTickets = [
            ticket
            for ticket in Tickets
            if ticket.get("claimed", {}).get("claimer") == user.id
        ]

        TotalResponseTime = timedelta(0)
        TotalClaimed = len(ClaimedTickets)
        TotalMessagesSent = 0
        for Ticket in ClaimedTickets:
            OpenedTime = datetime.fromtimestamp(Ticket["opened"])
            ClaimedTime = datetime.fromtimestamp(Ticket["claimed"]["claimedAt"])
            TotalResponseTime += ClaimedTime - OpenedTime
            Transcript = Ticket.get("transcript", [])
            for entry in Transcript:
                CompactMessages = entry.get("compact", [])
                TotalMessagesSent += sum(
                    1
                    for message in CompactMessages
                    if str(message.get("author_id", {})) == str(user.id)
                )

        AverageResponseTime = (
            TotalResponseTime / TotalClaimed if TotalClaimed > 0 else timedelta(0)
        )

        hours, remainder = divmod(AverageResponseTime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        FormattedResponseTime = ""
        if hours > 0:
            FormattedResponseTime += f"{int(hours)}h "
        if minutes > 0:
            FormattedResponseTime += f"{int(minutes)}m "
        FormattedResponseTime += f"{int(seconds)}s"

        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_author(
            name=f"@{user.name}",
            icon_url=user.display_avatar,
        )
        embed.add_field(
            name="Ticket Stats",
            value=(
                f"> **Claimed Tickets:** {TotalClaimed or 0}\n"
                f'> **Average Response Time:** {FormattedResponseTime.strip() or "0s"}\n'
                f"> **Messages Sent in Tickets:** {TotalMessagesSent or 0}"
            ),
        )
        embed.set_thumbnail(url=user.display_avatar)

        await interaction.followup.send(embed=embed)


class CloseRequest(discord.ui.View):
    def __init__(self, member: discord.Member, reason: str):
        super().__init__(timeout=None)
        self.member = member
        self.reason = reason

    @discord.ui.button(label="Close", style=discord.ButtonStyle.blurple)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.member:
            return await interaction.response.send_message(
                f"{no} You can't close this ticket.", ephemeral=True
            )
        await interaction.response.defer()
        Result = await interaction.client.db["Tickets"].find_one(
            {"ChannelID": interaction.channel.id}
        )
        if not Result:
            return await interaction.followup.send(
                f"{no} This isn't a ticket channel.", ephemeral=True
            )
        await interaction.message.delete()
        interaction.client.dispatch(
            "pticket_close", Result.get("_id"), self.reason, interaction.user
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.member:
            return await interaction.response.send_message(
                f"{no} You can't close this ticket.", ephemeral=True
            )
        await interaction.response.edit_message(
            view=None, content=f"{no} Cancelled.", embed=None
        )


async def setup(client: commands.Bot) -> None:

    await client.add_cog(TicketsPub(client))
