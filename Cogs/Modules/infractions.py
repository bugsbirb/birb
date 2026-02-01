import discord
from discord.ext import commands
from typing import Literal, Optional
import random
import string
import os
import re
from datetime import datetime
from discord import app_commands
from utils.format import PaginatorButtons, IsSeperateBot, strtotime, DefaultTypes
from utils.permissions import has_admin_role, premium
from utils.emojis import *
from utils.Module import ModuleCheck
from utils.autocompletes import infractiontypes, infractionreasons
from utils.HelpEmbeds import (
    BotNotConfigured,
    NoPermissionChannel,
    ChannelNotFound,
    ModuleNotEnabled,
    NoChannelSet,
    Support,
    ModuleNotSetup,
    NoPremium,
    NotYourPanel,
)


environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")


async def InfractionEmbed(self: commands.Bot, infraction: dict):
    voided = "(Voided)" if infraction.get("voided") else ""
    expiration = (
        f"\n> **Expiration:** <t:{int(infraction.get('expiration').timestamp())}:D>{' **(Infraction Expired)**' if infraction.get('expiration') and infraction.get('expiration') < datetime.now() else ''}"
        if infraction.get("expiration")
        else ""
    )
    jump_url = (
        f"\n> **[Jump to Infraction]({infraction.get('jump_url', '')})**"
        if infraction.get("jump_url")
        else ""
    )
    embed = discord.Embed(
        color=discord.Color.dark_embed(),
        timestamp=infraction.get("timestamp"),
    )
    try:
        Staff = await self.fetch_user(infraction.get("staff"))
        Admin = await self.fetch_user(infraction.get("management"))
    except (discord.NotFound, discord.HTTPException):
        Staff = None
        Admin = None
    value = (
        f"> **Manager:** <@{infraction.get('management')}>\n"
        f"> **Staff:** <@{infraction.get('staff')}>\n"
        f"> **Action:** {infraction.get('action')}\n"
        f"> **Reason:** {infraction.get('reason')}\n"
    )

    if len(value) > 1024:
        value = value[:1021] + "..."

    embed.add_field(name="Case Information", value=value)

    embed.set_author(name=f"Infraction | {infraction['random_string']} {voided}")
    value = f"> **Notes:** {infraction.get('notes')}{expiration}{jump_url}"
    if len(value) > 1024:
        value = value[:1021] + "..."
    embed.add_field(name="Additional Information", inline=False, value=value)
    if Staff and Admin:
        embed.set_footer(
            text=f"Created by @{Admin.display_name}", icon_url=Admin.display_avatar
        )
        embed.set_thumbnail(url=Staff.display_avatar)

    return embed


