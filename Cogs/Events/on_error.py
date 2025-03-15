import discord
from discord.ext import commands
from datetime import datetime
from utils.emojis import *
import string
import random
import traceback



class On_error(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: Exception):
            print('kk')
            if isinstance(error, discord.app_commands.errors.CommandNotFound):
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Command Not Found",
                        description="The command may be syncing. Please wait.",
                        color=discord.Color.red(),
                    )
                )
            


    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):

        # if environment == "development":
        #     return
        try:
            if isinstance(error, commands.NoPrivateMessage):
                await ctx.send(
                    f"  **{ctx.author.display_name},** I can't execute commands in DMs. Please use me in a server."
                )
                return
            if isinstance(error, commands.CommandNotFound):
                return
            if isinstance(error, commands.NotOwner):
                return

            if isinstance(error, commands.BadLiteralArgument):
                await ctx.send(
                    f"  **{ctx.author.display_name}**, you have used an invalid argument."
                )
                return
            if isinstance(error, commands.MemberNotFound):
                await ctx.send(
                    f"  **{ctx.author.display_name}**, that member isn't in the server."
                )
                return
            if isinstance(error, commands.MissingPermissions):
                return
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(
                    f"  **{ctx.author.display_name}**, you are missing a requirement."
                )
                return
            if isinstance(error, commands.BadArgument):
                return

            if ctx.guild is None:
                return
            error_id = "".join(random.choices(string.digits, k=24))
            error_id = f"error-{error_id}"
            TRACEBACK = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            ERROR = str(error)
            await self.client.db['errors'].insert_one(
                {
                    "error_id": error_id,
                    "error": ERROR,
                    "traceback": TRACEBACK,
                    "timestamp": datetime.now(),
                    "guild_id": ctx.guild.id,
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

            await ctx.send(embed=embed, view=view)
            Channel = self.client.get_channel(1333545239930994801)
            embed = discord.Embed(
                title="",
                description=f"```py\n{TRACEBACK}```",
                color=discord.Color.dark_embed(),
            )
            embed.add_field(
                name="Extra Information",
                value=f">>> **Guild:** {ctx.guild.name} (`{ctx.guild.id}`)\n**Command:** {ctx.command.qualified_name}\n**Timestamp:** <t:{int(datetime.now().timestamp())}>",
                inline=False,
            )
            embed.set_footer(text=f"Error ID: {error_id}")
            msg = await Channel.send(embed=embed)
            await self.client.db['errors'].update_one(
                {"error_id": error_id}, {"$set": {"MsgLink": msg.jump_url}}
            )
            return
        except discord.Forbidden:
            return
        except discord.HTTPException:
            return
        except discord.ClientException:
            return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(On_error(client))
