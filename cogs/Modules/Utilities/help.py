import discord
from discord import app_commands
from discord.ext import commands

# TODO: do not do it


class Help(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="help", description="View the help menu for the bot.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=HelpLayout())


class Commands(discord.ui.Button):
    async def callback(self, interaction):
        pass


class Guides(discord.ui.Button):
    async def callback(self, interaction):
        pass


class HelpContainer(discord.ui.Container):
    Image = discord.ui.MediaGallery(
        discord.MediaGalleryItem(
            media="https://cdn.discordapp.com/banners/1113245569490616400/296c735fe503749f1473a688228b130f.webp?size=1024&width=1024&height=0"
        )
    )
    Title = discord.ui.TextDisplay("## <:Globe:1368890672563617882> Help")
    Sep = discord.ui.Separator()

    section = discord.ui.Section(
        accessory=Commands(label="Go", custom_id="e")
    ).add_item(discord.ui.TextDisplay("> **Commands**"))
    section2 = discord.ui.Section(accessory=Guides(label="Go", custom_id="z")).add_item(
        discord.ui.TextDisplay("> **Guides**")
    )


class HelpLayout(discord.ui.LayoutView):
    Container = HelpContainer(id=1, accent_color=discord.Color.blurple())


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Help(client))
