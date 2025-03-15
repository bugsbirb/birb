import discord
from utils.erm import GetIdentifier
from utils.emojis import *

class Integrations(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Roblox Groups", emoji="<:robloxWhite:1200584000390053899>"
                ),
                discord.SelectOption(
                    label="ERM",
                    emoji="<:erm:1203823601107861504>",
                ),
            ]
        )
        self.author = author

    async def callback(self, interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.response.defer()
        if self.values[0] == "ERM":

            code = await GetIdentifier()
            result = await interaction.client.db['integrations'].find_one(
                {"server": interaction.guild.id, "erm": {"$exists": True}}
            )
            if result and result.get("erm", None):
                code = result.get("erm")
            embed = discord.Embed(
                title="<:erm:1203823601107861504> ERM API Integration",
                color=discord.Colour.brand_red(),
                description=(
                    "To complete the integration with ERM, please authorize the application by clicking the 'Authorize' button below. "
                    "Once you have authorized, press the 'Done' button to finalize the integration. "
                    "If you encounter any issues, refer to the [documentation](https://docs.astrobirb.dev/) for assistance."
                ),
            )

            view = KeyButton(
                interaction.user,
                f"https://discord.com/oauth2/authorize?client_id=1090291300881932378&redirect_uri=https%3A%2F%2Fapi.ermbot.xyz%2Fapi%2FAuth%2FCallback&response_type=code&scope=identify%20guilds&prompt=none&state={code}",
                code,
            )
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        elif self.values[0] == "Roblox Groups":
            from utils.roblox import GetValidToken
            from utils.HelpEmbeds import NotRobloxLinked

            token = await GetValidToken(user=interaction.user)
            if not token:
                return await interaction.followup.send(
                    embed=NotRobloxLinked(), ephemeral=True
                )
            view = discord.ui.View()
            view.add_item(GroupOptions(interaction.user))

            await interaction.followup.send(view=view, ephemeral=True)


class GroupOptions(discord.ui.Select):
    def __init__(self, author: discord.User):
        options = [
            discord.SelectOption(
                label="Group", description="Link the roblox group to the server."
            )
        ]
        super().__init__(options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        modal = EnterGroup(self.author)
        await interaction.response.send_modal(modal)


class EnterGroup(discord.ui.Modal):
    def __init__(self, author: discord.User):
        super().__init__(title="Enter Roblox Group ID")
        self.author = author
        self.group_id = discord.ui.TextInput(
            label="Group ID", placeholder="Enter the Roblox Group ID here"
        )

        self.add_item(self.group_id)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not config:
            config = {"_id": interaction.guild.id, "groups": {}}
        if not config.get("groups"):
            config["groups"] = {}

        from utils.roblox import GetGroup2, GetUser
        from utils.HelpEmbeds import NotRobloxLinked

        group = await GetGroup2(self.group_id.value, interaction.user)
        if not group or not group.get('owner'):
            return await interaction.response.edit_message(
                content=f"  **{interaction.user.display_name},** I couldn't find the roblox group from your account.",
                view=None,
                embed=None,
            )
        user = await GetUser(user=interaction.user)
        if not user:
            return await interaction.response.edit_message(
                embed=NotRobloxLinked(), view=None, content=None
            )
        RobloxID = (
            int(user.get("roblox", {}).get("id"))
            if user.get("roblox", {})
            else int(user.get("sub"))
        )

        OwnerID = int(group.get("owner").split("/")[1])
        if not OwnerID == RobloxID:
            return await interaction.response.edit_message(
                content=f"  **{interaction.user.display_name},** you aren't the owner of this group. Please get the owner of it to link it.",
                view=None,
                embed=None,
            )

        config["groups"]["id"] = self.group_id.value
        await interaction.client.config.update_one(
            {"_id": interaction.guild.id}, {"$set": config}, upsert=True
        )
        await interaction.response.edit_message(
            content=f" **{interaction.user.display_name}**, group succesfully linked.",
            view=None,
        )


class KeyButton(discord.ui.View):
    def __init__(self, author, link, key):
        super().__init__(timeout=None)
        self.author = author
        self.add_item(
            discord.ui.Button(
                label="Authorise", style=discord.ButtonStyle.link, url=link
            )
        )
        self.key = key

    @discord.ui.button(
        label="Done",
        style=discord.ButtonStyle.green,
        emoji="<:Permissions:1207365901956026368>",
    )
    async def apikey(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.client.db['integrations'].update_one(
            {"server": interaction.guild.id},
            {"$set": {"erm": self.key}},
            upsert=True,
        )
        embed = discord.Embed(
            description=f"  **API Key has been successfully updated!**",
            color=discord.Colour.brand_green(),
        )
        await interaction.response.edit_message(embed=embed, view=None)


async def integrationsEmbed(interaction: discord.Interaction, embed: discord.Embed):
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = (
        "> Integrations are an easy way to connect external providers to the bot. "
        "You can find out more at [the documentation](https://docs.astrobirb.dev/)."
    )
    config = await interaction.client.config.find_one({"_id": interaction.guild.id})

    ERM = await interaction.client.db['integrations'].find_one(
        {"server": int(interaction.guild.id), "erm": {"$exists": True}}
    )
    Groups = config.get("groups", {}).get("id", None) if config else None
    embed.add_field(
        name="<:link:1206670134064717904> Integrations",
        value=f"> **Groups**: {'Linked' if Groups else 'Unlinked'}\n> **ERM:** {'Linked' if ERM else 'Unlinked'}",
        inline=False,
    )
    embed.add_field(
        name="<:Modules:1296530049381568522> Functions",
        value="> * Infraction Types\n> -# We are still looking to add more purposes to integrations",
    )

    return embed
