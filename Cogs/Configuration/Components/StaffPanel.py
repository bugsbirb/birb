import discord
import discord.http
import traceback

from utils.emojis import *

from dotenv import load_dotenv

load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# Configuration = DB["Config"]
# infractiontypeactions = DB["infractiontypeactions"]
# Customisation = DB["Customisation"]


class StaffPanelOptions(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Customise Embed",
                    emoji="<:Customisation:1223063306131210322>",
                )
            ]
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {
                "Staff Utils": {},
                "Module Options": {},
                "_id": interaction.guild.id,
            }
        Selected = self.values[0]
        if Selected == "Customise Embed":
            await interaction.response.defer()
            try:
                custom = await interaction.client.db['Customisation'].find_one(
                    {"guild_id": interaction.guild.id, "name": "Staff Panel"}
                )
                embed = None

                from Cogs.Configuration.Components.EmbedBuilder import (
                    DisplayEmbed,
                    Embed,
                )

                view = Embed(interaction.user, FinalFunction, "Staff Panel")

                if custom:
                    embed = await DisplayEmbed(custom, interaction.user)
                else:
                    embed = discord.Embed(description="Untitled")
                view.remove_item(view.Buttons)
                view.remove_item(view.ForumsChannel)
                view.remove_item(view.RemoveEmbed)
                view.remove_item(view.Ping)
                view.remove_item(view.Permissions)
                view.remove_item(view.reset)

                await interaction.edit_original_response(embed=embed, view=view)
            except Exception as e:
                traceback.print_exc(e)
        elif Selected == "Dropdown Label":
            await interaction.response.send_modal(DropDownLabel())

        else:
            await interaction.response.send_message(
                f"  **{interaction.user.display_name},** an error occurred. Please try again later.",
                ephemeral=True,
            )


async def FinalFunction(interaction: discord.Interaction, d=None):
    embed = interaction.message.embeds[0]
    if embed:
        thumbnail = embed.thumbnail.url if embed.thumbnail else None
        author = embed.author.icon_url if embed.author else None
        data = {
            "name": "Staff Panel",
            "embed": {
                "title": embed.title,
                "description": embed.description,
                "thumbnail": thumbnail,
                "image": embed.image.url if embed.image else None,
                "color": f"{embed.color.value:06x}" if embed.color else None,
                "author": {
                    "name": embed.author.name if embed.author else None,
                    "icon_url": author,
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
    else:
        data = {
            "message": interaction.message.content,
            "name": "Staff Panel",
        }

    await interaction.client.db['Customisation'].update_one(
        {"guild_id": interaction.guild.id, "name": "Staff Panel"},
        {"$set": data},
        upsert=True,
    )
    from Cogs.Configuration.Configuration import ConfigMenu, Options

    view = discord.ui.View()
    view.add_item(StaffPanelOptions(interaction.user))
    view.add_item(
        ConfigMenu(
            Options(
                await interaction.client.config.find_one({"_id": interaction.guild.id}),
            ),
            interaction.user,
        )
    )
    await interaction.response.edit_message(
        embed=await StaffPanelEmbed(
            interaction, discord.Embed(color=discord.Color.dark_embed())
        ),
        view=view,
    )


class DropDownLabel(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Dropdown Label")
        self.label = discord.ui.TextInput(
            label="Panel Label",
            required=True,
            max_length=45,
        )
        self.add_item(self.label)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            Config = {"_id": interaction.guild.id, "Staff Utils": {"Label": ""}}
        if not Config.get("Staff Utils"):
            Config["Staff Utils"] = {}
        Config["Staff Utils"]["Label"] = self.label.value
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": Config}, upsert=True
        )
        embed = discord.Embed(
            description=f"  **{interaction.user.display_name},** you have successfully updated the panel label to **{self.label.value}**!",
            color=discord.Colour.brand_green(),
        )
        return await interaction.followup.send(embed=embed, ephemeral=True)


async def StaffPanelEmbed(interaction: discord.Interaction, embed: discord.Embed):
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = (
        "> The Staff Panel provides an overview of all staff members, including their roles, "
        "joining dates, and introductions. Select a staff member to view detailed information. "
        "Learn more in [the documentation](https://docs.astrobirb.dev/)."
    )
    return embed
