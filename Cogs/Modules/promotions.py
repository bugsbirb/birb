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



from dotenv import load_dotenv

load_dotenv()

environment = os.getenv("ENVIRONMENT")

from utils.HelpEmbeds import (
    BotNotConfigured,
    NoPermissionChannel,
    ChannelNotFound,
    ModuleNotEnabled,
    NoChannelSet,
    Support,
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
    if interaction.client.promotions_maintenance is True:
        await interaction.response.send_message(
            f"  **{interaction.user.display_name}**, the promotions module is currently under maintenance. Please try again later.",
            ephemeral=True,
        )
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

    if not await has_admin_role(interaction, "Promotion Permissions"):
        return

    if user is None:
        await msg.edit(
            content=f"  **{user.display_name}**, this user cannot be found.",
        )
        return

    if interaction.user.bot:
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, you can't promote bots.",
        )
        return

    if interaction.user == user:
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, you can't promote yourself.",
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

    HierarchyRoles = (
        Config.get("Promo", {}).get("System", {}).get("single", {}).get("Hierarchy", [])
    )
    if not HierarchyRoles:
        return await msg.edit(
            content=f"  **{interaction.user.display_name}**, the hierarchy roles have not been set up yet.",
        )
    SortedRoles = [
        interaction.guild.get_role(int(role_id))
        for role_id in HierarchyRoles
        if interaction.guild.get_role(int(role_id))
    ]
    SortedRoles.sort(key=lambda role: role.position)

    SkipRole = interaction.guild.get_role(int(rank)) if rank else None

    if SkipRole and SkipRole in SortedRoles:
        if interaction.user.top_role.position <= SkipRole.position:
            await msg.edit(
                content=f"  **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{SkipRole.name}`.",
            )
            return

    NextRole = None
    for index, role in enumerate(SortedRoles):
        if role in user.roles:
            if index + 1 < len(SortedRoles):
                NextRole = SortedRoles[index + 1]
        break
    if NextRole:
        if interaction.user.top_role.position <= NextRole.position:
            await msg.edit(
                content=f"  **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{NextRole.name}`.",
            )
            return

    if not NextRole and not SkipRole:
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, **@{user.display_name}** is already at the top of the hierarchy and cannot be promoted further.",
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
        content=f"  **{interaction.user.display_name}**, I've successfully promoted **@{user.display_name}**!",
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
    if interaction.client.promotions_maintenance is True:
        await interaction.response.send_message(
            f"  **{interaction.user.display_name}**, the promotions module is currently under maintenance. Please try again later.",
            ephemeral=True,
        )
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

    if not await has_admin_role(interaction, "Promotion Permissions"):
        return

    if user is None:
        await msg.edit(
            content=f"  **{user.display_name}**, this user cannot be found.",
        )
        return

    if interaction.user.bot:
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, you can't promote bots.",
        )
        return

    if interaction.user == user:
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, you can't promote yourself.",
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
            content=f"  **{interaction.user.display_name}**, the department `{department}` does not exist.",
        )
        return

    RoleIDs = department_data.get("ranks", [])
    SortedRoles = [
        interaction.guild.get_role(int(role_id))
        for role_id in RoleIDs
        if interaction.guild.get_role(int(role_id))
    ]
    SortedRoles.sort(key=lambda role: role.position)

    SkipRole = interaction.guild.get_role(int(rank)) if rank else None
    if SkipRole and SkipRole in SortedRoles:
        if interaction.user.top_role.position <= SkipRole.position:
            await msg.edit(
                content=f"  **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{SkipRole.name}`.",
            )
            return

    NextRole = None
    for index, current_role in enumerate(SortedRoles):
        if current_role in user.roles and index + 1 < len(SortedRoles):
            NextRole = SortedRoles[index + 1]
            if interaction.user.top_role.position <= NextRole.position:
                await msg.edit(
                    content=f"  **{interaction.user.display_name}**, you are not authorized to promote **{user.display_name}** to `{NextRole.name}`.",
                )
                return

    if not NextRole and not SkipRole:
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, **@{user.display_name}** is already at the top of the hierarchy and cannot be promoted further.",
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
        content=f"  **{interaction.user.display_name}**, I've successfully promoted **@{user.display_name}**!",
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
    if interaction.client.promotions_maintenance is True:
        await interaction.response.send_message(
            f"  **{interaction.user.display_name}**, the promotions module is currently under maintenance. Please try again later.",
            ephemeral=True,
        )
        return
    await interaction.response.defer()
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

    if not await has_admin_role(interaction, "Promotion Permissions"):
        return

    if staff is None:
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, this user cannot be found.",
        )
        return

    if staff.bot:
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, you can't promote bots.",
        )
        return

    if interaction.user == staff:
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, you can't promote yourself.",
        )
        return

    if interaction.user.top_role <= new:
        await msg.edit(
            content=f"  **{interaction.user.display_name}**, you are below the role `{new.name}` and do not have authority to promote this member.",
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
        content=f"  **{interaction.user.display_name}**, I've successfully promoted **@{staff.display_name}** to `{new.name}`!",
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
        if CO.get("_id") == 1092976553752789054:
            continue
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


class promo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command()
    async def pdebug(self, ctx: commands.Context):
        await ctx.send(f"{SyncedAmount}/{TotalNeedingSynced}")

    @commands.hybrid_command(description="View a staff member's promotions")
    @app_commands.describe(staff="The staff member to view promotion for")
    async def promotions(self, ctx: commands.Context, staff: discord.User):
        await ctx.defer()
        if self.client.promotions_maintenance:
            await ctx.send(
                f"  **{ctx.author.display_name}**, the promotions module is currently under maintenance. Please try again later.",
            )
            return

        if not await ModuleCheck(ctx.guild.id, "promotions"):
            await ctx.send(
                embed=ModuleNotEnabled(),
                view=Support(),
            )
            return

        if not await has_staff_role(ctx, "Promotion Permissions"):
            return

        embeds = []
        filter = {
            "guild_id": ctx.guild.id,
            "staff": staff.id,
        }
        Promotions = await self.client.db["promotions"].find(filter).to_list(750)
        if not len(Promotions) > 0:
            await ctx.send(
                f"  **{ctx.author.display_name}**, this staff member doesn't have any promotions.",
            )
            return

        msg = await ctx.send(
            embed=discord.Embed(
                description="<a:astroloading:1245681595546079285>",
                color=discord.Color.dark_embed(),
            )
        )

        embed = discord.Embed(
            color=discord.Color.dark_embed(),
        )
        embed.set_thumbnail(url=staff.display_avatar)
        embed.set_author(icon_url=staff.display_avatar, name=staff.display_name)

        for i, promotion in enumerate(Promotions):
            jump_url = promotion.get("jump_url", "")
            if jump_url:
                jump_url = f"\n> **[Jump to Promotion]({jump_url})**"

            value = f"> **Promoted By:** <@{promotion['management']}>\n> **New:** <@&{promotion.get('new', 'Unknown')}>\n> **Reason:** {promotion.get('reason')}{jump_url}"
            if len(value) > 1024:
                value = value[:1021] + "..."
            embed.add_field(
                name=f"<:Document:1223063264322125844> Promotion | {promotion['random_string']}",
                value=value,
                inline=False,
            )

            if (i + 1) % 9 == 0 or i == len(Promotions) - 1:
                embeds.append(embed)
                embed = discord.Embed(
                    title=f"{staff.name}'s Promotions",
                    description=f"* **User:** {staff.mention}\n* **User ID:** {staff.id}",
                    color=discord.Color.dark_embed(),
                )
                embed.set_thumbnail(url=staff.display_avatar)
                embed.set_author(icon_url=staff.display_avatar, name=staff.display_name)
        paginator = await PaginatorButtons()
        await paginator.start(ctx, pages=embeds, msg=msg)


class PromotionIssuer(discord.ui.View):
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
    await client.add_cog(promo(client))
