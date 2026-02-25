import discord
from discord.ext import commands
from utils.emojis import *
from discord import app_commands
from datetime import datetime

from utils.permissions import has_admin_role
import random
import re
from utils.Module import ModuleCheck
import asyncio
import logging
from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed, HandleButton
from utils.format import Replace

logger = logging.getLogger(__name__)



async def run(
    ctx: discord.Interaction,
    cmd: str = None,
    data: dict = None,
    channel: discord.TextChannel = None,
):
    await ctx.response.defer(ephemeral=True)
    client = ctx.client

    if not await ModuleCheck(ctx.guild.id, "customcommands"):
        await ctx.followup.send(
            f"{no} **{ctx.user.display_name}**, the custom commands module isn't enabled.",
            ephemeral=True,
        )
        return
    if not data:
        command_data = await client.db["Custom Commands"].find_one(
            {
                "Command" if not cmd else "name": (
                    cmd if not ctx.command else ctx.command.name
                ),
                "guild_id": ctx.guild.id,
            }
        )

        if command_data is None:
            await ctx.followup.send(
                f"{no} **{ctx.user.display_name},** That command does not exist.",
                ephemeral=True,
            )
            return
        command = cmd if not ctx.command else ctx.command.name
    else:
        command_data = data
        command = data.get("Command")

    if not await has_customcommandrole(ctx, command):
        return

    view = None
    if command_data.get("components"):
        view = await HandleButton(command_data)

    timestamp = datetime.utcnow().timestamp()
    replacements = {
        "{author.mention}": ctx.user.mention,
        "{author.name}": ctx.user.display_name,
        "{author.id}": str(ctx.user.id),
        "{timestamp}": f"<t:{int(timestamp)}:F>",
        "{guild.name}": ctx.guild.name,
        "{guild.id}": str(ctx.guild.id),
        "{guild.owner.mention}": ctx.guild.owner.mention if ctx.guild.owner else "",
        "{guild.owner.name}": (ctx.guild.owner.display_name if ctx.guild.owner else ""),
        "{guild.owner.id}": str(ctx.guild.owner.id) if ctx.guild.owner else "",
        "{random}": str(random.randint(1, 1000000)),
        "{guild.members}": str(ctx.guild.member_count),
        "{channel.name}": channel.name if channel else ctx.channel.name,
        "{channel.id}": str(channel.id) if channel else str(ctx.channel.id),
        "{channel.mention}": channel.mention if channel else ctx.channel.mention,
    }

    content = Replace(command_data.get("content", ""), replacements)
    embed = None
    if command_data.get("embed"):
        embed = await DisplayEmbed(command_data, None, replacements)
    target_channel = channel or ctx.channel
    try:
        if not cmd:
            msg = await target_channel.send(
                content,
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(
                    everyone=True, users=True, roles=True
                ),
            )
            await ctx.followup.send(
                f"{tick} **{ctx.user.display_name},** The command has been sent",
                ephemeral=True,
            )
        else:
            await ctx.followup.send(
                content,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    everyone=True, users=True, roles=True
                ),
                ephemeral=True,
            )

    except discord.Forbidden:
        await ctx.followup.send(
            f"{no} **{ctx.user.display_name},** I do not have permission to send messages in that channel.",
            ephemeral=True,
        )
        return

    loggingdata = await client.db["Commands Logging"].find_one(
        {"guild_id": ctx.guild.id}
    )
    if loggingdata:
        loggingchannel = client.get_channel(loggingdata["channel_id"])
        if loggingchannel:
            log_embed = discord.Embed(
                title="Custom Command Usage",
                description=f"Command **{command}** was used by {ctx.user.mention} in {ctx.channel.mention}",
                color=discord.Color.dark_embed(),
            )
            log_embed.set_author(
                name=ctx.user.display_name, icon_url=ctx.user.display_avatar
            )
            try:
                await loggingchannel.send(embed=log_embed)
            except (discord.Forbidden, discord.HTTPException):
                logger.warning(
                    f"I could not send the log message in the specified channel (guild: {ctx.guild.name})"
                )


async def SyncCommand(self: commands.Bot, name: str, guild: int):
    Stripped = name.strip().lower()
    Stripped = Stripped.lstrip("/")
    Stripped = Stripped.replace(" ", "_")
    Stripped = re.sub(r"[^a-z0-9\-_]", "", Stripped)
    if not (1 <= len(Stripped) <= 32):
        return

    async def command_callback(interaction: discord.Interaction):
        await run(interaction)

    try:
        Command = app_commands.Command(
            name=Stripped, description="[Custom CMD]", callback=command_callback
        )

        await self.db["Custom Commands"].update_one(
            {"name": name, "guild_id": guild},
            {
                "$set": {
                    "Command": Command.qualified_name,
                }
            },
        )
        self.tree.add_command(Command, guild=discord.Object(id=guild))
        await self.tree.sync(guild=discord.Object(id=guild))

    except discord.app_commands.errors.CommandAlreadyRegistered:
        return
    except Exception as e:
        logger.error(f"Error syncing command '{name}' in guild {guild}: {e}")


async def Unsync(self: commands.Bot, name: str, guild: int):
    try:
        self.tree.remove_command(name, guild=discord.Object(id=guild))
        await self.tree.sync(guild=discord.Object(id=guild))
    except discord.errors.NotFound:
        pass
    return


class CustomCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        # await self.RegisterCustomCommands()
        pass

    @commands.command()
    async def prefix(self, ctx: commands.Context, prefix: str = None):
        result = await self.client.db["prefixes"].find_one({"guild_id": ctx.guild.id})
        if result:

            currentprefix = result.get("prefix", "!!")
        else:
            currentprefix = "!!"

        if prefix is None:

            await ctx.send(
                f"<:command1:1223062616872583289> **{ctx.author.display_name},** the prefix is `{currentprefix}`",
            )
        else:
            if ctx.author.guild_permissions.manage_guild:

                await self.client.db["prefixes"].update_one(
                    {"guild_id": ctx.guild.id},
                    {"$set": {"prefix": prefix}},
                    upsert=True,
                )
                await ctx.send(
                    f"<:whitecheck:1190819388941668362> **{ctx.author.display_name},** I've set the prefix to `{prefix}`",
                )
            else:
                await ctx.send(
                    f"<:command1:1223062616872583289> **{ctx.author.display_name},** the prefix is `{currentprefix}`",
                )

    async def RegisterCustomCommands(self):
        filter = {}
        if os.getenv("CUSTOM_GUILD"):
            filter["guild_id"] = int(os.getenv("CUSTOM_GUILD"))

        customcommands = (
            await self.client.db["Custom Commands"].find(filter).to_list(length=None)
        )
        GuildsToSync = set()
        SyncedServers = 0

        for command in customcommands:
            Raw = None
            guild_id = None
            try:
                ActualRaw = command.get('name')
                Raw = command.get("name", "").strip().lower()
                guild_id = command.get("guild_id")
            except (KeyError, AttributeError):
                continue
            if not guild_id:
                continue

            Command = Raw.strip().lower().replace(" ", "_")
            Command = re.sub(r"[^a-z0-9\-_]", "", Command)
            if not (1 <= len(Command) <= 32):
                continue

            async def command_callback(interaction: discord.Interaction):
                await run(interaction)

            Command = app_commands.Command(
                name=Command, description="[Custom CMD]", callback=command_callback
            )

            try:
                command = self.client.tree.add_command(
                    Command, guild=discord.Object(id=guild_id)
                )
            except discord.app_commands.errors.CommandAlreadyRegistered:
                continue

            if Command and Command.name:
                await self.client.db["Custom Commands"].update_one(
                    {"name": ActualRaw, "guild_id": guild_id},
                    {
                        "$set": {
                            "Command": Command.name,
                        }
                    },
                )
            GuildsToSync.add(guild_id)

        for guild_id in GuildsToSync:
            try:
                await self.client.tree.sync(guild=discord.Object(id=guild_id))

            except Exception as e:
                continue

            except (
                TypeError,
                discord.errors.NotFound,
                discord.errors.Forbidden,
                ValueError,
            ):
                continue
            SyncedServers += 1
            await asyncio.sleep(3)
        logger.info("[💻] Finished Syncing Custom Commands")

    @staticmethod
    async def replace_variables(message, replacements):
        for placeholder, value in replacements.items():
            if value is not None:
                message = str(message).replace(placeholder, str(value))
            else:
                message = str(message).replace(placeholder, "")
        return message


class Voting(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="0",
        style=discord.ButtonStyle.green,
        emoji="<:whitecheck:1223062421212631211>",
        custom_id="vote",
    )
    async def upvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        message_id = interaction.message.id

        voting = await interaction.client.db["Commands Voting"].find_one(
            {"message_id": message_id}
        ) or {
            "votes": 0,
            "Voters": [],
        }
        if interaction.user.id in voting["Voters"]:
            await interaction.client.db["Commands Voting"].update_one(
                {"message_id": message_id},
                {
                    "$inc": {"votes": -1},
                    "$pull": {"Voters": interaction.user.id},
                },
            )
            button.label = str(voting["votes"] - 1)
            await interaction.message.edit(view=self)
            await interaction.followup.send(
                f"{tick} **{interaction.user.display_name},** You have successfully unvoted.",
                ephemeral=True,
            )
        else:
            await interaction.client.db["Commands Voting"].update_one(
                {"message_id": message_id},
                {
                    "$inc": {"votes": 1},
                    "$push": {"Voters": interaction.user.id},
                },
                upsert=True,
            )
            button.label = str(voting["votes"] + 1)
            await interaction.message.edit(view=self)
            await interaction.followup.send(
                f"{tick} **{interaction.user.display_name},** You have successfully voted.",
                ephemeral=True,
            )

    @discord.ui.button(
        label="Voters",
        style=discord.ButtonStyle.blurple,
        emoji="<:folder:1235296135728594965>",
        custom_id="viewlist",
    )
    async def list(self, interaction: discord.Interaction, button: discord.ui.Button):
        voting = await interaction.client.db["Commands Voting"].find_one(
            {"message_id": interaction.message.id}
        )
        voters = voting.get("Voters", [])
        if not voters:
            voters_str = f"**{interaction.user.display_name},** there are no voters!"
        else:
            voters_str = "\n".join([f"<@{voter}> ({voter})" for voter in voters])

        embed_description = str(voters_str)[:4096]
        embed = discord.Embed(
            title="Voters",
            description=embed_description,
            color=discord.Color.dark_embed(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def has_customcommandrole(ctx, command):
    if isinstance(ctx, discord.Interaction):
        author = ctx.user
        send = ctx.followup.send
        client = ctx.client
    else:
        author = ctx.author
        send = ctx.send
        client = ctx.client

    filter = {"guild_id": ctx.guild.id, "name": command}
    role_data = await client.db["Custom Commands"].find_one(filter)

    if role_data and "permissionroles" in role_data:
        role_ids = role_data["permissionroles"]
        if not isinstance(role_ids, list):
            role_ids = [role_ids]

        if any(role.id in role_ids for role in author.roles):
            return True
        else:
            await send(
                f"{no} **{author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Custom Command Permission`"
            )
            return False
    else:

        return await has_admin_role(ctx)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(CustomCommands(client))
