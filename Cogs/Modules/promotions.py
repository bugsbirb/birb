import discord
from discord.ext import commands
from discord import app_commands
import os
from dataclasses import dataclass
from utils.emojis import *
import datetime
import random
from utils.format import PaginatorButtons
import string
from utils.permissions import has_admin_role, has_staff_role
import logging

logger = logging.getLogger(__name__)
from utils.Module import ModuleCheck
from utils.autocompletes import DepartmentAutocomplete, RoleAutocomplete
from utils.format import IsSeperateBot

environment = os.getenv("ENVIRONMENT")

from utils.HelpEmbeds import (
    BotNotConfigured,
    NoPermissionChannel,
    ChannelNotFound,
    ModuleNotEnabled,
    NoChannelSet,
    Support,
    NotYourPanel,
)


async def CheckCooldown(
    interaction: discord.Interaction, User: discord.Member, Cooldown
):
    if not Cooldown:
        return False, None

    try:
        Cooldown = int(Cooldown)
    except ValueError:
        return False, None

    CooldownData: dict = await interaction.client.db["Cooldown"].find_one(
        {"User": User.id, "Guild": interaction.guild.id}
    )
    if not CooldownData or not CooldownData.get("LastPromoted"):
        return False, None

    Now = datetime.datetime.now()
    LastPromoted = CooldownData.get("LastPromoted")

    if Now - LastPromoted < datetime.timedelta(days=Cooldown):
        return True, LastPromoted
    return False, None


@dataclass
class IPromotionContext:
    interaction: discord.Interaction
    msg: discord.Message
    Config: dict
    channel: discord.TextChannel


async def PromotionContext(
    interaction: discord.Interaction,
    target: discord.Member | discord.User,
):
    if not await has_admin_role(interaction, "Promotion Permissions"):
        return None

    await interaction.response.defer()

    msg = await interaction.followup.send(
        f"<a:Loading:1167074303905386587> Processing promotion..."
    )

    if not await ModuleCheck(interaction.guild.id, "promotions"):
        await msg.edit(
            embed=ModuleNotEnabled(),
            view=Support(),
        )
        return None

    # if target.bot:
    #     await msg.edit(
    #         content=f"{no} **{interaction.user.display_name}**, you can't promote bots."
    #     )
    #     return None

    if interaction.user.id == target.id:
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you can't promote yourself."
        )
        return None

    config = await interaction.client.config.find_one({"_id": interaction.guild.id})

    if not config:
        await msg.edit(
            embed=BotNotConfigured(),
            view=Support(),
        )
        return None

    channel_id = config.get("Promo", {}).get("channel")

    if not channel_id:
        await msg.edit(
            embed=NoChannelSet(),
            view=Support(),
        )
        return None

    try:
        channel = await interaction.guild.fetch_channel(int(channel_id))
    except (discord.Forbidden, discord.NotFound):
        await msg.edit(
            embed=ChannelNotFound(),
            view=Support(),
        )
        return None

    client = await interaction.guild.fetch_member(interaction.client.user.id)

    if not channel.permissions_for(client).send_messages:
        await msg.edit(
            embed=NoPermissionChannel(channel),
            view=Support(),
        )
        return None

    cooldown, lastedPromoted = await CheckCooldown(
        interaction,
        target,
        config.get("Promo", {}).get("Cooldown"),
    )

    if cooldown:
        days = int(config.get("Promo", {}).get("Cooldown", 1))

        timestamp = int((lastedPromoted + datetime.timedelta(days=days)).timestamp())

        await msg.edit(
            content=(
                f"{no} **{interaction.user.display_name}**, "
                f"**@{target.display_name}** is on cooldown, "
                f"you can promote them again <t:{timestamp}:R>."
            )
        )
        return None

    return IPromotionContext(
        interaction=interaction,
        msg=msg,
        Config=config,
        channel=channel,
    )


