import discord
import discord.http
from utils.emojis import *

from dotenv import load_dotenv
import traceback

load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# Configuration = DB["Config"]
# Customisation = DB["Customisation"]


class Suggestions(discord.ui.Select):
    def __init__(self, author: discord.User):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Suggestions Channel",
                    emoji="<:tag:1234998802948034721>",
                ),
                discord.SelectOption(
                    label="Customise Embeds",
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
        option = interaction.data["values"][0]
        if option == "Suggestions Channel":
            Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
            if not Config:
                Config = {"Suggestions": {}, "_id": interaction.guild.id}
            view = discord.ui.View()
            view.add_item(
                SuggestionsChannel(
                    self.author,
                    interaction.guild.get_channel(
                        Config.get("Suggestions", {}).get("channel")
                    ),
                    interaction.message,
                )
            )
            await interaction.response.send_message(view=view, ephemeral=True)
        if option == "Customise Embeds":
            view = discord.ui.View()
            view.add_item(EmbedSelection(self.author))
            await interaction.response.edit_message(
                embed=None,
                view=view,
                content="<:List:1223063187063308328> Select which embed you want to edit.",
            )


class SuggestionsChannel(discord.ui.ChannelSelect):
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

        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if config is None:
            config = {"_id": interaction.guild.id, "Suggestions": {}}
        elif "Suggestions" not in config:
            config["Suggestions"] = {}

        config["Suggestions"]["channel"] = self.values[0].id if self.values else None
        await interaction.client.config.update_one({"_id": interaction.guild.id}, {"$set": config})
        Updated = await interaction.client.config.find_one({"_id": interaction.guild.id})

        await interaction.response.edit_message(content=None)
        try:
            await self.message.edit(
                embed=await SuggestionsEmbed(
                    interaction,
                    Updated,
                    discord.Embed(color=discord.Color.dark_embed()),
                ),
            )
        except:
            pass


async def CustomiseEmbed(interaction: discord.Interaction, option):
    try:
        await interaction.response.defer()
        custom = await interaction.client.db['Customisation'].find_one(
            {"guild_id": interaction.guild.id, "type": option}
        )
        embed = None

        from Cogs.Configuration.Components.EmbedBuilder import (
            DisplayEmbed,
            Embed,
        )

        if not custom:
            view = Embed(
                interaction.user,
                FinalFunction,
                option,
                {
                    "thumb": "{staff.avatar}",
                    "author_url": "{author.avatar}",
                    "option": option,
                    "image": "{image}",
                },
            )
            embed = discord.Embed(
                title="",
                description="<:Member:1226674150463111299> {author.mention}",
                color=discord.Color.yellow(),
            )
            embed.set_thumbnail(url=interaction.user.display_avatar)
            embed.set_image(
                url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png"
            )

            embed.add_field(
                name="<:pin:1226671966413389864> Suggestion", value="{suggestion}"
            )
            embed.set_author(
                icon_url=interaction.user.display_avatar, name="{author.name}"
            )
            embed.add_field(
                name="<:messageforward1:1230919023361921165> Opinions",
                value="{upvotes} <:UpVote:1223062893096996934> | {downvote} <:DownVote:1223063241433939989>",
            )
            if option == "Accepted Suggestion":
                embed.title = f"  Suggestion Accepted"
                embed.color = discord.Color.brand_green()

            if option == "Denied Suggestion":
                embed.title = f"  Suggestion Denied"
                embed.color = discord.Color.brand_red()
                embed.add_field(name="Denied Reason", value="{reason}", inline=False)

            view.remove_item(view.Buttons)
            view.remove_item(view.RemoveEmbed)
            view.remove_item(view.Content)
            view.remove_item(view.Permissions)
            view.remove_item(view.ForumsChannel)
            view.remove_item(view.Ping)
            return await interaction.edit_original_response(
                embed=embed, view=view, content=None
            )
        view = Embed(
            interaction.user,
            FinalFunction,
            option,
            {
            "thumb": (
                interaction.user.display_avatar.url
                if custom.get("embed", {}).get("thumbnail") == "{author.avatar}"
                else (
                    "{staff.avatar}"
                    if custom.get("embed", {}).get("thumbnail") == "{staff.avatar}"
                    else custom.get("embed", {}).get("thumbnail", "") 
                )
            ),

            "author_url": (
                interaction.user.display_avatar.url
                if custom.get("embed", {}).get("author", {}).get("icon_url") == "{author.avatar}"
                else (
                    "{staff.avatar}"
                    if custom.get("embed", {}).get("author", {}).get("icon_url") == "{staff.avatar}"
                    else custom.get("embed", {}).get("author", {}).get("icon_url", "") 
                )
                            ),
                "image": custom.get('image'),
                "option": option,
            },
        )
        embed = await DisplayEmbed(custom, interaction.user)
        view.remove_item(view.Buttons)
        view.remove_item(view.RemoveEmbed)
        view.remove_item(view.Content)
        view.remove_item(view.Permissions)
        view.remove_item(view.ForumsChannel)
        view.remove_item(view.Ping)

        return await interaction.edit_original_response(
            embed=embed, view=view, content=None
        )
    except Exception as e:
        traceback.print_exc(e)


async def FinalFunction(interaction: discord.Interaction, d={}):
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
    await interaction.client.db['Customisation'].update_one(
        {"guild_id": interaction.guild.id, "type": d.get("option")},
        {"$set": data},
        upsert=True,
    )
    Config = await interaction.client.config.find_one({"_id": interaction.guild.id})

    view = discord.ui.View()
    view.add_item(Suggestions(interaction.user))
    view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
    await interaction.response.edit_message(
        embed=await SuggestionsEmbed(
            interaction, Config, discord.Embed(color=discord.Color.dark_embed())
        ),
        content="",
        view=view,
    )


class EmbedSelection(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(label="Normal", value="Suggestion"),
                discord.SelectOption(label="Accepted", value="Accepted Suggestion"),
                discord.SelectOption(label="Denied", value="Denied Suggestion"),
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

        option = self.values[0]
        await CustomiseEmbed(interaction, option)


async def SuggestionsEmbed(
    interaction: discord.Interaction, config: dict, embed: discord.Embed
):
    if not config:
        config = {"Suggestions": {}}
    Channel = (
        interaction.guild.get_channel(config.get("Suggestions", {}).get("channel"))
        or "Not Configured"
    )

    if isinstance(Channel, discord.TextChannel):
        Channel = Channel.mention

    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> This is where you can manage your server's suggestions settings! Suggestions is a way for members to give suggestions to the server. You can find out more at [the documentation](https://docs.astrobirb.dev/)."
    embed.add_field(
        name="<:settings:1207368347931516928> Suggestions",
        value=f"> `Suggestions Channel:` {Channel}\n\nIf you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
        inline=False,
    )
    return embed
