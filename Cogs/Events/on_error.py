import discord
from discord.ext import commands
from datetime import datetime
from utils.emojis import *
from discord import app_commands
import string
from utils.HelpEmbeds import *
import random
import traceback
import sentry_sdk
import os


class Tree(app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction):
        if self.client.maintenance is True:
            await interaction.response.send_message(
                embed=GlobalMaintenance(self.client.maintenanceReason), view=Support()
            )
            return False
        return True

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError | Exception,
    ):

        if isinstance(error, app_commands.errors.CommandNotFound):
            try:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        color=discord.Color.brand_red(),
                        description="```\nApplication command 'promote' not found\n```",
                    ).add_field(
                        name="<:Help:1184535847513624586> How To Fix",
                        value=(
                            f"> 1. Wait a bit; the bot may be loading commands. "
                            f"(Started: <t:{int(self.client.launch_time.timestamp())}:R>)\n"
                            "> 2. Go to /config -> Modules -> Enable and disable the promotion module."
                        ),
                    ),
                    ephemeral=True,
                )
            except discord.HTTPException:
                pass
        elif isinstance(error, app_commands.errors.CommandInvokeError):
            pass

        else:
            await super().on_error(interaction, error)


class On_error(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.Start = datetime.now()
        self.client.add_check(self.CheckStatus)

    async def CheckStatus(self, ctx: commands.Context):
        if self.client.maintenance:
            await ctx.send(
                embed=GlobalMaintenance(self.client.maintenanceReason), view=Support()
            )
            return False
        return True

    async def ErrorResponse(self, interactionType, error: Exception):
        if self.client.maintenance:
            return
        try:
            if isinstance(interactionType, commands.Context):
                author = interactionType.author
                channel = interactionType.channel
                guild = interactionType.guild
                send = interactionType.send
                command = interactionType.command
            elif isinstance(interactionType, discord.Interaction):
                author = interactionType.user
                guild = interactionType.guild
                channel = interactionType.channel

                if not interactionType.response.is_done():
                    await interactionType.response.defer(ephemeral=True)
                send = interactionType.followup.send
                command = interactionType.command
            else:
                return

            if isinstance(error, commands.NoPrivateMessage):
                await send(
                    f"{no} **{author.display_name},** I can't execute commands in DMs. Please use me in a server.",
                    ephemeral=(
                        True
                        if isinstance(interactionType, discord.Interaction)
                        else False
                    ),
                )
                return
            if isinstance(error, commands.CommandNotFound):
                return
            if isinstance(error, commands.NotOwner):
                return
            if isinstance(error, commands.BadLiteralArgument):
                await send(
                    f"{no} **{author.display_name}**, you have used an invalid argument.",
                    ephemeral=(
                        True
                        if isinstance(interactionType, discord.Interaction)
                        else False
                    ),
                )
                return
            if isinstance(error, commands.MemberNotFound):
                await send(
                    f"{no} **{author.display_name}**, that member isn't in the server.",
                    ephemeral=(
                        True
                        if isinstance(interactionType, discord.Interaction)
                        else False
                    ),
                )
                return
            if isinstance(error, commands.MissingPermissions):
                return
            if isinstance(error, commands.MissingRequiredArgument):
                await send(
                    f"{no} **{author.display_name}**, you are missing a requirement.",
                    ephemeral=(
                        True
                        if isinstance(interactionType, discord.Interaction)
                        else False
                    ),
                )
                return
            if isinstance(error, commands.BadArgument):
                return

            if guild is None:
                return
            errorId = self.captureSentry(
                error,
                {
                    "guildId": guild.id,
                    "authorId": author.id,
                    "channelId": channel.id,
                    "command": (command.qualified_name if command else "unknown"),
                },
            )
            sentry = True if errorId != None else False
            error_id = (
                errorId or f"error-{''.join(random.choices(string.digits, k=24))}"
            )
            TRACEBACK = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            ERROR = str(error)
            await self.client.db["errors"].insert_one(
                {
                    "error_id": error_id,
                    "error": ERROR,
                    "traceback": TRACEBACK,
                    "timestamp": datetime.now(),
                    "guild_id": guild.id,
                    "sentry": sentry,
                }
            )
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Contact Support",
                    style=discord.ButtonStyle.link,
                    url="https://discord.gg/DhWdgfh3hN",
                )
            )
            embed = discord.Embed(
                title="<:x21:1214614676772626522> Command Error",
                description=f"Error ID: `{error_id}`\n-# We can't fix bugs without you, please report this to our support services.",
                color=discord.Color.brand_red(),
            )

            await send(
                embed=embed,
                view=view,
                ephemeral=(
                    True if isinstance(interactionType, discord.Interaction) else False
                ),
            )
            Channel = self.client.get_channel(1333545239930994801)
            embed = discord.Embed(
                title="",
                description=f"```py\n{TRACEBACK}```",
                color=discord.Color.dark_embed(),
            )
            embed.add_field(
                name="Extra Information",
                value=f">>> **Guild:** {guild.name} (`{guild.id}`)\n**Command:** {command.qualified_name if command else 'Unknown'}\n**Timestamp:** <t:{int(datetime.now().timestamp())}>",
                inline=False,
            )
            embed.set_footer(text=f"Error ID: {error_id}")
            msg = await Channel.send(embed=embed)
            await self.client.db["errors"].update_one(
                {"error_id": error_id}, {"$set": {"MsgLink": msg.jump_url}}
            )
            return
        except discord.Forbidden:
            return
        except discord.HTTPException:
            return
        except discord.ClientException:
            return

    def captureSentry(self, error, info: dict):
        if not os.getenv("SENTRY_URL"):
            return None
        sentry_sdk.metrics.count(
            "errorCount", 1, attributes={"command": info.get("command", "unknown")}
        )
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("authorId", str(info.get("authorId", 0)))
            scope.set_tag("guildId", str(info.get("guildId", 0)))
            scope.set_tag("channelId", str(info.get("channelId", 0)))
            scope.set_tag("command", info.get("command", "unknown"))

            eventId = sentry_sdk.capture_exception(error)
            return eventId

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        await self.ErrorResponse(ctx, error)

    @commands.Cog.listener()
    async def on_application_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        await self.ErrorResponse(interaction, error)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(On_error(client))