@app_commands.autocomplete(rank=RoleAutocomplete)
@app_commands.describe(
    user="What staff member are you promoting?",
    reason="What makes them deserve the promotion?",
    rank="What is the role you are awarding them with?",
)
async def SingleHierarchy(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str,
    rank: str = None,
):

    try:
        context = await PromotionContext(interaction=interaction, target=user)
    except Exception as e:
        print(f"[S Context] {e}")
    if not context:
        return

    client = await interaction.guild.fetch_member(interaction.client.user.id)
    if context.channel.permissions_for(client).send_messages is False:
        return await context.msg.edit(
            embed=NoPermissionChannel(context.channel),
            view=Support(),
        )

    NextRole = None
    HierarchyRoles = (
        context.Config.get("Promo", {})
        .get("System", {})
        .get("single", {})
        .get("Hierarchy", [])
    )
    if not HierarchyRoles:
        return await context.msg.edit(
            content=f"{no} **{interaction.user.display_name}**, the hierarchy roles have not been set up yet.",
        )

    SortedRoles = [
        interaction.guild.get_role(int(roleId))
        for roleId in HierarchyRoles
        if interaction.guild.get_role(int(roleId))
    ]
    SortedRoles.sort(key=lambda r: r.position)
    PreviousRole = None
    HierarchyRoles = [role for role in SortedRoles if role in user.roles]
    PreviousRole = (
        max(HierarchyRoles, key=lambda r: r.position) if HierarchyRoles else None
    )
    SkipRole = interaction.guild.get_role(int(rank)) if rank else None
    if SkipRole and SkipRole in SortedRoles:
        if interaction.user.top_role.position <= SkipRole.position:
            await context.msg.edit(
                content=f"{no} **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{SkipRole.name}`.",
            )
            return

    NextRole = SkipRole

    if not SkipRole:
        UserRolesInHierarchy = [role for role in SortedRoles if role in user.roles]
        if not UserRolesInHierarchy:
            NextRole = SortedRoles[0] if SortedRoles else None
        else:
            NextRole = None
            for i, role in enumerate(SortedRoles):
                if role in user.roles:
                    if i + 1 < len(SortedRoles):
                        NextRole = SortedRoles[i + 1]
                    break
    if NextRole and interaction.user.top_role.position <= NextRole.position:
        await context.msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{NextRole.name}`.",
        )
        return

    if not NextRole and not SkipRole:
        await context.msg.edit(
            content=f"{no} **{interaction.user.display_name}**, **@{user.display_name}** is already at the top of the hierarchy and cannot be promoted further.",
        )
        return

    if not NextRole:
        await context.msg.edit(
            content=f"{no} **{interaction.user.display_name}**, **@{user.display_name}** i was unable to calculate which role comes next.",
            view=Support(),
        )

    Object = await interaction.client.db["promotions"].insert_one(
        {
            "management": interaction.user.id,
            "staff": user.id,
            "reason": reason,
            "random_string": "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            ),
            "new": NextRole.id,
            "previous": PreviousRole.id if PreviousRole else None,
            "guild_id": interaction.guild.id,
            "jump_url": None,
            "timestamp": datetime.datetime.now(),
            "annonymous": False,
            "Modmail System": "single",
            "single": {"SkipTo": rank},
        }
    )

    interaction.client.dispatch("promotion", Object.inserted_id, context.Config)
    await context.msg.edit(
        content=f"{tick} **{interaction.user.display_name}**, I've successfully promoted **@{user.display_name}**!",
    )


@app_commands.autocomplete(department=DepartmentAutocomplete, rank=RoleAutocomplete)
@app_commands.describe(
    user="What staff member are you promoting?",
    reason="What makes them deserve the promotion?",
    department="What department are they in?",
    rank="What is the role you are awarding them with?",
)
async def MultiHireachy(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str,
    department: str,
    rank: str = None,
):
    try:
        context = await PromotionContext(interaction=interaction, target=user)
        if not context:
            return

        client = await interaction.guild.fetch_member(interaction.client.user.id)
        if context.channel.permissions_for(client).send_messages is False:
            return await context.msg.edit(
                embed=NoPermissionChannel(context),
                view=Support(),
            )
        DepartmentHierarchies = [
            dept
            for sublist in context.Config.get("Promo", {})
            .get("System", {})
            .get("multi", {})
            .get("Departments", [])
            for dept in sublist
        ]
        department_data = next(
            (dept for dept in DepartmentHierarchies if dept.get("name") == department),
            None,
        )
        if not department_data:
            await context.msg.edit(
                content=f"{no} **{interaction.user.display_name}**, the department `{department}` does not exist.",
            )
            return

        NextRole = None
        PreviousRole = None

        RoleIDs = department_data.get("ranks", [])
        SortedRoles = [
            interaction.guild.get_role(int(roleId))
            for roleId in RoleIDs
            if interaction.guild.get_role(int(roleId))
        ]
        SortedRoles.sort(key=lambda r: r.position)

        HierarchyRoles = [role for role in SortedRoles if role in user.roles]
        PreviousRole = (
            max(HierarchyRoles, key=lambda r: r.position) if HierarchyRoles else None
        )
        UserRolesInHierarchy = [role for role in SortedRoles if role in user.roles]
        SkipRole = interaction.guild.get_role(int(rank)) if rank else None
        if SkipRole and SkipRole in SortedRoles:
            if interaction.user.top_role.position <= SkipRole.position:
                await context.msg.edit(
                    content=f"{no} **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{SkipRole.name}`.",
                )
                return

        NextRole = SkipRole
        if not NextRole:
            if not UserRolesInHierarchy:
                NextRole = SortedRoles[0] if SortedRoles else None
            else:
                NextRole = None
                for i, role in enumerate(SortedRoles):
                    if role in user.roles:
                        if i + 1 < len(SortedRoles):
                            NextRole = SortedRoles[i + 1]
                        break

        if NextRole and interaction.user.top_role.position <= NextRole.position:
            await context.msg.edit(
                content=f"{no} **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{NextRole.name}`.",
            )
            return

        if not NextRole:
            await context.msg.edit(
                content=f"{no} **{interaction.user.display_name}**, **@{user.display_name}** is already at the top of the hierarchy and cannot be promoted further.",
            )
            return

        Object = await interaction.client.db["promotions"].insert_one(
            {
                "management": interaction.user.id,
                "staff": user.id,
                "reason": reason,
                "random_string": "".join(
                    random.choices(string.ascii_uppercase + string.digits, k=10)
                ),
                "guild_id": interaction.guild.id,
                "jump_url": None,
                "new": NextRole.id,
                "previous": PreviousRole.id if PreviousRole else None,
                "timestamp": datetime.datetime.now(),
                "annonymous": False,
                "Modmail System": "Multi Hierarchy",
                "multi": {"Department": department, "SkipTo": rank},
            }
        )

        interaction.client.dispatch("promotion", Object.inserted_id, context.Config)
        await context.msg.edit(
            content=f"{tick} **{interaction.user.display_name}**, I've successfully promoted **@{user.display_name}**!",
        )
    except (Exception) as e:
        print(e)


