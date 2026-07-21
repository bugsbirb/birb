from typing import Optional, Literal

import psutil
from discord.ext import commands

from core.bot.emojis import *


class management(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command()
    @commands.is_owner()
    async def version(self, ctx: commands.Context, v: str):
        await self.client.db["Support Variables"].update_one(
            {"_id": 1}, {"$set": {"version": v}}, upsert=True
        )

    @commands.command()
    @commands.is_owner()
    async def vps(self, ctx: commands.Context):
        await ctx.defer()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        embed = (
            discord.Embed(color=discord.Color.dark_embed())
            .add_field(
                name="`🧠` Memory",
                value=f"> `Total:` {memory.total / 1e9:.2f} GB\n> `Available:` {memory.available / 1e9:.2f} GB\n> `Usage:` {memory.percent}%",
                inline=False,
            )
            .add_field(
                name="` 💫 ` CPU Usage", value=f"{psutil.cpu_percent()}%", inline=False
            )
            .add_field(
                name="` 💿 ` Disk",
                value=f"> `Total:` {disk.total / 1e9:.2f} GB\n> `Used:` {disk.used / 1e9:.2f} GB\n> `Usage:` {disk.percent}%",
                inline=False,
            )
        )
        await ctx.author.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def say(self, ctx: commands.Context, *, message: str):
        channel = ctx.channel
        await channel.send(message)
        await ctx.message.delete()

    @commands.group()
    @commands.is_owner()
    async def features(self, ctx: commands.Context):
        return

    @features.command()
    @commands.is_owner()
    async def add(self, ctx: commands.Context, server: int, *, feature: str):
        await self.client.db["Config"].update_one(
            {"_id": server}, {"$addToSet": {"Features": feature}}, upsert=True
        )
        await ctx.send(
            f"` ✅ ` **{ctx.author.display_name},** feature added to server `{server}`."
        )

    @features.command()
    @commands.is_owner()
    async def remove(self, ctx: commands.Context, server: int, *, features: str):
        await self.client.db["Config"].update_one(
            {"_id": server}, {"$pull": {"Features": features}}, upsert=True
        )
        await ctx.send(
            f"` ❌ ` **{ctx.author.display_name},** feature removed from server `{server}`."
        )

    @commands.command()
    @commands.is_owner()
    async def analytics(self, ctx: commands.Context):
        result = await self.client.db["analytics"].find({}).to_list(length=None)

        content = ""
        for x in result:
            for key, value in x.items():
                if key != "_id":
                    content += f"{key}: {value}\n"
            content += "\n"
            with open("analytics.txt", "w", encoding="utf-8") as file:
                file.write(content)

            await ctx.send(file=discord.File("analytics.txt"))

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ) -> None:

        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(management(client))
