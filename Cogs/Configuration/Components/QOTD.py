import discord
import discord.http
from utils.emojis import *

from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# Customisation = DB["Customisation"]
# qotd = DB["QOTD Configuration"]
# qotds = DB["qotd"]
# Configuration = DB["Config"]


class QOTDOptions(discord.ui.Select):
    def __init__(self, author: discord.Member, options: list):

        super().__init__(options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.response.defer()
        option = interaction.data["values"][0]
        from Cogs.Configuration.Configuration import ConfigMenu, Options
        if option == "Start QOTD":
            await interaction.client.db['qotd'].update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"nextdate": datetime.now() + timedelta(days=1)}},
                upsert=True,
            )
            nextdate = datetime.now() + timedelta(days=1)
            timestamp = f"<t:{int(nextdate.timestamp())}>"
            embed = discord.Embed(
                title=f"  Enabled",
                description=f"> **Next Post Date:** {timestamp}",
                color=discord.Color.brand_green(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            options = [
                discord.SelectOption(
                    label="Stop QOTD",
                    emoji="<:stop:1330484991414501418>",
                    description="End the daily questions.",
                ),
                discord.SelectOption(
                    label="Channel", emoji="<:tag:1234998802948034721>"
                ),
                discord.SelectOption(label="Ping", emoji="<:Ping:1298301862906298378>"),
                discord.SelectOption(
                    label="Preferences", emoji="<:leaf:1160541147320553562>"
                ),
            ]
            view = discord.ui.View()
            view.add_item(QOTDOptions(self.author, options))
            view.add_item(
                ConfigMenu(
                    Options(
                        await interaction.client.config.find_one({"_id": interaction.guild.id})
                    ),
                    interaction.user,
                )
            )
            await interaction.edit_original_response(
                embed=await QOTDEMbed(
                    interaction, discord.Embed(color=discord.Color.dark_embed())
                ),
                view=view,
            )
        elif option == "Stop QOTD":


            await interaction.client.db['qotd'].update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"nextdate": None}},
                upsert=True,
            )
            embed = discord.Embed(
                title=f"  Disabled",
                description="> **QOTD has been disabled.**",
                color=discord.Color.brand_red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            options = [
                discord.SelectOption(
                    label="Start QOTD",
                    emoji="<:start:1299717567660687371>",
                    description="Start the daily questions. (Pressing this while its already started will restart it.)",
                ),
                discord.SelectOption(
                    label="Channel", emoji="<:tag:1234998802948034721>"
                ),
                discord.SelectOption(label="Ping", emoji="<:Ping:1298301862906298378>"),
                discord.SelectOption(
                    label="Preferences", emoji="<:leaf:1160541147320553562>"
                ),
            ]

            view = discord.ui.View()
            view.add_item(QOTDOptions(self.author, options))
            view.add_item(
                ConfigMenu(
                    Options(
                        await interaction.client.config.find_one({"_id": interaction.guild.id})
                    ),
                    interaction.user,
                )
            )

            await interaction.edit_original_response(
                embed=await QOTDEMbed(
                    interaction, discord.Embed(color=discord.Color.dark_embed())
                ),
                view=view,
            )

        elif option == "Channel":

            Config = await interaction.client.db['qotd'].find_one({"_id": interaction.guild.id})
            if not Config:
                Config = {"_id": interaction.guild.id, "channel": None}
            view = discord.ui.View()
            view.add_item(
                QOTDChannel(
                    self.author,
                    (
                        [interaction.guild.get_channel(Config.get("channel"))]
                        if Config.get("channel")
                        else []
                    ),
                    interaction.message,
                )
            )
            await interaction.followup.send(view=view, ephemeral=True)
        elif option == "Preferences":
            Config = await interaction.client.db['qotd'].find_one({"guild_id": interaction.guild.id})
            if not Config:
                Config = {"guild_id": interaction.guild.id, "qotdthread": True}
            view = Preferences(self.author)
            if Config.get("qotdthread"):
                view.IssuerButton.label = "Threads (Enabled)"
                view.IssuerButton.style = discord.ButtonStyle.green
            else:
                view.IssuerButton.label = "Threads (Disabled)"
                view.IssuerButton.style = discord.ButtonStyle.red

            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.description = "> - **Threads:** If enabled, the bot will create a thread for each QOTD post. This is useful for keeping the discussion organized."

            embed.set_author(
                name="Preferences",
                icon_url="https://cdn.discordapp.com/emojis/1160541147320553562.webp?size=96&quality=lossless",
            )
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        elif option == "Ping":
            view = discord.ui.View()
            view.add_item(PingRole(interaction.user, interaction.message))
            await interaction.followup.send(view=view, ephemeral=True)


class PingRole(discord.ui.RoleSelect):
    def __init__(
        self,
        author: discord.Member,
        message: discord.Message = None,
    ):
        super().__init__(
            min_values=0,
            max_values=1,
        )
        self.author = author
        self.message = message

    async def callback(self, interaction):
        from Cogs.Configuration.Configuration import ConfigMenu, Options

        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        await interaction.client.db['qotd'].update_one(
            {"guild_id": interaction.guild.id},
            {
                "$set": {
                    "pingrole": self.values[0].id if self.values else None if self.values else None,
                    "guild_id": interaction.guild_id,
                }
            },
            upsert=True,
        )
        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await QOTDEMbed(
                    interaction, discord.Embed(color=discord.Color.dark_embed())
                ),
            )
        except:
            pass