@app_commands.describe(
    staff="What staff member are you promoting?",
    new="What is the role you are awarding them with?",
    reason="What makes them deserve the promotion?",
)
async def issue(
    interaction: discord.Interaction,
    staff: discord.User,
    new: discord.Role,
    reason: str,
):
    context = await PromotionContext(interaction=interaction, target=staff)
    if not context:
        return

    client = await interaction.guild.fetch_member(interaction.client.user.id)
    if context.channel.permissions_for(client).send_messages is False:
        return await context.msg.edit(
            embed=NoPermissionChannel(context),
            view=Support(),
        )

    client = await interaction.guild.fetch_member(interaction.client.user.id)
    if context.channel.permissions_for(client).send_messages is False:
        return await context.msg.edit(
            embed=NoPermissionChannel(context.channel),
            view=Support(),
        )
    Object = await interaction.client.db["promotions"].insert_one(
        {
            "management": interaction.user.id,
            "staff": staff.id,
            "reason": reason,
            "new": new.id,
            "previous": None,
            "random_string": "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            ),
            "guild_id": interaction.guild.id,
            "jump_url": None,
            "timestamp": datetime.datetime.now(),
            "annonymous": False,
        }
    )

    interaction.client.dispatch("promotion", Object.inserted_id, context.Config)
    await context.msg.edit(
        content=f"{tick} **{interaction.user.display_name}**, I've successfully promoted **@{staff.display_name}** to `{new.name}`!",
    )


