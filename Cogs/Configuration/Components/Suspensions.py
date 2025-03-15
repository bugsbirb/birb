import discord
import discord.http
import traceback

from utils.emojis import *

from dotenv import load_dotenv

load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# Configuration = DB["Config"]
# Customisation = DB["Customisation"]


class SuspensionOptions(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Suspension Channel", emoji="<:tag:1234998802948034721>"
                ),
                discord.SelectOption(
                    label="Customise Embed",
                    emoji="<:Customisation:1223063306131210322>",
                ),
            ]
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {"Suspension": {}, "_id": interaction.guild.id}
        if self.values[0] == "Suspension Channel":
            view = discord.ui.View()
            view.add_item(
                SuspensionChannel(
                    self.author,
                    interaction.guild.get_channel(
                        Config.get("Suspension", {}).get("channel")
                    ),
                    interaction.message,
                )
            )
        elif self.values[0] == "Customise Embed":
            try:
                custom = await interaction.client.db["Customisation"].find_one(
                    {"guild_id": interaction.guild.id, "type": "Suspension"}
                )
                embed = None

                from Cogs.Configuration.Components.EmbedBuilder import (
                    DisplayEmbed,
                    NoEmbed,
                    Embed,
                )

                view = Embed(
                    interaction.user,
                    FinalFunction2,
                    "Suspension",
                    {"thumb": "{staff.avatar}", "author_url": "{author.avatar}"},
                )
                if not custom:
                    embed = discord.Embed(color=discord.Color.dark_embed())
                    embed.title = "Staff Consequences & Discipline"
                    embed.description = "- **Staff Member:** {staff.mention}\n- **Action:** Suspension\n- **Reason:** {reason}\n- **Duration:** {start_time} - {end_time}"
                    embed.set_author(
                        name="Signed, {author.name}",
                        icon_url=interaction.user.display_avatar,
                    )
                    embed.color = discord.Color.dark_embed()
                    embed.set_thumbnail(url=interaction.user.display_avatar)
                    view.remove_item(view.Buttons)
                    view.remove_item(view.RemoveEmbed)
                    view.remove_item(view.Content)
                    view.remove_item(view.Permissions)
                    view.remove_item(view.ForumsChannel)
                    view.remove_item(view.Ping)
                    return await interaction.response.edit_message(
                        embed=embed, view=view
                    )

                if custom.get("embed") is not None or not custom.get("embed") == {}:
                    embed = await DisplayEmbed(custom, interaction.user)
                    message = custom.get("message")
                else:
                    view = NoEmbed(interaction.user, FinalFunction2, "Suspension")
                view.remove_item(view.Buttons)
                view.remove_item(view.RemoveEmbed)
                view.remove_item(view.Content)
                view.remove_item(view.Permissions)
                view.remove_item(view.ForumsChannel)
                view.remove_item(view.Ping)
                view = Embed(
                    interaction.user,
                    FinalFunction2,
                    "Suspension",
                    {
                        "thumb": (
                            (
                                interaction.user.display_avatar.url
                                if interaction.user.display_avatar
                                else (
                                    None
                                    if custom.get("embed", {}).get("thumbnail")
                                    in ["{author.avatar}", "{staff.avatar}"]
                                    else custom.get("embed", {}).get("thumbnail")
                                )
                            )
                            if custom.get("embed", {}).get("thumbnail")
                            else None
                        ),
                        "author_url": (
                            (
                                interaction.user.display_avatar.url
                                if interaction.user.display_avatar
                                else (
                                    None
                                    if custom.get("embed", {})
                                    .get("author", {})
                                    .get("icon_url")
                                    in ["{author.avatar}", "{staff.avatar}"]
                                    else custom.get("embed", {})
                                    .get("author", {})
                                    .get("icon_url")
                                )
                            )
                            if custom.get("embed", {}).get("author", {}).get("icon_url")
                            else None
                        ),
                        "image": (
                            (
                                interaction.user.display_avatar.url
                                if interaction.user.display_avatar
                                else (
                                    None
                                    if custom.get("embed", {}).get("image")
                                    in ["{author.avatar}", "{staff.avatar}"]
                                    else custom.get("embed", {}).get("image")
                                )
                            )
                            if custom.get("embed", {}).get("image")
                            else None
                        ),
                    },
                )
                return await interaction.response.edit_message(
                    content=message if message else None, embed=embed, view=view
                )
            except Exception as e:
                traceback.print_exc(e)

        await interaction.response.send_message(view=view, ephemeral=True)


async def FinalFunction2(interaction: discord.Interaction, d=None):
    from Cogs.Configuration.Configuration import ConfigMenu, Options

    embed = interaction.message.embeds[0]
    if embed:
        data = {
            "content": interaction.message.content,
            "creator": interaction.user.id,
            "embed": {
                "title": embed.title,
                "description": embed.description,
                "thumbnail": d.get("thumb"),
                "image": d.get("image"),
                "color": f"{embed.color.value:06x}" if embed.color else None,
                "author": {
                    "name": embed.author.name if embed.author else None,
                    "icon_url": d.get("author_url"),
                },
                "fields": [
                    {
                        "name": field.name,
                        "value": field.value,
                        "inline": field.inline,
                    }
                    for field in embed.fields
                ],
            },
        }

    await interaction.client.db["Customisation"].update_one(
        {"guild_id": interaction.guild.id, "type": "Suspension"},
        {"$set": data},
        upsert=True,
    )
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})

    view = discord.ui.View()
    view.add_item(SuspensionOptions(interaction.user))
    view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
    await interaction.response.edit_message(
        embed=await SuspensionEmbed(
            interaction, Config, discord.Embed(color=discord.Color.dark_embed())
        ),
        view=view,
    )


class SuspensionChannel(discord.ui.ChannelSelect):
    def __init__(
        self,
        author: discord.Member,
        channel: discord.TextChannel = None,
        message: discord.Message = None,
    ):
        super().__init__(
            min_values=0,
            max_values=1,
            default_values=[channel] if channel else [],
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        self.author = author
        self.channel = channel
        self.message = message

    async def callback(self, interaction):
        from Cogs.Configuration.Configuration import ConfigMenu, Options

        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Suspension": {}}
        elif "Suspension" not in config:
            config["Suspension"] = {}

        config["Suspension"]["channel"] = self.values[0].id if self.values else None
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}
        )
        Updated = await interaction.client.config.find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await SuspensionEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


async def SuspensionEmbed(
    interaction: discord.Interaction, Config: dict, embed: discord.Embed
):
    if not Config:
        Config = {"Suspension": {}, "_id": interaction.guild.id}

    Channel = (
        interaction.guild.get_channel(Config.get("Suspension", {}).get("channel"))
        or "Not Configured"
    )
    if isinstance(Channel, discord.TextChannel):
        Channel = Channel.mention

    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's suspensions settings! Suspension are a way to punish staff members for a period of time. You can find out more at [the documentation](https://docs.astrobirb.dev/)."
    embed.add_field(
        name="<:settings:1207368347931516928> Suspension",
        value=f"> `Suspension Channel:` {Channel}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
        inline=False,
    )
    return embed