class Infractions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_group(description="Infract multiple staff members")
    async def infraction(self, ctx: commands.Context):
        pass

    @infraction.command(name="multiple", description="Infract multiple staff members")
    @app_commands.autocomplete(action=infractiontypes)
    @app_commands.describe(
        action="The action to take",
        reason="The reason for the action",
        notes="Additional notes",
        expiration="The expiration date of the infraction (m/h/d/w)",
        anonymous="Whether to send the infraction anonymously",
    )
    async def infraction_multiple(
        self,
        ctx: commands.Context,
        action: discord.ext.commands.Range[str, 1, 200],
        *,
        reason: discord.ext.commands.Range[str, 1, 2000],
        notes="",
        expiration: Optional[str] = None,
        anonymous: Optional[Literal["True"]] = None,
    ):
        if not await premium(ctx.guild.id):
            return await ctx.send(embed=NoPremium(), view=Support())
        if not await ModuleCheck(ctx.guild.id, "infractions"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )

            return
        if not await has_admin_role(ctx, "Infraction Permissions"):
            return
        await ctx.defer(ephemeral=True)
        view = discord.ui.View()

        view.add_item(InfractionMultiple(action, reason, notes, expiration, anonymous))
        await ctx.send(
            f"<:List:1223063187063308328> **{ctx.author.display_name}**, select the users you want to infraction!",
            view=view,
        )

    async def TypePerms(self, author: discord.Member, Action: dict):
        if not Action:
            return True
        if not Action.get("RequiredRoles"):
            return True
        if any(role.id in Action.get("RequiredRoles", []) for role in author.roles):
            return True
        return False

    @infraction.command(description="Infract staff members")
    @app_commands.autocomplete(action=infractiontypes)
    @app_commands.autocomplete(reason=infractionreasons)
    @app_commands.describe(
        staff="The staff member to infract",
        action="The action to take",
        reason="The reason for the action",
        notes="Additional notes",
        expiration="The expiration date of the infraction (m/h/d/w)",
        anonymous="Whether to send the infraction anonymously",
    )
    async def issue(
        self,
        ctx: commands.Context,
        staff: discord.User,
        action: discord.ext.commands.Range[str, 1, 200],
        *,
        reason: discord.ext.commands.Range[str, 1, 2000],
        notes="",
        expiration: Optional[str] = None,
        anonymous: Optional[Literal["True"]] = None,
    ):
        if not await has_admin_role(ctx, "Infraction Permissions"):
            return
        if not await ModuleCheck(ctx.guild.id, "infractions"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )

            return
        isEscalated = False

        TypeActions = await self.client.db["infractiontypeactions"].find_one(
            {"guild_id": ctx.guild.id, "name": action}
        )
        if not await self.TypePerms(ctx.author, TypeActions):
            return await ctx.send(
                f"{no} **{ctx.author.display_name},** you don't have permission to use this shift type."
            )

        Config = await self.client.config.find_one({"_id": ctx.guild.id})
        if Config is None:
            return await ctx.send(embed=BotNotConfigured(), view=Support())
        if Config.get("Infraction", None) is None:
            return await ctx.send(embed=ModuleNotSetup(), view=Support())
        if staff is None:
            await ctx.send(
                f"{no} **{ctx.author.display_name}**, this user can not be found.",
            )
            return
        isApproval = bool(
            Config.get("Infraction", {}).get("Approval", None)
            and Config.get("Infraction", {}).get("Approval", {}).get("channel")
            is not None
        )
        msg = await ctx.send(
            content=f"<a:Loading:1167074303905386587> **{ctx.author.display_name},** hold on while I infract this staff member.",
        )
        if staff.id == self.client.user.id:
            await msg.edit(
                content=f"{no} **{ctx.author.display_name},** what did I do to you?"
            )
            return
        if staff.bot:
            await msg.edit(
                content=f"{no} **{ctx.author.display_name},** I'm not gonna infract my own kind."
            )
            return

        if Config.get("Infraction", {}).get("channel") is None:
            return await msg.edit(content="", embed=NoChannelSet(), view=Support())
        try:
            channel = await self.client.fetch_channel(
                int(Config.get("Infraction", {}).get("channel"))
            )
        except (discord.Forbidden, discord.NotFound):
            return await msg.edit(content=f"", embed=ChannelNotFound(), view=Support())
        if not channel:
            return await msg.edit(content=f"", embed=ChannelNotFound(), view=Support())
        client = await ctx.guild.fetch_member(self.client.user.id)
        if (
            channel.permissions_for(client).send_messages is False
            or channel.permissions_for(client).view_channel is None
        ):

            return await msg.edit(
                content=f"",
                embed=NoPermissionChannel(channel),
            )
        if expiration and not re.match(r"^\d+[mhdws]$", expiration):
            await msg.edit(
                content=f"{no} **{ctx.author.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.",
            )
            return
        if expiration:
            expiration = await strtotime(expiration)
        random_string = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=10)
        )
        if Config.get("group", {}).get("id", None):
            from utils.roblox import GetValidToken
            from utils.HelpEmbeds import NotRobloxLinked

            Roblox = await GetValidToken(user=ctx.author)
            if not Roblox:
                return await msg.edit(embed=NotRobloxLinked())
        Org = action
        CheckedActions = []
        isEscalated = False
        NextType = None

        Max = 30
        Min = 0

        while Min < Max:
            TypeActions = await self.client.db["infractiontypeactions"].find_one(
                {"guild_id": ctx.guild.id, "name": action}
            )
            if not TypeActions:
                break

            Escalation = TypeActions.get("Escalation")
            if not Escalation:
                break

            Threshold = Escalation.get("Threshold")
            NextType = Escalation.get("Next Type")

            try:
                Threshold = int(Threshold)
            except (ValueError, TypeError):
                break

            if not NextType or action in CheckedActions:
                break

            InfractionsOfType = await self.client.db["infractions"].count_documents(
                {
                    "guild_id": ctx.guild.id,
                    "staff": staff.id,
                    "action": action,
                    "Upscaled": {"$exists": False},
                }
            )
            Current = InfractionsOfType + 1
            if InfractionsOfType + 1 >= Threshold:
                CheckedActions.append(
                    {
                        "action": action,
                        "count": Current,
                        "threshold": Threshold,
                    }
                )
                Org = action
                action = NextType
                isEscalated = True
            else:
                break
        FormeData = {
            "guild_id": ctx.guild.id,
            "staff": staff.id,
            "management": ctx.author.id,
            "action": action,
            "reason": reason,
            "notes": notes if notes else "`N/A`",
            "expiration": expiration,
            "random_string": random_string,
            "annonymous": anonymous,
            "timestamp": datetime.now(),
            "SkipExec": None,
        }
        embeds = []
        EscFrom = None
        if isApproval:
            FormeData["ApprovalStatus"] = True
        if NextType and isEscalated:
            FormeData["EscalatedFrom"] = Org
            FormeData["EscalationChain"] = list(CheckedActions)

            parts = []
            for step in CheckedActions:
                count = step["count"]
                Action = step["action"]
                plural = "s" if count != 1 else ""
                parts.append(f"{count} {Action}{plural}")

            if len(parts) > 1:
                Text = " and ".join(parts[-2:])
            else:
                Text = parts[0]

            EscFrom = discord.Embed(color=discord.Color.blue()).set_author(
                name=f"Automatically escalated from {Text} to {action}",
                icon_url="https://cdn.discordapp.com/emojis/1401307998260822028.webp?size=96",
            )

        if Config.get("Module Options", {}).get("Infraction Confirmation", False):
            custom = await self.client.db["Customisation"].find_one(
                {"guild_id": ctx.guild.id, "type": "Infractions"}
            )
            from Cogs.Events.on_infraction import Replacements, DefaultEmbed
            from utils.ui import YesOrNo

            if custom:
                from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed

                replaces = Replacements(staff, FormeData, ctx.author)
                embed = await DisplayEmbed(custom, ctx.author, replaces)
            else:
                embed = DefaultEmbed(FormeData, staff, ctx.author)
            embeds.append(embed)
            if EscFrom:
                embeds.append(EscFrom)

            view = YesOrNo(Z="Z_Z" if isEscalated else None)
            msg = await msg.edit(
                embeds=embeds,
                view=view,
                content=f"<:Tip:1238599473429483612> **{ctx.author.display_name}**, are you sure?\n-# Infraction Preview",
            )
            await view.wait()
            if view.value is None:
                return await msg.edit(
                    content=f"{crisis} **{ctx.author.display_name},** you didn't respond in time.",
                    view=None,
                    embed=None,
                )
            elif view.value is True:
                pass
            elif view.value == "SkipExec":
                FormeData["action"] = Org
                FormeData["skipExec"] = True
            else:
                return await msg.edit(
                    content=f"{no} **{ctx.author.display_name},** infraction cancelled.",
                    view=None,
                    embed=None,
                )

        if NextType and isEscalated:
            await self.client.db["infractions"].update_many(
                {
                    "guild_id": ctx.guild.id,
                    "staff": staff.id,
                    "action": Org,
                    "Upscaled": {"$exists": False},
                },
                {"$set": {"Upscaled": True}},
            )

        InfractionResult = await self.client.db["infractions"].insert_one(FormeData)
        if not InfractionResult.inserted_id:
            await msg.edit(
                content=f"{crisis} **{ctx.author.display_name},** I had an issue submitting this infraction. Please head to our support server!",
            )
            return
        if isApproval:
            try:
                channel = await self.client.fetch_channel(
                    int(Config.get("Infraction", {}).get("channel"))
                )
            except (discord.Forbidden, discord.NotFound):
                return await msg.edit(
                    content=f"", embed=ChannelNotFound(), view=Support()
                )
            if not channel:
                return await msg.edit(
                    content=f"", embed=ChannelNotFound(), view=Support()
                )
            self.client.dispatch(
                "infraction_approval", InfractionResult.inserted_id, Config
            )
            return await msg.edit(
                content=f"{tick} **{ctx.author.display_name},** I've successfully sent the infraction to approval.",
                embed=None,
                view=None,
            )

        self.client.dispatch(
            "infraction", InfractionResult.inserted_id, Config, TypeActions
        )

        await msg.edit(
            content=f"{tick} **{ctx.author.display_name},** I've successfully infracted **@{staff.display_name}**! {f'(Escalated to {action})' if isEscalated and FormeData.get('skipExec') is None else ''}",
            embed=None,
            view=None,
        )

    @infraction.command(description="View member's or server infractions")
    @app_commands.describe(
        staff="The staff member to view infractions for",
        scope="The scope of infractions to view",
    )
    async def list(
        self,
        ctx: commands.Context,
        staff: discord.User = None,
        scope: Literal["Voided", "Expired", "All"] = None,
    ):
        await ctx.defer()
        if not await ModuleCheck(ctx.guild.id, "infractions"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return
        if not await has_admin_role(ctx, "Infraction Permissions"):
            return

        filter = {
            "guild_id": ctx.guild.id,
            **({"staff": staff.id} if staff else {}),
            "voided": (
                True
                if scope == "Voided"
                else {"$ne": True} if scope != "Expired" else None
            ),
            "expired": True if scope == "Expired" else None,
            "$or": [{"ApprovalStatus": {"$exists": False}}, {"ApprovalStatus": False}],
        }
        filter = {k: v for k, v in filter.items() if v is not None}

        infractions = await self.client.db["infractions"].find(filter).to_list(125)
        if not infractions:
            scope_text = (
                "voided"
                if scope == "Voided"
                else "expired" if scope == "Expired" else "any"
            )
            await ctx.send(
            f"{no} **{ctx.author.display_name}**, no "
            + (f"{scope_text} " if scope_text else "")
            + "infractions were found"
            + (f" for **@{staff.display_name}**" if staff else "")
            + "."
        )
        return


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
        embed = (
            discord.Embed(color=discord.Color.dark_embed())
            .set_thumbnail(url=staff.display_avatar if staff else ctx.guild.icon)
            .set_author(
                icon_url=staff.display_avatar if staff else ctx.guild.icon,
                name=(f"@{staff.name}'s " if staff else f"{ctx.guild.name}'s ")
                + (
                    "Voided"
                    if scope == "Voided"
                    else "Expired" if scope == "Expired" else ""
                )
                + " Infractions",
            )
        )

        embeds = []
        for i, infraction in enumerate(infractions):
            voided = "**(Voided)**" if infraction.get("voided") else ""
            jump_url = (
                f"\n> **[Jump to Infraction]({infraction.get('jump_url', '')})**"
                if infraction.get("jump_url")
                else ""
            )
            exp = infraction.get("expiration")
            expiration = (
                f"\n> **Expiration:** <t:{int(exp.timestamp())}:D>{' **(Infraction Expired)**' if exp and exp < datetime.now() else ''}"
                if exp
                else ""
            )
            value = (
                f"> **Infracted By:** <@{infraction.get('management')}>\n"
                + (f"> **Staff:** <@{infraction.get('staff')}>\n" if not staff else "")
                + f"> **Action:** {infraction.get('action')}\n"
                + f"> **Reason:** {infraction.get('reason')}\n"
                + f"> **Notes:** {infraction.get('notes')}{expiration}{jump_url}"
            )[:1025]

            embed.add_field(
                name=f"<:Document:1223063264322125844> Infraction | {infraction['random_string']} {voided}",
                value=value[:1021] + "..." if len(value) > 1024 else value,
                inline=False,
            )
            if (
                (i + 1) % 5 == 0
                or i == len(infractions) - 1
                or self.EmbedSize(embed) > 5999
            ):
                embeds.append(embed)
                embed = (
                    discord.Embed(color=discord.Color.dark_embed())
                    .set_thumbnail(
                        url=staff.display_avatar if staff else ctx.guild.icon
                    )
                    .set_author(
                        icon_url=staff.display_avatar if staff else ctx.guild.icon,
                        name=(f"@{staff.name}'s " if staff else f"{ctx.guild.name}'s ")
                        + (
                            "Voided"
                            if scope == "Voided"
                            else "Expired" if scope == "Expired" else ""
                        )
                        + " Infractions",
                    )
                )

        paginator = await PaginatorButtons(
            extra=[
                discord.ui.Button(
                    label="View Online",
                    style=discord.ButtonStyle.link,
                    url=f"https://astrobirb.dev/panel/{ctx.guild.id}",
                ),
            ]
        )

        await paginator.start(ctx, pages=embeds[:45], msg=msg)

    @infraction.command(description="View an infraction and manage it.")
    @app_commands.describe(
        id="The ID of the infraction to view",
        voided="Show a hidden infraction",
    )
    async def view(self, ctx: commands.Context, id: str, voided: bool = False):
        if not await ModuleCheck(ctx.guild.id, "infractions"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )

            return
        if not await has_admin_role(ctx, "Infraction Permissions"):
            return

        filter = {
            "guild_id": ctx.guild.id,
            "random_string": id,
            "voided": {"$ne": True},
        }
        if voided:
            filter["voided"] = True

        infraction = await self.client.db["infractions"].find_one(filter)

        if infraction is None:
            await ctx.send(
                f"{no} **{ctx.author.display_name}**, I couldn't find the infraction with ID `{id}` in this guild.",
            )
            return

        embed = await InfractionEmbed(self.client, infraction)
        view = ManageInfraction(infraction, ctx.author)
        if infraction.get("voided"):
            view.void.label = "Delete"
            view.void.style = discord.ButtonStyle.red
        await ctx.send(embed=embed, view=view)

    def EmbedSize(self, embed: discord.Embed):
        size = len(embed.title or "") + len(embed.description or "")
        size += len(embed.footer.text or "") if embed.footer else 0
        size += sum(
            len(field.name or "") + len(field.value or "") for field in embed.fields
        )
        return size


class InfractionMultiple(discord.ui.UserSelect):
    def __init__(self, action, reason, notes, expiration, anonymous):
        super().__init__(placeholder="Members", max_values=25, min_values=1)
        self.action = action
        self.reason = reason
        self.notes = notes
        self.expiration = expiration
        self.anonymous = anonymous

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        action = self.action
        reason = self.reason
        notes = self.notes
        expiration = self.expiration
        anonymous = self.anonymous
        isEscalated = False

        TypeActions = await interaction.client.db["infractiontypeactions"].find_one(
            {"guild_id": interaction.guild.id, "name": action}
        )
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if Config is None:
            return await interaction.followup.send(
                embed=BotNotConfigured(), ephemeral=True
            )
        if Config.get("Infraction", None) is None:
            return await interaction.followup.send(
                embed=ModuleNotSetup(), ephemeral=True
            )
        if Config.get("Infraction", {}).get("channel") is None:
            return await interaction.followup.send(embed=NoChannelSet(), ephemeral=True)

        if Config.get("group", {}).get("id", None):
            from utils.roblox import GetValidToken
            from utils.HelpEmbeds import NotRobloxLinked

            Roblox = await GetValidToken(user=interaction.user)
            if not Roblox:
                return await interaction.followup.send(
                    embed=NotRobloxLinked(), ephemeral=True
                )

        try:
            channel = await interaction.client.fetch_channel(
                int(Config.get("Infraction", {}).get("channel"))
            )
        except (discord.Forbidden, discord.NotFound):
            return await interaction.followup.send(
                embed=ChannelNotFound(), ephemeral=True
            )
        if not channel:
            return await interaction.followup.send(
                embed=ChannelNotFound(), ephemeral=True
            )

        client = await interaction.guild.fetch_member(interaction.client.user.id)
        if (
            channel.permissions_for(client).send_messages is False
            or channel.permissions_for(client).view_channel is None
        ):
            return await interaction.followup.send(
                embed=NoPermissionChannel(channel), ephemeral=True
            )

        if expiration and not re.match(r"^\d+[mhdws]$", expiration):
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.",
                ephemeral=True,
            )
        if expiration:
            expiration = await strtotime(expiration)

        for staff in self.values:
            if staff is None:
                await interaction.followup.send(
                    f"{no} **{interaction.user.display_name}**, this user can not be found.",
                    ephemeral=True,
                )
                return

            NextType = None
            if TypeActions and TypeActions.get("Escalation", None):
                Escalation = TypeActions.get("Escalation")
                Threshold = Escalation.get("Threshold", None)
                NextType = Escalation.get("Next Type")
                if Threshold and NextType:
                    InfractionsWithType = await interaction.client.db[
                        "infractions"
                    ].count_documents(
                        {
                            "guild_id": interaction.guild.id,
                            "staff": staff.id,
                            "action": action,
                            "Upscaled": {"$exists": False},
                        }
                    )
                    if isinstance(Threshold, str):
                        if InfractionsWithType + 1 >= int(Threshold):
                            isEscalated = True
                            Org = action
                            action = NextType

            random_string = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )

            FormeData = {
                "guild_id": interaction.guild.id,
                "staff": staff.id,
                "management": interaction.user.id,
                "action": action,
                "reason": reason,
                "notes": notes if notes else "`N/A`",
                "expiration": expiration,
                "random_string": random_string,
                "annonymous": anonymous,
                "timestamp": datetime.now(),
            }

            if isEscalated:
                FormeData[
                    "reason"
                ] += f"\n-# Automatically escalated to **{action}** from **{Org}**"

            InfractionResult = await interaction.client.db["infractions"].insert_one(
                FormeData
            )
            if not InfractionResult.inserted_id:
                await interaction.edit_original_response(
                    content=f"{crisis} **{interaction.user.display_name},** hi I had a issue submitting this infraction please head to support!",
                    embed=None,
                    view=None,
                )
                return

            if NextType and isEscalated:
                await interaction.client.db["infractions"].update_many(
                    {
                        "guild_id": interaction.guild.id,
                        "staff": staff.id,
                        "action": Org,
                        "Upscaled": {"$exists": False},
                    },
                    {"$set": {"Upscaled": True}},
                )

            TypeActions = await interaction.client.db["infractiontypeactions"].find_one(
                {"guild_id": interaction.guild.id, "name": action}
            )

            interaction.client.dispatch(
                "infraction", InfractionResult.inserted_id, Config, TypeActions
            )

        await interaction.edit_original_response(
            content=f"{tick} **{interaction.user.display_name},** I have infracted all the staff members!",
            view=None,
        )


