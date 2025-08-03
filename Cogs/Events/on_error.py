import discord
from discord.ext import commands
from datetime import datetime
from utils.emojis import *
from discord import app_commands
import string
from utils.HelpEmbeds import *
import random
import traceback


class Tree(app_commands.CommandTree):
    async def on_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError | Exception,
    ):
        if interaction.command:
            if isinstance(error, app_commands.errors.CommandNotFound):

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

        else:
            await super().on_error(interaction, error)


class On_error(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.Start = datetime.now()

    async def ErrorResponse(self, ctx_or_interaction, error: Exception):
        try:
            if isinstance(ctx_or_interaction, commands.Context):
                author = ctx_or_interaction.author
                guild = ctx_or_interaction.guild
                send = ctx_or_interaction.send
                command = ctx_or_interaction.command
            elif isinstance(ctx_or_interaction, discord.Interaction):
                author = ctx_or_interaction.user
                guild = ctx_or_interaction.guild
                send = ctx_or_interaction.response.send_message
                command = ctx_or_interaction.command
            else:
                return

            if isinstance(error, commands.NoPrivateMessage):
                await send(
                    f"{no} **{author.display_name},** I can't execute commands in DMs. Please use me in a server.",
                    ephemeral=(
                        True
                        if isinstance(ctx_or_interaction, discord.Interaction)
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
                        if isinstance(ctx_or_interaction, discord.Interaction)
                        else False
                    ),
                )
                return
            if isinstance(error, commands.MemberNotFound):
                await send(
                    f"{no} **{author.display_name}**, that member isn't in the server.",
                    ephemeral=(
                        True
                        if isinstance(ctx_or_interaction, discord.Interaction)
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
                        if isinstance(ctx_or_interaction, discord.Interaction)
                        else False
                    ),
                )
                return
            if isinstance(error, commands.BadArgument):
                return

            if guild is None:
                return
            error_id = "".join(random.choices(string.digits, k=24))
            error_id = f"error-{error_id}"
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
                description=f"Error ID: `{error_id}`",
                color=discord.Color.brand_red(),
            )

            await send(
                embed=embed,
                view=view,
                ephemeral=(
                    True
                    if isinstance(ctx_or_interaction, discord.Interaction)
                    else False
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
