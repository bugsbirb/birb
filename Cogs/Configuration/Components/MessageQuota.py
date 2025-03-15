import discord
import discord.http

from utils.emojis import *

from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# autoactivity = DB["auto activity"]

# Configuration = DB["Config"]


class QuotaOptions(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Quota Amount", emoji="<:uilsortamountup:1248315081154887761>"
                ),
                discord.SelectOption(
                    label="Ignored Channels", emoji="<:tag:1234998802948034721>"
                ),
                discord.SelectOption(
                    label="Auto Activity", emoji="<:suspensions:1234998406938755122>"
                ),
            ]
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(
                embed=discord.Embed(
                    description=f"  **{interaction.user.display_name},** this is not your panel!",
                    color=discord.Colour.brand_red(),
                ),
                ephemeral=True,
            )

        selection = self.values[0]
        view = discord.ui.View()
        if selection == "Quota Amount":
            await interaction.response.send_modal(
                MessageQuota(
                    author=interaction.user, default=None, message=interaction.message
                )
            )
            return
        if selection == "Ignored Channels":
            Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
            if not Config:
                Config = {"Message Quota": {}, "_id": interaction.guild.id}
            view.add_item(
                IgnoredChannels(
                    author=interaction.user,
                    default=[
                        interaction.guild.get_channel(int(channel_id))
                        for channel_id in Config.get("Message Quota", {}).get(
                            "Ignored Channels", []
                        )
                    ],
                    message=interaction.message,
                ),
            )
            await interaction.response.send_message(view=view, ephemeral=True)
        if selection == "Auto Activity":
            view.add_item(AutoActivity(interaction.user))
            await interaction.response.send_message(view=view, ephemeral=True)


class IgnoredChannels(discord.ui.ChannelSelect):
    def __init__(self, author: discord.Member, default: list = None, message=None):
        super().__init__(
            max_values=10,
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.default = default
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.followup.send(
                embed=discord.Embed(
                    description=f"  **{interaction.user.display_name},** this is not your panel!",
                    color=discord.Colour.brand_red(),
                ),
                ephemeral=True,
            )

        Config = await interaction.client.config.find_one({"_id": interaction.guild.id}) or {
            "Message Quota": {"Ignored Channels": []},
            "_id": interaction.guild.id,
        }
        if not Config.get("Message Quota"):
            Config = {
                "Message Quota": {"Ignored Channels": []},
            }

        if "Ignored Channels" not in Config.get("Message Quota"):
            Config["Message Quota"]["Ignored Channels"] = []

        Config["Message Quota"]["Ignored Channels"] = [
            ch_id
            for ch_id in Config["Message Quota"]["Ignored Channels"]
            if ch_id in [channel.id for channel in self.values]
        ] + [
            channel.id
            for channel in self.values
            if channel.id not in Config["Message Quota"]["Ignored Channels"]
        ]

        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": Config}, upsert=True
        )
        Updated = await interaction.client.config.find_one({"_id": interaction.guild.id})
        view = discord.ui.View()
        view.add_item(QuotaOptions(interaction.user))
        await interaction.response.edit_message(view=view)
        try:
            await self.message.edit(
                embed=await MessageQuotaEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                )
            )
        except:
            pass


