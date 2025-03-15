import discord
import discord.http

from utils.emojis import *

from dotenv import load_dotenv
from utils.permissions import premium
from Cogs.Modules.customcommands import SyncCommand, Unsync
from utils.HelpEmbeds import NoPremium, Support
load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# Commands = DB["Custom Commands"]


class CustomCommands(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Manage Commands", emoji="<:command1:1223062616872583289>"
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

        await interaction.response.defer()
        IsPremium = await premium(interaction.guild.id)
        if self.values[0] == "Manage Commands":
            embed = discord.Embed(color=discord.Colour.dark_embed())
            embed.set_author(
                name="Custom Commands",
                icon_url="https://cdn.discordapp.com/emojis/1223062616872583289.webp?size=96&quality=lossless",
            )
            embed.set_thumbnail(url=interaction.guild.icon)
            commands = await interaction.client.db['Custom Commands'].find({"guild_id": interaction.guild.id}).to_list(
                length=None
            )
            for commands in commands:
                Required = commands.get("permissionroles")
                if Required:
                    Roles = []
                    for role in Required:
                        Role = interaction.guild.get_role(role)
                        if not Role:
                            continue
                        Roles.append(Role)
                    Required = ", ".join([role.mention for role in Roles])
                else:
                    Required = "None"
                embed.add_field(
                    name=f"<:command1:1223062616872583289> {commands.get('name')}",
                    value=f">>> {replytop} **Required:** {Required}\n{replybottom} **Created:** <@{commands.get('creator')}> (`{commands.get('creator')}`)",
                    inline=False,
                )
                if 20 <= len(embed.fields):
                    break
            if len(embed.fields) == 0:
                embed.description == "> There are no custom commands!"
            
            embed.set_footer(text=f"{len(commands)}/{10 if not IsPremium else '∞'} Commands")
            view = ManageCommands(self.author)
            view.CreateCommand.label = f"Create ({len(commands)}/{10 if not IsPremium else '∞'})"
            await interaction.followup.send(view=view, embed=embed)
            del commands


class ManageCommands(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=360)
        self.author = author

    @discord.ui.button(label="Create", emoji="<:Add:1163095623600447558>")
    async def CreateCommand(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        CustomCommands = await interaction.client.db['Custom Commands'].count_documents({"guild_id": interaction.guild.id})
        IsPremium = await premium(interaction.guild.id)

        if CustomCommands > (10 if not IsPremium else float('inf')):
            return await interaction.response.send_message(embed=NoPremium, view=Support())

        await interaction.response.send_modal(CreateCommand(interaction.user))

    @discord.ui.button(label="Edit", emoji="<:Pen:1235001839036923996>")
    async def EditCommand(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        commands = await interaction.client.db['Custom Commands'].find({"guild_id": interaction.guild.id}).to_list(
            length=None
        )
        Options = []
        Added = set()
        for command in commands:
            name = command.get("name")
            if not name or name in Added:
                continue
            if any(option.label == command.get("name") for option in Options):
                continue
            Options.append(
                discord.SelectOption(
                    label=command.get("name"), value=command.get("name")
                )
            )
            Added.add(name)

            if 25 <= len(Options):
                break
        if len(Options) == 0:
            return await interaction.followup.send(
                content=f"  **{interaction.user.display_name},** there are no custom commands.",
                ephemeral=True,
            )
        view = discord.ui.View()
        view.add_item(CommandSelection(Options, "edit"))
        await interaction.edit_original_response(view=view, embed=None)
        del commands

    @discord.ui.button(label="Delete", emoji="<:Subtract:1229040262161109003>")
    async def DeleteCommand(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        commands = await interaction.client.db['Custom Commands'].find({"guild_id": interaction.guild.id}).to_list(
            length=None
        )
        Options = []
        Added = set()
        for command in commands:
            name = command.get("name")
            if not name or name in Added:
                continue

            Options.append(
                discord.SelectOption(
                    label=command.get("name"), value=command.get("name")
                )
            )
            Added.add(name)

            if len(Options) > 25:
                continue
        if len(Options) == 0:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** there are no custom commands.",
                ephemeral=True,
            )
        view = discord.ui.View()
        view.add_item(CommandSelection(Options, "delete"))
        await interaction.edit_original_response(view=view, embed=None)
        del commands


class CommandSelection(discord.ui.Select):
    def __init__(self, options: list, typed: str):
        super().__init__(options=options)
        self.typed = typed

    async def callback(self, interaction: discord.Interaction):
        if self.typed == "edit":
            from Cogs.Configuration.Components.EmbedBuilder import (
                NoEmbed,
                Embed,
                DisplayEmbed,
            )

            command = await interaction.client.db['Custom Commands'].find_one(
                {"name": self.values[0], "guild_id": interaction.guild.id}
            )
            data = {
                "name": command.get("name"),
                "content": command.get("content"),
                "creator": command.get("creator"),
                "permissionroles": command.get("permissionroles"),
                "components": command.get("components"),
                "embed": command.get("embed"),
            }
            if command.get("embed"):
                embed_data = command.get("embed")
                if any(
                    [
                        embed_data.get("title"),
                        embed_data.get("description"),
                        embed_data.get("thumbnail"),
                        embed_data.get("image"),
                        embed_data.get("color"),
                        embed_data.get("author"),
                        embed_data.get("fields"),
                    ]
                ):
                    view = Embed(interaction.user, FinalFunc, "Custom Commands", data)
                    embed = await DisplayEmbed(command, interaction.user)
                    view.remove_item(view.reset)
                    view.remove_item(view.ForumsChannel)
                    view.remove_item(view.Ping)
                    await interaction.response.edit_message(view=view, embed=embed)
                else:
                    view = NoEmbed(interaction.user, FinalFunc, "Custom Commands", data)
                    view.remove_item(view.reset)
                    await interaction.response.edit_message(
                        view=view,
                        content=(
                            command.get("content") if command.get("content") else None
                        ),
                    )
            else:
                view = NoEmbed(interaction.user, FinalFunc, "Custom Commands", data)
                view.remove_item(view.reset)
                await interaction.response.edit_message(
                    view=view,
                    content=command.get("content") if command.get("content") else None,
                )

        if self.typed == "delete":
            await interaction.client.db['Custom Commands'].delete_one(
                {"name": self.values[0], "guild_id": interaction.guild.id}
            )
            await Unsync(interaction.client, self.values[0], interaction.guild.id)
            await interaction.response.edit_message(
                content=f"  **{interaction.user.display_name},** I've deleted the command.",
                view=None,
                embed=None,
            )


class CreateCommand(discord.ui.Modal, title="Create Command"):
    def __init__(self, author: discord.member):
        super().__init__()
        self.name = discord.ui.TextInput(
            label="Command Name", max_length=100, required=True
        )
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        command = await interaction.client.db['Custom Commands'].find_one(
            {"guild_id": interaction.guild.id, "name": self.name.value}
        )
        if command:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** theres already a command named that.",
                ephemeral=True,
            )
        from Cogs.Configuration.Components.EmbedBuilder import NoEmbed

        view = NoEmbed(
            interaction.user,
            FinalFunc,
            "Custom Commands",
            {"name": self.name.value},
        )
        view.remove_item(view.reset)

        await interaction.response.edit_message(view=view, embed=None, content=None)


async def FinalFunc(interaction: discord.Interaction, datad: dict):
    embed = interaction.message.embeds[0] if interaction.message.embeds else None

    if embed:
        thumbnail = embed.thumbnail.url if embed.thumbnail else None
        author = embed.author.icon_url if embed.author else None
        color = f"{embed.color.value:06x}" if embed.color else None

        data = {
            "name": datad.get("name"),
            "content": interaction.message.content,
            "creator": interaction.user.id,
            "embed": {
                "title": embed.title,
                "description": embed.description,
                "thumbnail": thumbnail,
                "image": embed.image.url if embed.image else None,
                "color": color,
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
            "components": datad.get("components"),
        }
        if datad.get("permissionroles"):
            data["permissionroles"] = datad.get("permissionroles")
    else:
        data = {
            "name": datad.get("name"),
            "content": interaction.message.content,
            "name": datad.get("name"),
            "components": datad.get("components"),
        }
        if datad.get("permissionroles"):
            data["permissionroles"] = datad.get("permissionroles")

    result = await interaction.client.db['Custom Commands'].update_one(
        {"name": datad.get("name"), "guild_id": interaction.guild.id},
        {"$set": data},
        upsert=True,
    )
    print(f"Modified count: {result.modified_count}, Upserted ID: {result.upserted_id}")

    await SyncCommand(interaction.client, datad.get("name"), interaction.guild.id)

    await interaction.response.edit_message(
        content=f"  **{interaction.user.display_name},** success.",
        view=None,
        embed=None,
    )


async def CustomCommandsEmbed(interaction: discord.Interaction, embed: discord.Embed):
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> Custom Commands are a way to create your own commands that can be used by people in the server. You can find out more at [the documentation](https://docs.astrobirb.dev/)."
    return embed