class ManageInfraction(discord.ui.View):
    def __init__(self, infraction: dict, author: discord.Member):
        super().__init__()
        self.infraction = infraction
        self.author = author
        self.add_item(
            discord.ui.Button(
                label="View Online",
                style=discord.ButtonStyle.link,
                url=f"https://astrobirb.dev/panel/{infraction.get('guild_id')}/{infraction.get('random_string')}",
            )
        )

    @discord.ui.button(
        label="Edit",
        style=discord.ButtonStyle.blurple,
        emoji="<:edit:1333861885778333798>",
    )
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        view = ImDone(interaction.user, self.infraction)
        view.add_item(EditInfraction(self.infraction, self.author))
        await interaction.response.edit_message(
            view=view,
        )

    @discord.ui.button(
        label="Void",
        style=discord.ButtonStyle.danger,
        emoji="<:Destroy:1333862072143974421>",
    )
    async def void(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        infraction = self.infraction
        if infraction.get("voided", False):
            await interaction.client.db["infractions"].delete_one(
                {"_id": infraction["_id"]}
            )
            return await interaction.response.edit_message(
                content=f"{tick} **{interaction.user.display_name}**, I've deleted the infraction permanently.",
                view=None,
                embed=None,
            )

        await interaction.client.db["infractions"].update_one(
            {"_id": infraction["_id"]},
            {"$set": {"voided": True}, "$unset": {"expiration": ""}},
            upsert=False,
        )
        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name}**, I've voided the infraction.",
            view=None,
            embed=None,
        )
        interaction.client.dispatch("infraction_void", infraction["_id"])
        interaction.client.dispatch(
            "infraction_log", infraction["_id"], "delete", interaction.user
        )


