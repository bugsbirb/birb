import discord
from discord.ext import commands
from utils.emojis import *
import os
import sentry_sdk

SupportRoles = (
    [int(x) for x in os.getenv("SUPPORT").split(",")] if os.getenv("SUPPORT") else []
)


class SupportCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    def SupportPermissions(self, ctx: commands.Context) -> bool:
        if self.client.owner_id == ctx.author.id:
            return True
        if any(role.id in SupportRoles for role in ctx.author.roles):
            return True
        return False

    @commands.command()
    async def error(self, ctx: commands.Context, errorId: str):
        if not self.SupportPermissions(ctx):
            return
        error = await self.client.db["errors"].find_one({"error_id": errorId})
        if not error:
            return await ctx.send(
                f"` ❌ ` **{ctx.author.display_name},** I can't find this error."
            )
        try:
            await ctx.message.add_reaction("✉️")
        except discord.Forbidden:
            return
        try:
            content = f"` 🐛 ` `{errorId}` (Traceback Snippet)\n\n```\n{error.get('error')}\n```\n\n> This is confidential and must only be shared with support & devs.\n> You can use this error to debug the issue they are dealing with, or to tell devs about it,"
            await ctx.author.send(
                content=content,
            )
        except discord.Forbidden:
            return

    @commands.command()
    async def ebg(self, ctx: commands.Context, guild: str):
        if not self.SupportPermissions(ctx):
            return
        errors = (
            await self.client.db["errors"]
            .find({"guild_id": int(guild)})
            .sort("_id", -1)
            .limit(5)
            .to_list(length=5)
        )
        if not errors:
            return await ctx.send(
                f"` ❌ ` **{ctx.author.display_name},** I can't find any errors."
            )
        try:
            await ctx.message.add_reaction("✉️")
        except discord.Forbidden:
            return
        try:
            content = f"` 🐛 ` **Recent Errors** ({guild})\n"
            for error in errors:
                content += f"➤ `{error.get('error_id')}`\n"
            await ctx.author.send(content=content)
        except discord.Forbidden:
            return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SupportCog(client))
