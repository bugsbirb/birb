import discord
import discord.http
from utils.emojis import *

from dotenv import load_dotenv

load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# Customisation = DB["Customisation"]
# Configuration = DB["Config"]
# interaction.client.db["Auto Responders"] = DB["Auto interaction.client.db["Auto Responders"]"]
# premium = DB["Premium"]


class AutoResponderOptions(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Manage Responses",
                    emoji="<:autoresponse:1250481563615887391>",
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
        if self.values[0] == "Manage Responses":
            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_author(
                name="Auto Responders",
                icon_url="https://cdn.discordapp.com/emojis/1250481563615887391.webp?size=96&quality=lossless",
            )
            embed.set_thumbnail(url=interaction.guild.icon)
            Responses = await interaction.client.db["Auto Responders"].find(
                {"guild_id": interaction.guild.id}
            ).to_list(length=None)
            for response in Responses:
                embed.add_field(
                    name=f"{response.get('trigger')}",
                    value=f"{replytop} `Responses:` {response.get('response')}\n{replybottom} `Similarity:` {response.get('similarity', 'N/A')}%",
                    inline=False,
                )
                if 25 <= len(embed.fields):
                    break
            view = AutoResponder(self.author)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class AutoResponder(discord.ui.View):
    def __init__(self, author):
        self.author = author
        super().__init__(timeout=360)

    @discord.ui.button(label="Create", style=discord.ButtonStyle.green, row=1)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_modal(Create())

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, row=1)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.send_modal(DeleteByTrigger2())


class Create(discord.ui.Modal):
    def __init__(self):
        self.trigger = discord.ui.TextInput(
            label="Trigger", style=discord.TextStyle.long
        )
        self.response = discord.ui.TextInput(
            label="Response", style=discord.TextStyle.long
        )
        self.snuzzy = discord.ui.TextInput(
            label="Similarity",
            style=discord.TextStyle.short,
            required=False,
            placeholder="How similiar it has to be to the trigger to respond (1 - 100) Recommend: (70 - 100)",
        )
        super().__init__(title="Auto Responder", timeout=360)

        self.add_item(self.trigger)
        self.add_item(self.response)
        self.add_item(self.snuzzy)

    async def on_submit(self, interaction: discord.Interaction):
        result = await interaction.client.db["Auto Responders"].find_one(
            {"guild_id": interaction.guild.id, "trigger": self.trigger.value}
        )
        if result:
            await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** another response is using the same trigger.",
                ephemeral=True,
            )
            return
        try:
            if self.snuzzy.value is not None or "":
                sim = int(self.snuzzy.value)
            else:
                sim = None
        except ValueError:
            sim = None
        await interaction.client.db["Auto Responders"].insert_one(
            {
                "guild_id": interaction.guild.id,
                "trigger": self.trigger.value,
                "response": self.response.value,
                "similarity": sim,
            }
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** response created.",
            embed=None,
            view=None,
        )


class EditModal(discord.ui.Modal):
    def __init__(self, trigger, response, similarity):
        self.trigger = discord.ui.TextInput(
            label="Trigger", style=discord.TextStyle.long, default=trigger
        )
        self.response = discord.ui.TextInput(
            label="Response", style=discord.TextStyle.long, default=response
        )

        self.snuzzy = discord.ui.TextInput(
            label="Similarity",
            style=discord.TextStyle.short,
            required=False,
            placeholder="How similiar it has to be to the trigger to respond (1 - 10)",
            default=similarity,
        )
        super().__init__(title="Auto Responder", timeout=360)
        self.add_item(self.trigger)
        self.add_item(self.response)
        self.add_item(self.snuzzy)

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.client.db["Auto Responders"].update_one(
            {"guild_id": interaction.guild.id},
            {
                "$set": {
                    "trigger": self.trigger.value,
                    "response": self.response.value,
                    "similarity": self.snuzzy.value,
                }
            },
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** response edited.",
            embed=None,
            view=None,
        )


class DeleteByTrigger(discord.ui.View):
    def __init__(self, author):
        self.author = author
        super().__init__(timeout=360)

    @discord.ui.button(label="Delete By Text", row=2, style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_modal(DeleteByTrigger2())


class DeleteByTrigger2(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Delete By Text", timeout=360)
        self.trigger = discord.ui.TextInput(
            label="Trigger Text", style=discord.TextStyle.long
        )
        self.add_item(self.trigger)

    async def on_submit(self, interaction: discord.Interaction):
        result = await interaction.client.db["Auto Responders"].find_one(
            {"guild_id": interaction.guild.id, "trigger": self.trigger.value}
        )
        if not result:
            await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** no response found with that trigger.",
                ephemeral=True,
            )
            return
        await interaction.client.db["Auto Responders"].delete_one(
            {"guild_id": interaction.guild.id, "trigger": self.trigger.value}
        )
        await interaction.response.edit_message(
            content=f"  **{interaction.user.display_name},** response deleted.",
            embed=None,
            view=None,
        )


async def AutoResponseEmbed(interaction: discord.Interaction, embed: discord.Embed):
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> Autoresponses are automatic messages sent when a message matches a trigger. You can set the similarity of the trigger, so it only responds when the message is similar enough.\n\nYou can find out more at [the documentation](https://docs.astrobirb.dev/)."
    return embed
