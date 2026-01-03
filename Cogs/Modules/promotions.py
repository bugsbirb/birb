import discord
from discord.ext import commands
from discord import app_commands
import os
from utils.emojis import *
import datetime
import random
from utils.format import PaginatorButtons
import string
from utils.permissions import has_admin_role, has_staff_role
from utils.Module import ModuleCheck
from utils.autocompletes import DepartmentAutocomplete, RoleAutocomplete
from utils.format import IsSeperateBot
# TODO: Merge the 3 commands together some how, extremely inefficient, and it's hard to update.


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

    if not await has_admin_role(interaction, "Promotion Permissions"):
        return
    await interaction.response.defer()
    msg: discord.Message = await interaction.followup.send(
        f"<a:Loading:1167074303905386587> Promoting **@{user.display_name}**...",
    )
    if not await ModuleCheck(interaction.guild.id, "promotions"):
        await msg.edit(
            embed=ModuleNotEnabled(),
            view=Support(),
            ephemeral=True,
        )
        return
    if user is None:
        await msg.edit(
            content=f"{no} **{user.display_name}**, this user cannot be found.",
        )
        return

    if interaction.user.bot:
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you can't promote bots.",
        )
        return

    if interaction.user == user:
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you can't promote yourself.",
        )
        return

    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not Config:
        return await msg.edit(
            embed=BotNotConfigured(),
            view=Support(),
        )
    if not Config.get("Promo", {}).get("channel"):
        return await msg.edit(
            embed=NoChannelSet(),
            view=Support(),
        )

    try:
        channel = await interaction.guild.fetch_channel(
            int(Config.get("Promo", {}).get("channel"))
        )
    except (discord.Forbidden, discord.NotFound):
        return await msg.edit(
            embed=ChannelNotFound(),
            view=Support(),
        )
    if not channel:
        return await msg.edit(
            embed=ChannelNotFound(),
            view=Support(),
        )
    CallDown, LastPromoted = await CheckCooldown(
        interaction, user, Config.get("Promo", {}).get("Cooldown", None)
    )
    if CallDown:
        Time = int(Config.get("Promo", {}).get("Cooldown", 1))
        Timestamp = int((LastPromoted + datetime.timedelta(days=Time)).timestamp())
        return await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, **@{user.display_name}** is on cooldown, you can promote them again <t:{Timestamp}:R>."
        )

    client = await interaction.guild.fetch_member(interaction.client.user.id)
    if channel.permissions_for(client).send_messages is False:
        return await msg.edit(
            embed=NoPermissionChannel(channel),
            view=Support(),
        )

    HierarchyRoles = (
        Config.get("Promo", {}).get("System", {}).get("single", {}).get("Hierarchy", [])
    )
    if not HierarchyRoles:
        return await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, the hierarchy roles have not been set up yet.",
        )
    SortedRoles = [
        interaction.guild.get_role(int(roleId))
        for roleId in HierarchyRoles
        if interaction.guild.get_role(int(roleId))
    ]
    SortedRoles.sort(key=lambda r: r.position)

    SkipRole = interaction.guild.get_role(int(rank)) if rank else None

    if SkipRole and SkipRole in SortedRoles:
        if interaction.user.top_role.position <= SkipRole.position:
            await msg.edit(
                content=f"{no} **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{SkipRole.name}`.",
            )
            return

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
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{NextRole.name}`.",
        )
        return

    if not NextRole and not SkipRole:
        await msg.edit(
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
            "timestamp": datetime.datetime.now(),
            "annonymous": False,
            "Modmail System": "single",
            "single": {"SkipTo": rank},
        }
    )

    interaction.client.dispatch("promotion", Object.inserted_id, Config)
    await msg.edit(
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

    if not await has_admin_role(interaction, "Promotion Permissions"):
        return
    await interaction.response.defer()
    msg: discord.Message = await interaction.followup.send(
        f"<a:Loading:1167074303905386587> Promoting **@{user.display_name}**...",
    )
    if not await ModuleCheck(interaction.guild.id, "promotions"):
        await interaction.followup.send(
            embed=ModuleNotEnabled(),
            view=Support(),
            ephemeral=True,
        )
        return

    if user is None:
        await msg.edit(
            content=f"{no} **{user.display_name}**, this user cannot be found.",
        )
        return

    if interaction.user.bot:
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you can't promote bots.",
        )
        return

    if interaction.user == user:
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you can't promote yourself.",
        )
        return

    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not Config:
        return await msg.edit(
            embed=BotNotConfigured(),
            view=Support(),
        )
    if not Config.get("Promo", {}).get("channel"):
        return await msg.edit(
            embed=NoChannelSet(),
            view=Support(),
        )

    try:
        channel = await interaction.guild.fetch_channel(
            int(Config.get("Promo", {}).get("channel"))
        )
    except (discord.Forbidden, discord.NotFound):
        return await msg.edit(
            embed=ChannelNotFound(),
            view=Support(),
        )
    if not channel:
        return await msg.edit(
            embed=ChannelNotFound(),
            view=Support(),
        )

    client = await interaction.guild.fetch_member(interaction.client.user.id)
    if channel.permissions_for(client).send_messages is False:
        return await msg.edit(
            embed=NoPermissionChannel(channel),
            view=Support(),
        )
    CallDown, LastPromoted = await CheckCooldown(
        interaction, user, Config.get("Promo", {}).get("Cooldown", None)
    )
    if CallDown:
        Time = int(Config.get("Promo", {}).get("Cooldown", 1))
        Timestamp = int((LastPromoted + datetime.timedelta(days=Time)).timestamp())
        return await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, **@{user.display_name}** is on cooldown, you can promote them again <t:{Timestamp}:R>."
        )

    DepartmentHierarchies = [
        dept
        for sublist in Config.get("Promo", {})
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
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, the department `{department}` does not exist.",
        )
        return

    RoleIDs = department_data.get("ranks", [])
    SortedRoles = [
        interaction.guild.get_role(int(roleId))
        for roleId in RoleIDs
        if interaction.guild.get_role(int(roleId))
    ]
    SortedRoles.sort(key=lambda r: r.position)

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
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{NextRole.name}`.",
        )
        return

    if not NextRole:
        await msg.edit(
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
            "timestamp": datetime.datetime.now(),
            "annonymous": False,
            "Modmail System": "Multi Hierarchy",
            "multi": {"Department": department, "SkipTo": rank},
        }
    )

    interaction.client.dispatch("promotion", Object.inserted_id, Config)
    await msg.edit(
        content=f"{tick} **{interaction.user.display_name}**, I've successfully promoted **@{user.display_name}**!",
    )


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
    await interaction.response.defer()
    if not await has_admin_role(interaction, "Promotion Permissions"):
        return    
    msg: discord.Message = await interaction.followup.send(
        f"<a:Loading:1167074303905386587> Promoting **@{staff.display_name}**...",
    )
    if not await ModuleCheck(interaction.guild.id, "promotions"):
        await interaction.followup.send(
            embed=ModuleNotEnabled(),
            view=Support(),
            ephemeral=True,
        )
        return

    if staff is None:
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, this user cannot be found.",
        )
        return

    if staff.bot:
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you can't promote bots.",
        )
        return

    if interaction.user == staff:
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you can't promote yourself.",
        )
        return

    if interaction.user.top_role <= new:
        await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, you are below the role `{new.name}` and do not have authority to promote this member.",
        )
        return

    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not Config:
        return await msg.edit(
            embed=BotNotConfigured(),
            view=Support(),
        )
    if not Config.get("Promo", {}).get("channel"):
        return await msg.edit(
            embed=NoChannelSet(),
            view=Support(),
        )
    try:
        channel = await interaction.guild.fetch_channel(
            int(Config.get("Promo", {}).get("channel"))
        )
    except (discord.Forbidden, discord.NotFound):
        return await msg.edit(
            embed=ChannelNotFound(),
            view=Support(),
        )
    if not channel:
        return await msg.edit(
            embed=ChannelNotFound(),
            view=Support(),
        )
    client = await interaction.guild.fetch_member(interaction.client.user.id)
    if channel.permissions_for(client).send_messages is False:
        return await msg.edit(
            embed=NoPermissionChannel(channel),
            view=Support(),
        )
    CallDown, LastPromoted = await CheckCooldown(
        interaction, staff, Config.get("Promo", {}).get("Cooldown", None)
    )
    if CallDown:
        Time = int(Config.get("Promo", {}).get("Cooldown", 1))
        Timestamp = int((LastPromoted + datetime.timedelta(days=Time)).timestamp())
        return await msg.edit(
            content=f"{no} **{interaction.user.display_name}**, **@{staff.display_name}** is on cooldown, you can promote them again <t:{Timestamp}:R>."
        )

    Object = await interaction.client.db["promotions"].insert_one(
        {
            "management": interaction.user.id,
            "staff": staff.id,
            "reason": reason,
            "new": new.id,
            "random_string": "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            ),
            "guild_id": interaction.guild.id,
            "jump_url": None,
            "timestamp": datetime.datetime.now(),
            "annonymous": False,
        }
    )

    interaction.client.dispatch("promotion", Object.inserted_id, Config)
    await msg.edit(
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
    import logging

    print("[Promotions] Syncing commands...")
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