class EditInfraction(discord.ui.Select):
    def __init__(self, infraction: dict, author: discord.Member):
        super().__init__(
            placeholder="What do you want to edit?",
            options=[
                discord.SelectOption(label="Action", value="action"),
                discord.SelectOption(label="Reason", value="reason"),
                discord.SelectOption(label="Notes", value="notes"),
                discord.SelectOption(label="Expiration", value="expiration"),
            ],
        )
        self.infraction = infraction
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        value = self.values[0]
        if value == "action":
            config = await interaction.client.config.find_one(
                {"_id": interaction.guild.id}
            )
            if config is None:
                return await interaction.followup.send(
                    embed=BotNotConfigured(),
                )
            Types = config.get("Infraction", {}).get("types", [])
            options = None
            if not Types or len(Types) == 0:
                Types = DefaultTypes()

            options = [
                discord.SelectOption(label=name[:80], value=name[:80])
                for name in set(Types)
            ]

            view = ImDone(self.author, self.infraction)
            view.done.label = "Cancel"
            view.done.style = discord.ButtonStyle.red
            view.add_item(UpdateAction(self.infraction, self.author, options))
            return await interaction.response.edit_message(
                content="",
                view=view,
            )

        view = UpdateInfraction(self.infraction, self.author, self.values[0])
        await interaction.response.send_modal(view)


