import discord
from discord.ext import commands
import os
from core.discord.ui import YesOrNo, BasicPaginator

AdminRoles = (
    [int(x) for x in os.getenv("STAFF").split(",")] if os.getenv("STAFF") else []
)


class AdminCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    def AdminPermission(self, ctx: commands.Context) -> bool:
        if self.client.owner_id == ctx.author.id:
            return True
        if ctx.author.id in AdminRoles:
            return True
        return False

    @commands.command()
    async def leave(self, ctx: commands.Context, id: str):
        if not self.AdminPermission(ctx):
            return

        guild = self.client.get_guild(int(id))
        if not guild:
            return await ctx.send(
                f"` ❌ ` **{ctx.author.display_name},** I couldn't find the guild."
            )
        try:
            await guild.leave()
        except:
            return await ctx.send(
                f"` ❌ ` **{ctx.author.display_name},** I couldn't leave the guild."
            )
        await ctx.send(
            f"` ✅ ` **{ctx.author.display_name},** I have left the guild ({guild.name} | `{guild.id}`)."
        )

    @commands.command()
    async def guilds(self, ctx: commands.Context):
        if not self.AdminPermission(ctx):
            return

        guilds = self.client.guilds
        if len(guilds) == 0:
            return await ctx.send(
                f"` ❌ ` **{ctx.author.display_name},** I am not in any guilds."
            )
        description = ""
        messages = []
        for guild in guilds:
            description += f"➤ **@{guild.name}** | `{guild.id}`\n"
            if len(description.split("\n")) >= 10:
                messages.append(description)
                description = ""

        if description:
            messages.append(description)

        await ctx.send(
            content=messages[0],
            view=BasicPaginator(author=ctx.author, messages=messages),
        )

    @commands.command()
    async def whitelist(self, ctx: commands.Context, id: str):
        if not self.AdminPermission(ctx):
            return

        AlreadyRegistered = await self.client.db["whitelist"].find_one({"_id": id})
        if AlreadyRegistered:
            return await ctx.send(
                f"` ❌ ` **{ctx.author.display_name},** this guild is already whitelisted."
            )
        await self.client.db["whitelist"].insert_one({"_id": id})
        await ctx.send(
            f"` ✅ ` **{ctx.author.display_name},** this guild has been whitelisted."
        )

    @commands.command()
    async def unwhitelist(self, ctx: commands.Context, id: str):
        if not self.AdminPermission(ctx):
            return

        AlreadyRegistered = await self.client.db["whitelist"].find_one({"_id": id})
        if not AlreadyRegistered:
            return await ctx.send(
                f"` ❌ ` **{ctx.author.display_name},** this guild is not whitelisted."
            )
        await self.client.db["whitelist"].delete_one({"_id": id})
        view = YesOrNo(ctx.author)

        guild = self.client.get_guild(int(id))

        msg = await ctx.send(
            f"` ✅ ` **{ctx.author.display_name},** this guild has been unwhitelisted.",
            view=view,
            embed=(
                discord.Embed(
                    description="Would you like to remove this the bot from this server?",
                    color=discord.Color.dark_theme(),
                )
                .set_thumbnail(url=guild.icon)
                .add_field(
                    name=f"@{guild.name}",
                    value=f"> **ID:** {guild.id}\n> **Members:** {guild.member_count}\n> **Owner:** <@{guild.owner_id}>\n> **Created:** <t:{int(guild.created_at.timestamp())}:F>",
                )
                if guild
                else None
            ),
        )

        if not guild:
            return
        await view.wait()
        if view.value is None:
            return
        if view.value:
            if not guild:
                return await msg.edit(
                    content=f"` ❌ ` **{ctx.author.display_name},** this guild doesn't have the bot in it."
                )
            try:
                await guild.leave()
            except:
                return await msg.edit(
                    content=f"` ❌ ` **{ctx.author.display_name},** I couldn't leave the guild."
                )
            await msg.edit(
                content=f"` ✅ ` **{ctx.author.display_name},** this guild has been unwhitelisted and the bot has been kicked from the guild.",
                view=None,
            )
        else:
            await msg.edit(
                content=f"` ✅ ` **{ctx.author.display_name},** this guild has been unwhitelisted.",
                view=None,
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(AdminCog(client))
