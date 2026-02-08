import discord
from discord.ext import commands
from utils.format import IsSeperateBot
from discord import app_commands


class Membership(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(description="Learn about Birb's premium tiers and features.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(private_channels=True, dms=True, guilds=True)
    async def membership(self, interaction: discord.Interaction):
        embed = discord.Embed(color=discord.Color.dark_embed())
        embed.add_field(
            name="🕹️ Premium - $2.50",
            value="> **Whitelabel Lite** - Allow you to send infraction, promotion, qotd messages as webhooks.\n> **Infraction Hierarchies**\n> **Unlimited Modmail Categories**\n> **More Custom Commands** - (10 -> ∞)\n> **Auto Response** - Automatically responds to keywords, uses similarity detection aswell.\n> **Infraction Reason Presets** - Add reasons which you can pick from while creating an infraction.\n>  **Forums Controls** - Adds controls to manage the thread with buttons.\n> **Mass Infractions** - You are able to select a bunch of people and infract them for the same reason + type.",
            inline=False,
        )
        embed.add_field(
            name="🤖 Whitelabel - $5.00",
            value="> Fully branded bot with your name, avatar. Hosted by us.",
            inline=False,
        )
        embed.set_author(
            name=self.client.user.display_name, icon_url=self.client.user.display_avatar
        )
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Premium",
                emoji="🕹️",
                style=discord.ButtonStyle.link,
                url="https://www.patreon.com/checkout/AstroBirb?rid=22855340&vanity=11440929",
            )
        )
        view.add_item(
            discord.ui.Button(
                label="Whitelabel",
                emoji="🤖",
                style=discord.ButtonStyle.link,
                url="https://www.patreon.com/checkout/AstroBirb?rid=22733636&vanity=11440929",
            )
        )
        await interaction.response.send_message(embed=embed, view=view)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Membership(client))