async def SyncServer(self: commands.Bot, guild: discord.Guild):
    app_commands.CommandTree.remove_command(self.tree, "promote", guild=guild)

    def DefaultCommand():
        return app_commands.Command(
            name="promote",
            description="Promote a staff member",
            callback=issue,
            guild_ids=[guild.id],
        )

    C = await self.config.find_one({"_id": guild.id})
    if not C:
        command = DefaultCommand()
    elif not C.get("Promo", None):
        command = DefaultCommand()
    elif not C.get("Promo").get("System", None):
        command = DefaultCommand()
    elif not C.get("Promo").get("System", {}).get("type"):
        command = DefaultCommand()
    elif C.get("Promo").get("System", {}).get("type") == "multi":
        command = app_commands.Command(
            name="promote",
            description="Promote a staff member",
            callback=MultiHireachy,
            guild_ids=[guild.id],
        )
    elif C.get("Promo").get("System", {}).get("type") == "single":
        command = app_commands.Command(
            name="promote",
            description="Promote a staff member",
            callback=SingleHierarchy,
            guild_ids=[guild.id],
        )
    else:
        command = DefaultCommand()

    app_commands.CommandTree.add_command(self.tree, command, guild=guild)
    await self.tree.sync(guild=guild)


TotalNeedingSynced = 0
SyncedAmount = 0


async def SyncCommands(self: commands.Bot):
    global SyncedAmount
    global TotalNeedingSynced

    logger.info("[Promotions] Syncing commands...")
    Multi = set()
    Single = set()
    TheOG = set()
    filter = {}
    if environment == "custom":
        filter["_id"] = int(os.getenv("CUSTOM_GUILD"))

    C = await self.config.find(filter).to_list(length=None)
    for CO in C:
        if not CO:
            continue
        if not CO.get("Promo", None):
            continue
        if CO.get("Promo") == {}:
            continue
        if CO.get("Modules", {}).get("promotions", False) is False:
            continue
        if not self.get_guild(int(CO["_id"])):
            continue

        if CO.get("Promo").get("System", {}).get("type") == "multi":
            Multi.add(CO["_id"])
        elif CO.get("Promo").get("System", {}).get("type") == "single":
            Single.add(CO["_id"])
        elif CO.get("Promo").get("System", {}).get("type", "og") == "og":
            TheOG.add(CO["_id"])

    for i in Multi.union(Single, TheOG):

        try:
            app_commands.CommandTree.remove_command(
                self.tree, "promote", guild=discord.Object(id=i)
            )
        except Exception as e:
            logging.error(e)
    try:

        if not len(Multi) == 0:
            MultiCommand = app_commands.Command(
                name="promote",
                description="Promote a staff member",
                callback=MultiHireachy,
                guild_ids=list(Multi),
            )
            try:
                app_commands.CommandTree.add_command(
                    self.tree,
                    MultiCommand,
                    guilds=[discord.Object(id=i) for i in Multi],
                )
            except Exception as e:
                logging.error(e)
        if not len(Single) == 0:
            SingleCommand = app_commands.Command(
                name="promote",
                description="Promote a staff member",
                callback=SingleHierarchy,
                guild_ids=list(Single),
            )
            try:
                app_commands.CommandTree.add_command(
                    self.tree,
                    SingleCommand,
                    guilds=[discord.Object(id=i) for i in Single],
                )
            except Exception as e:
                logging.error(e)
        if not len(TheOG) == 0:
            GlobalCommand = app_commands.Command(
                name="promote",
                description="Promote a staff member",
                callback=issue,
                guild_ids=list(TheOG),
            )
            try:

                app_commands.CommandTree.add_command(
                    self.tree,
                    GlobalCommand,
                    guilds=[discord.Object(id=i) for i in TheOG],
                )
            except Exception as e:
                logging.error(e)
    except Exception as e:
        logging.error(e)

    TotalNeedingSynced += len(Multi.union(Single, TheOG))

    All = list(Multi.union(Single, TheOG))
    for i in All:
        try:
            await self.tree.sync(guild=discord.Object(id=i))
            SyncedAmount += 1
        except:
            continue
    del All
    del Multi
    del Single
    del TheOG