class UpdateInfraction(discord.ui.Modal):
    def __init__(self, infraction: dict, author: discord.Member, type: str):
        super().__init__(timeout=360, title="Update Infraction")
        self.infraction = infraction
        self.author = author

        self.exp = None
        self.reason = None
        self.notes = None
        if type == "reason":
            self.reason = discord.ui.TextInput(
                default=infraction.get("reason"),
                label="Reason",
                placeholder="The reason for the action",
            )
            self.add_item(self.reason)
        elif type == "notes":
            self.notes = discord.ui.TextInput(
                default=infraction.get("notes"),
                label="Notes",
                placeholder="Additional notes",
            )
            self.add_item(self.notes)
        elif type == "expiration":
            self.exp = discord.ui.TextInput(
                label="Expiration",
                placeholder="1d (1 day), 2h (2 hours), etc.",
            )
            self.add_item(self.exp)

    async def on_submit(self, interaction: discord.Interaction):
        Org = self.infraction.copy()
        if self.exp:
            expiration = self.exp.value
            if expiration and not re.match(r"^\d+[mhdws]$", expiration):
                await interaction.response.send_message(
                    f"{no} **{interaction.user.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.",
                    ephemeral=True,
                )
                return
            if expiration:
                expiration = await strtotime(expiration)
                self.infraction["expiration"] = expiration
                await interaction.client.db["infractions"].update_one(
                    {"_id": self.infraction["_id"]},
                    {"$set": {"expiration": expiration}},
                )
        elif self.reason:
            self.infraction["reason"] = self.reason.value
            await interaction.client.db["infractions"].update_one(
                {"_id": self.infraction["_id"]},
                {"$set": {"reason": self.reason.value}},
            )
        elif self.notes:
            self.infraction["notes"] = self.notes.value
            await interaction.client.db["infractions"].update_one(
                {"_id": self.infraction["_id"]},
                {"$set": {"notes": self.notes.value}},
            )
        view = ManageInfraction(self.infraction, self.author)
        if self.infraction.get("voided"):
            view.void.label = "Delete"
            view.void.style = discord.ButtonStyle.red
        await interaction.response.edit_message(
            embed=await InfractionEmbed(interaction.client, self.infraction),
            view=view,
        )

        interaction.client.dispatch("infraction_edit", self.infraction)
        interaction.client.dispatch(
            "infraction_log",
            self.infraction.get("_id"),
            "modify",
            interaction.user,
            Org,
        )


class ImDone(discord.ui.View):
    def __init__(self, author, infraction):
        super().__init__()
        self.author = author
        self.infraction = infraction

    @discord.ui.button(
        label="I'm Done",
        style=discord.ButtonStyle.green,
        row=2,
    )
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        view = ManageInfraction(self.infraction, self.author)
        if self.infraction.get("voided"):
            view.void.label = "Delete"
            view.void.style = discord.ButtonStyle.red
        await interaction.response.edit_message(
            content="",
            view=view,
        )


class UpdateAction(discord.ui.Select):
    def __init__(
        self,
        infraction: dict,
        author: discord.Member,
        options: list,
    ):
        super().__init__(
            placeholder="Select the action",
            options=options,
        )
        self.infraction = infraction
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        self.infraction["action"] = self.values[0]
        await interaction.client.db["infractions"].update_one(
            {"_id": self.infraction["_id"]},
            {"$set": {"action": self.values[0]}},
        )

        interaction.client.dispatch("infraction_edit", self.infraction)
        await interaction.response.edit_message(
            embed=await InfractionEmbed(interaction.client, self.infraction),
            view=ManageInfraction(self.infraction, self.author),
        )

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Infractions(client))
