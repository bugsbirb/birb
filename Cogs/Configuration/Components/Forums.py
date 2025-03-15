import discord
import discord.http
from utils.emojis import *
from utils.format import IsSeperateBot

from dotenv import load_dotenv

load_dotenv()


class ForumsOptions(discord.ui.Select):
    def __init__(self, author: discord.User):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Manage Forums", emoji="<:category:1248312604733210735>"
                ),
            ],
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
        option = interaction.data["values"][0]
        if option == "Manage Forums":
            embed = discord.Embed(color=discord.Colour.dark_embed())
            embed.set_author(
                name="Forum Posts",
                icon_url="https://cdn.discordapp.com/emojis/1223062562782838815.webp?size=96&quality=lossless",
            )
            embed.set_thumbnail(url=interaction.guild.icon)
            Forums = await interaction.client.db["Forum Configuration"].find(
                {"guild_id": interaction.guild.id}
            ).to_list(length=None)
            for form in Forums:
                embed.add_field(
                    name=f"<:forum:1223062562782838815> {form.get('name')}",
                    value=f"{replytop} **Created:** <@{form.get('creator') if form.get('creator') else 'Unknown'}> (`{form.get('creator') if form.get('creator') else 'Unknown'}`)\n{replybottom} **Channel:** <#{form.get('channel_id') if form.get('channel_id') else 'Unknown'}>",
                    inline=False,
                )
                if 20 <= len(embed.fields):
                    break
            if len(embed.fields) == 0:
                embed.description == "> There are no custom commands!"

            view = ForumManagent(self.author)
            if IsSeperateBot():
                view.add.label = "Add"
                view.edit.label = "Edit"
                view.remove.label = "Delete"
            await interaction.followup.send(view=view, embed=embed)


class ForumManagent(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__()
        self.author = author

    @discord.ui.button(emoji="<:Add:1163095623600447558>")
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)        
        await interaction.response.send_modal(CreateForum(interaction.user))

    @discord.ui.button(emoji="<:Pen:1235001839036923996>")
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)        
        view = discord.ui.View()
        Forums = await interaction.client.db["Forum Configuration"].find({"guild_id": interaction.guild.id}).to_list(
            length=None
        )
        Options = []
        for form in Forums:
            if any(option.label == form.get("name") for option in Options):
                continue
            Options.append(
                discord.SelectOption(label=form.get("name"), value=form.get("name"))
            )

            if 25 <= len(Options):
                break
        if len(Options) == 0:
            return await interaction.response.send_message(
                f"  **{interaction.user.display_name},** there are no forums.",
                ephemeral=True,
            )
        view.add_item(ForumSelection(interaction.user, "Edit", Options))
        await interaction.response.edit_message(view=view, embed=None)
        del Forums

    @discord.ui.button(emoji="<:Subtract:1229040262161109003>")
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)        
        view = discord.ui.View()
        Forums = await interaction.client.db["Forum Configuration"].find({"guild_id": interaction.guild.id}).to_list(
            length=None
        )
        Options = []
        for form in Forums:
            if any(option.label == form.get("name") for option in Options):
                continue
            Options.append(
                discord.SelectOption(label=form.get("name"), value=form.get("name"))
            )

            if 25 <= len(Options):
                break
        if len(Options) == 0:
            return await interaction.response.send_message(
                f"  **{interaction.user.display_name},** there are no forums.",
                ephemeral=True,
            )
        view.add_item(ForumSelection(interaction.user, "Remove", Options))
        await interaction.response.edit_message(view=view, embed=None)


class ForumSelection(discord.ui.Select):
    def __init__(self, author: discord.User, typed: str, options: list):
        super().__init__(min_values=1, max_values=1, options=options)
        self.author = author
        self.typed = typed

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        await interaction.response.defer()
        from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed, Embed

        Forum = await interaction.client.db["Forum Configuration"].find_one(
            {"guild_id": interaction.guild.id, "name": self.values[0]}
        )
        if not Forum:
            return await interaction.followup.send(
                f"  **{interaction.user.display_name},** theres no forum named that.",
                ephemeral=True,
            )
        if self.typed == "Remove":
            await interaction.client.db["Forum Configuration"].delete_one(
                {"guild_id": interaction.guild.id, "name": self.values[0]}
            )
            return await interaction.edit_original_response(
                content=f" **{interaction.user.display_name},** successfully deleted the forum.",
                embed=None,
                view=None,
            )
        elif self.typed == "Edit":
            embed = await DisplayEmbed(Forum, interaction.user)
            data = {
                "name": Forum.get("name"),
                "channel_id": Forum.get("channel_id"),
                "Close": Forum.get("Close"),
                "Lock": Forum.get("Lock"),
            }
            view = Embed(interaction.user, FinalFunc, "Forum", data)
            view.remove_item(view.reset)
            view.remove_item(view.RemoveEmbed)
            view.remove_item(view.Permissions)
            view.remove_item(view.Content)

            await interaction.edit_original_response(
                embed=embed,
                view=view,
            )


class CreateForum(discord.ui.Modal, title="Create Forum"):
    def __init__(self, author: discord.member):
        super().__init__()
        self.name = discord.ui.TextInput(
            label="Forum Name", max_length=100, required=True
        )
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        Forum = await interaction.client.db["Forum Configuration"].find_one(
            {"guild_id": interaction.guild.id, "name": self.name.value}
        )
        if Forum:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** theres already a forum named that.",
                ephemeral=True,
            )
        from Cogs.Configuration.Components.EmbedBuilder import Embed

        view = Embed(
            interaction.user,
            FinalFunc,
            "Forum",
            {"name": self.name.value},
        )
        view.remove_item(view.reset)
        view.remove_item(view.RemoveEmbed)
        view.remove_item(view.Permissions)
        view.remove_item(view.Content)

        await interaction.response.edit_message(
            view=view, embed=discord.Embed(title="Untitled"), content=None
        )


async def FinalFunc(interaction: discord.Interaction, datad: dict):
    embed = interaction.message.embeds[0] if interaction.message.embeds else None

    if embed:
        if not datad.get("channel_id"):
            await interaction.response.send_message(
                f" **{interaction.user.display_name},** you need to select a forum channel before finishing.",
                ephemeral=True,
            )
            return
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
        if datad.get("Close"):
            data["Close"] = datad["Close"]
        if datad.get("Lock"):
            data["Lock"] = datad["Lock"]
        if datad.get("channel_id"):
            data["channel_id"] = datad["channel_id"]
        if datad.get("ping"):
            data["role"] = datad["ping"]

    result = await interaction.client.db["Forum Configuration"].update_one(
        {"name": datad.get("name"), "guild_id": interaction.guild.id},
        {"$set": data},
        upsert=True,
    )
    await interaction.response.edit_message(
        content=f" **{interaction.user.display_name},** success.",
        view=None,
        embed=None,
    )


async def ForumsEmbed(interaction: discord.Interaction, embed: discord.Embed):
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> Forums are a way of automatically sending a message to a forum when its made. You can find out more at [the documentation](https://docs.astrobirb.dev/)."
    return embed