async def PromotionEmbed(self: commands.Bot, promotion: dict):
    jump_url = (
        f"\n> **[Jump to Promotion]({promotion.get('jump_url', '')})**"
        if promotion.get("jump_url")
        else ""
    )
    embed = discord.Embed(
        color=discord.Color.dark_embed(),
        timestamp=promotion.get("timestamp"),
    )
    try:
        Staff = await self.fetch_user(promotion.get("staff"))
        Manager = await self.fetch_user(promotion.get("management"))
        Role = self.get_guild(promotion.get("guild_id")).get_role(promotion.get("new"))
    except (discord.NotFound, discord.HTTPException, AttributeError):
        Staff = None
        Manager = None
        Role = None

    value = (
        f"> **Manager:** <@{promotion.get('management')}>\n"
        f"> **Staff:** <@{promotion.get('staff')}>\n"
        f"> **Updated Rank:** {Role.mention if Role else 'Unknown'}\n"
        f"> **Reason:** {promotion.get('reason')}\n"
    )

    if len(value) > 1024:
        value = value[:1021] + "..."

    embed.add_field(name="Promotion Information", value=value)

    if jump_url:
        embed.add_field(name="Additional Information", inline=False, value=jump_url)

    if Staff and Manager:
        embed.set_footer(
            text=f"Created by @{Manager.display_name}", icon_url=Manager.display_avatar
        )
        embed.set_thumbnail(url=Staff.display_avatar)

    return embed


