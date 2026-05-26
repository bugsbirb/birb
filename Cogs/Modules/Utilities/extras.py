import discord
from discord.ext import commands
from discord import app_commands

from datetime import datetime


import aiohttp
from utils.emojis import *


class Utility(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        client.launch_time = datetime.now()
        self.client.help_command = None

    @app_commands.command(name="birb", description="Get silly birb photo")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def birb(self, interaction: discord.Interaction):
        try:
            async with aiohttp.ClientSession() as session, session.get(
                "https://api.alexflipnote.dev/birb"
            ) as response:
                response.raise_for_status()
                data = await response.json()

            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_image(url=data.get("file"))
            await interaction.response.send_message(embed=embed)

        except aiohttp.ClientError as e:
            await interaction.response.send_message(
                f"{crisis} {interaction.user.mention}, I couldn't get a birb image for you :c\n**Error:** `{e}`",
            )

    @app_commands.command(description="Get support from the support server")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def support(self, interaction: discord.Interaction):
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Join",
                url="https://discord.gg/DhWdgfh3hN",
                style=discord.ButtonStyle.blurple,
                emoji="<:link:1206670134064717904>",
            )
        )
        view.add_item(
            discord.ui.Button(
                label="Documentation",
                url="https://docs.astrobirb.dev",
                style=discord.ButtonStyle.blurple,
                emoji="📚",
            )
        )

        bot_user = self.client.user
        embed = discord.Embed(
            description="Encountering issues with Birb? Our support team is here to help! Join our official support server using the link below.",
            color=0x2B2D31,
        )
        embed.set_author(name=bot_user.display_name, icon_url=bot_user.display_avatar)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(description="Invite Birb to your server")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def invite(self, interaction: discord.Interaction):
        view = discord.ui.View().add_item(
            discord.ui.Button(
                label="Invite",
                url="https://discord.com/api/oauth2/authorize?client_id=1113245569490616400&permissions=1632557853697&scope=bot%20applications.commands",
                style=discord.ButtonStyle.blurple,
                emoji="<:link:1206670134064717904>",
            )
        )
        await interaction.response.send_message(view=view)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Utility(client))