class MessageQuota(discord.ui.Modal, title="Message Quota"):
    def __init__(self, author: discord.Member, default: str = None, message=None):
        super().__init__()
        self.Quota = discord.ui.TextInput(
            label="Quota Amount",
            placeholder="Enter the amount of messages required to be active",
            style=discord.TextStyle.short,
            default=default,
        )
        self.add_item(self.Quota)
        self.author = author
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
            if not Config:
                Config = {"Message Quota": {}, "_id": interaction.guild.id}
            if not Config.get('Message Quota'):
                Config['Message Quota'] = {}
            Config["Message Quota"]["quota"] = int(self.Quota.value)
            await interaction.client.config.update_one(
                {"_id": interaction.guild.id}, {"$set": Config}, upsert=True
            )
            Updated = await interaction.client.config.find_one({"_id": interaction.guild.id})
            await interaction.response.edit_message(content="")
            try:
                await self.message.edit(
                    embed=await MessageQuotaEmbed(
                        interaction,
                        Updated,
                        discord.Embed(color=discord.Color.dark_embed()),
                    ),
                )
            except:
                pass
        except ValueError:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** please enter a valid number.",
                color=discord.Colour.brand_red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class AutoActivity(discord.ui.Select):
    def __init__(self, author):
        self.author = author

        options = [
            discord.SelectOption(label="Toggle", emoji="<:Button:1223063359184830494>"),
            discord.SelectOption(label="Channel", emoji="<:tag:1234998802948034721>"),
            discord.SelectOption(
                label="Post Date", emoji="<:time:1158064756104630294>"
            ),
        ]
        super().__init__(
            placeholder="Auto Activity", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        view = discord.ui.View()
        if selection == "Toggle":

            view.add_item(ActivityToggle(interaction.user))
            await interaction.response.send_message(view=view, ephemeral=True)
        if selection == "Channel":
            view.add_item(PostChannel(interaction.user))
            await interaction.response.send_message(view=view, ephemeral=True)
        if selection == "Post Date":
            await interaction.response.send_modal(PostDate())


class PostDate(discord.ui.Modal, title="How often?"):

    postdate = discord.ui.TextInput(
        label="Post Day",
        placeholder="What day do you want it to post every week? (Monday, Tuesday etc)",
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        days = [
            "sunday",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "tuesday",
        ]
        specified_day = self.postdate.value.lower()

        if specified_day not in days:
            await interaction.response.send_message(
                "Invalid day specified. Please enter a valid day of the week.",
                ephemeral=True,
            )
            return
        CurrentDay = datetime.utcnow().weekday()
        Specified = days.index(specified_day)

        Days = (Specified - CurrentDay) % 7

        if Days <= 0:
            Days += 7
        NextDate = datetime.utcnow() + timedelta(days=Days - 1)
        await interaction.client.db['auto activity'].update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"day": self.postdate.value, "nextdate": NextDate}},
            upsert=True,
        )
        embed = discord.Embed(
            title="Success!",
            color=discord.Color.brand_green(),
            description=f"**Next Post Date:** <t:{int(NextDate.timestamp())}>",
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class PostChannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(
            placeholder="Post Channel",
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer(ephemeral=True)

        filter = {"guild_id": interaction.guild.id}
        try:
            await interaction.client.db['auto activity'].update_one(
                filter, {"$set": {"channel_id": self.values[0].id if self.values else None}}, upsert=True
            )
            await interaction.edit_original_response(content=None)
        except Exception as e:
            return


class ActivityToggle(discord.ui.Select):
    def __init__(self, author):
        self.author = author

        options = [
            discord.SelectOption(label="Enabled"),
            discord.SelectOption(label="Disabled"),
        ]
        super().__init__(
            placeholder="Activity Toggle", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if color == "Enabled":
            await interaction.response.send_message(
                content=f"ed", ephemeral=True
            )
            await interaction.client.db['auto activity'].update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"enabled": True}},
                upsert=True,
            )

        if color == "Disabled":
            await interaction.response.send_message(
                content=f"  Disabled", ephemeral=True
            )
            await interaction.client.db['auto activity'].update_one(
                {"guild_id": interaction.guild.id},
                {"$set": {"enabled": False}},
                upsert=True,
            )


async def MessageQuotaEmbed(
    interaction: discord.Interaction, Config: dict, embed: discord.Embed
):
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
    if not Config:
        Config = {"Message Quota": {}}
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    IgnoredChannels = (
        ", ".join(
            f"<#{int(Channel)}>"
            for Channel in Config.get("Message Quota", {}).get("Ignored Channels") or []
        )
        or "Not Configured"
    )
    embed.description = "> This is where you can manage your server's message quota! If you wanna know more about what this does head to the [advanced permissions page](https://docs.astrobirb.dev/advanced-permissions) on the [documentation](https:/docs.astrobirb.dev)\n"
    embed.add_field(
        name="<:settings:1207368347931516928> Message Quota",
        value=f"{replytop} `Quota:` {Config.get('Message Quota', {}).get('quota', 'Not Configured')}\n{replybottom} `Ignored Channels:` {IgnoredChannels}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
        inline=False,
    )
    return embed