class promo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_group(description="Promotion commands")
    async def promotion(self, ctx: commands.Context):
        pass

    @promotion.command(description="View information about a promotion.")
    @app_commands.describe(id="The id of the promotion.")
    async def view(self, ctx: commands.Context, id: str):
        await ctx.defer()
        if not await ModuleCheck(ctx.guild.id, "promotions"):
            await ctx.send(embed=ModuleNotEnabled(), view=Support())
            return

        if not await has_staff_role(ctx, "Promotion Permissions"):
            return

        promotion = await self.client.db["promotions"].find_one(
            {"guild_id": ctx.guild.id, "random_string": id}
        )

        if not promotion:
            await ctx.send(
                f"{no} **{ctx.author.display_name}**, this promotion could not be found."
            )
            return
        view = ManagePromotion(promotion, ctx.author)
        if promotion.get("voided"):
            view.void.label = "Delete"
            view.void.style = discord.ButtonStyle.red
        embed = await PromotionEmbed(self.client, promotion)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(description="View a staff member's promotions")
    @app_commands.describe(staff="The staff member to view promotions for")
    async def promotions(self, ctx: commands.Context, staff: discord.User):
        await ctx.defer()

        if not await ModuleCheck(ctx.guild.id, "promotions"):
            await ctx.send(embed=ModuleNotEnabled(), view=Support())
            return

        if not await has_staff_role(ctx, "Promotion Permissions"):
            return

        filter = {"guild_id": ctx.guild.id, "staff": staff.id}
        promotions = await self.client.db["promotions"].find(filter).to_list(750)

        if not promotions:
            await ctx.send(
                f"{no} **{ctx.author.display_name}**, this staff member doesn't have any promotions."
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

        embeds = []
        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.set_thumbnail(url=staff.display_avatar)
        embed.set_author(icon_url=staff.display_avatar, name=staff.display_name)

        for i, promotion in enumerate(promotions):
            jump_url = promotion.get("jump_url", "")
            jump_url_text = (
                f"\n> **[Jump to Promotion]({jump_url})**" if jump_url else ""
            )

            value = (
                f"> **Promoted By:** <@{promotion['management']}>\n"
                f"> **New:** <@&{promotion.get('new', 'Unknown')}>\n"
                f"> **Reason:** {promotion.get('reason')}{jump_url_text}"
            )

            if len(value) > 1024:
                value = value[:1021] + "..."

            embed.add_field(
                name=f"<:Document:1223063264322125844> Promotion | {promotion['random_string']}",
                value=value,
                inline=False,
            )

            if (i + 1) % 9 == 0 or i == len(promotions) - 1:
                embeds.append(embed)
                embed = discord.Embed(color=discord.Color.dark_embed())
                embed.set_thumbnail(url=staff.display_avatar)
                embed.set_author(icon_url=staff.display_avatar, name=staff.display_name)

        paginator = await PaginatorButtons()
        await paginator.start(ctx, pages=embeds, msg=msg)


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
        view = ManagePromotion(self.infraction, self.author)
        if self.infraction.get("voided"):
            view.void.label = "Delete"
            view.void.style = discord.ButtonStyle.red
        await interaction.response.edit_message(
            content="",
            view=view,
        )


class ManagePromotion(discord.ui.View):
    def __init__(self, promotion: dict, author: discord.Member):
        super().__init__()
        self.promotion = promotion
        self.author = author

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
        view = ImDone(interaction.user, self.promotion)
        view.add_item(EditPromotion(self.promotion, self.author))
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

        promotion = self.promotion
        if promotion.get("voided", False):
            await interaction.client.db["promotions"].delete_one(
                {"_id": promotion["_id"]}
            )
            return await interaction.response.edit_message(
                content=f"{tick} **{interaction.user.display_name}**, I've deleted the promotion permanently.",
                view=None,
                embed=None,
            )

        await interaction.client.db["promotions"].update_one(
            {"_id": promotion["_id"]},
            {"$set": {"voided": True}, "$unset": {"expiration": ""}},
            upsert=False,
        )
        await interaction.response.edit_message(
            content=f"{tick} **{interaction.user.display_name}**, I've voided the promotion.",
            view=None,
            embed=None,
        )
        interaction.client.dispatch("promotion_void", promotion["_id"])
        interaction.client.dispatch(
            "promotion_log", promotion["_id"], "delete", interaction.user
        )


class EditPromotion(discord.ui.Select):
    def __init__(self, infraction: dict, author: discord.Member):
        super().__init__(
            placeholder="What do you want to edit?",
            options=[
                discord.SelectOption(label="Reason", value="reason"),
                discord.SelectOption(label="Notes", value="notes"),
            ],
        )
        self.infraction = infraction
        self.author = author

    async def callback(self, interaction: discord.Interaction):

        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        if self.values[0] == "reason":
            view = UpdatePromotion(self.infraction, self.author, "reason")
            await interaction.response.send_modal(view)
        elif self.values[0] == "notes":
            view = UpdatePromotion(self.infraction, self.author, "notes")
            await interaction.response.send_modal(view)


class UpdatePromotion(discord.ui.Modal):
    def __init__(self, infraction: dict, author: discord.Member, type: str):
        super().__init__(timeout=360, title="Update Promotion")
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

    async def on_submit(self, interaction: discord.Interaction):
        Org = self.infraction.copy()
        if self.reason:
            self.infraction["reason"] = self.reason.value
            await interaction.client.db["promotions"].update_one(
                {"_id": self.infraction["_id"]},
                {"$set": {"reason": self.reason.value}},
            )
        elif self.notes:
            self.infraction["notes"] = self.notes.value
            await interaction.client.db["promotions"].update_one(
                {"_id": self.infraction["_id"]},
                {"$set": {"notes": self.notes.value}},
            )
        view = ManagePromotion(self.infraction, self.author)
        if self.infraction.get("voided"):
            view.void.label = "Delete"
            view.void.style = discord.ButtonStyle.red
        await interaction.response.edit_message(
            embed=await PromotionEmbed(interaction.client, self.infraction),
            view=view,
        )

        interaction.client.dispatch("promotion", self.infraction, True)
        interaction.client.dispatch(
            "promotion_log",
            self.infraction.get("_id"),
            "modify",
            interaction.user,
            Org,
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(promo(client))
