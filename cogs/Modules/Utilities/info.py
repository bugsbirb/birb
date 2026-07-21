import discord
from discord.ext import commands

from core.bot.emojis import Emojis


class botinfo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(
        name="info", description="Statistics + Information about the bot."
    )
    async def info(self, ctx: commands.Context):
        await ctx.defer()
        embed = discord.Embed(
            color=discord.Color.dark_embed(),
            description="Birb is designed to simplify tasks related to managing staff, staff punishment, activity tracking.",
        )
        embed.add_field(
            name="Birb Information",
            value=(
                f"> **Version:** {await self.client.GetVersion()}\n"
                f"> **Servers:** {len(self.client.guilds)}\n"
                f"> **Shards:** {self.client.shard_count}\n"
            ),
        )
        embed.add_field(
            name="Links",
            value=(
                "> [**Support Server**](https://discord.gg/Qsz6DyGMTB)\n"
                "> [**Website**](https://www.astrobirb.dev)\n"
                "> [**Upvote**](https://top.gg/bot/1113245569490616400/vote)\n"
            ),
        )
        embed.set_author(
            name=self.client.user.display_name,
            icon_url=self.client.user.avatar.url,
            url="https://www.astrobirb.dev",
        )

        embed.set_thumbnail(url=self.client.user.avatar.url)

        view = Buttons(self.client)
        view.add_item(
            discord.ui.Button(
                label="Documentation",
                style=discord.ButtonStyle.link,
                emoji="📚",
                url="https://docs.astrobirb.dev",
            )
        )
        await ctx.send(embed=embed, view=view)


class Buttons(discord.ui.View):
    def __init__(self, client: commands.Bot):
        super().__init__()
        self.client = client

    @discord.ui.button(
        label="Attributions",
        style=discord.ButtonStyle.blurple,
        emoji=f"{Emojis.info}",
    )
    async def attributions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="**Attributions**",
            description=(
                "* [Solar Icon Sets](https://icon-sets.iconify.design/solar/)\n"
                "* [Tabler](https://tabler.io)\n"
                "* [Google Material Icons](https://fonts.google.com/icons?selected=Material+Icons)"
            ),
            color=discord.Color.dark_embed(),
        )
        embed.set_author(name="Birb", icon_url=self.client.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(botinfo(client))
