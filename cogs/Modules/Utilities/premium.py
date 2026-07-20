import discord
from discord.ext import commands
from core.integrations.patreon import SubscriptionUser


class Premium(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(description="Run this command after purchasing premium.")
    async def premium(self, ctx: commands.Context):

        msg = await ctx.send(
            embed=discord.Embed(
                color=discord.Color.yellow(),
                description="Checking membership status...",
            ).set_author(
                name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url
            )
        )

        try:
            user, _, HasPremium = await SubscriptionUser(
                UserID=ctx.author.id, Tiers=["22733636", "22855340"]
            )
        except Exception:
            await msg.edit(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description="An error occurred while checking your Patreon status.",
                ).set_author(
                    name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url
                )
            )
            return

        if not user or not user.get("attributes", {}).get("social_connections", {}).get(
            "discord"
        ):
            await msg.edit(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description="Could not find your Patreon account. Please link your account first.",
                ).set_author(
                    name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url
                )
            )
            return

        if HasPremium:
            await msg.edit(
                embed=discord.Embed(
                    color=discord.Color.green(),
                    description="You have an active Premium membership. Your perks have been granted! Now, run `/config` in a server to activate your benefits.",
                ).set_author(
                    name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url
                )
            )
            await self.client.db["Subscriptions"].update_one(
                {"user": ctx.author.id},
                {
                    "$set": {
                        "user": ctx.author.id,
                        "guilds": [],
                        "created": discord.utils.utcnow(),
                        "Tokens": 1,
                    }
                },
                upsert=True,
            )
        else:
            await msg.edit(
                embed=discord.Embed(
                    color=discord.Color.orange(),
                    description="You do not have an active Premium membership. [Learn more](https://www.patreon.com/astrobirb)",
                ).set_author(
                    name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url
                )
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Premium(client))