class QOTDChannel(discord.ui.ChannelSelect):
    def __init__(self, author, channels, msg):
        super().__init__(
            placeholder="Channel",
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
            default_values=channels,
        )
        self.author = author
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.client.db['qotd'].update_one(
            {"guild_id": interaction.guild.id},
            {
                "$set": {
                    "channel_id": self.values[0].id if self.values else None,
                    "guild_id": interaction.guild_id,
                }
            },
            upsert=True,
        )
        await self.msg.edit(
            embed=await QOTDEMbed(
                interaction, discord.Embed(color=discord.Color.dark_embed())
            )
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** channel has been updated.",
            view=None,
            embed=None,
        )


class Preferences(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    async def ToggleOption(
        self, interaction: discord.Interaction, button: discord.ui.Button, Option: str
    ):
        QOTD = await interaction.client.db['qotd'].find_one({"guild_id": interaction.guild.id})
        if not QOTD:
            QOTD = {"guild_id": interaction.guild.id, "qotdthread": True}

        if Option == "qotdthread":
            if QOTD.get("qotdthread", True):
                QOTD["qotdthread"] = False
                self.IssuerButton.label = "Threads (Disabled)"
                self.IssuerButton.style = discord.ButtonStyle.red
            else:
                QOTD["qotdthread"] = True
                self.IssuerButton.label = "Threads (Enabled)"
                self.IssuerButton.style = discord.ButtonStyle.green

        await interaction.client.db['qotd'].update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"qotdthread": QOTD["qotdthread"]}},
            upsert=True,
        )
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Threads (Enabled)", style=discord.ButtonStyle.green)
    async def IssuerButton(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.ToggleOption(interaction, button, "qotdthread")


async def QOTDEMbed(interaction: discord.Interaction, embed: discord.Embed):
    config = await interaction.client.db['qotd'].find_one({"guild_id": interaction.guild.id})
    channel = (
        interaction.guild.get_channel(config.get("channel_id") if config else 0)
        or "Not Configured"
    )
    NextDate = config.get("nextdate") if config else None
    if NextDate:
        NextDate = f"<t:{int(NextDate.timestamp())}>" or "Not Active"
    else:
        NextDate = "Not Active"

    if isinstance(channel, discord.TextChannel):
        channel = channel.mention
    ping = (
        f'<@&{config.get("pingrole")}>'
        if config and config.get("pingrole")
        else "Not Configured"
    )

    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's QOTD settings! QOTD is a way for members to answer a question of the day. You can find out more at [the documentation](https://docs.astrobirb.dev/)."
    embed.add_field(
        name="<:settings:1207368347931516928> Daily Questions",
        value=f"{replytop} `Channel:` {channel}\n{replymiddle} `Ping`: {ping}\n{replybottom} `Next Date:` {NextDate} (Not 100% accurate)\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
        inline=False,
    )
    return embed
