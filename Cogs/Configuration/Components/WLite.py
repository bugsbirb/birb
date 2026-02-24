import discord
from utils.permissions import premium
from utils.HelpEmbeds import NoPremium
from utils.emojis import *
from utils.HelpEmbeds import NotYourPanel


class WLiteOption(discord.ui.Select):
    def __init__(self, author: discord.Member):
        super().__init__(
            options=[
                discord.SelectOption(
                    label="Edit Profile", emoji="<:Pen:1235001839036923996>"
                ),
            ]
        )
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if not await premium(interaction.guild.id):
            return await interaction.response.send_message(
                embed=NoPremium(), ephemeral=True
            )
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )

        await interaction.response.send_modal(EditProfile(self.author))


class EditProfile(discord.ui.Modal):
    def __init__(self, author: discord.Member):
        super().__init__(title="Edit Profile", timeout=360)
        self.author = author
        self.nickname = discord.ui.Label(
            text="Nickname",
            component=discord.ui.TextInput(placeholder="Wumpus...", required=False),
            description="This will be the bots username, only in this server.",
        )
        self.avatar = discord.ui.Label(
            text="Avatar",
            description="This will be the bots avatar, only in this server.",
            component=discord.ui.FileUpload(min_values=1, required=False),
        )
        self.add_item(self.nickname)
        self.add_item(self.avatar)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not await premium(interaction.guild.id):
            return await interaction.followup.send(embed=NoPremium(), ephemeral=True)
        assert isinstance(self.nickname.component, discord.ui.TextInput)
        assert isinstance(self.avatar.component, discord.ui.FileUpload)
        avatar = (
            self.avatar.component.values[0] if self.avatar.component.values else None
        )
        nickname = self.nickname.component.value
        try:
            await interaction.guild.me.edit(
                nick=nickname,
                avatar=await avatar.read() if avatar else None,
                reason=f"Bot profile changed, edited by {self.author.id} ",
            )
        except (discord.Forbidden, discord.HTTPException):
            return await interaction.followup.send(
                content=f"{crisis} **{interaction.user.display_name},** an error occured while trying to edit the bot in this server.",
                ephemeral=True,
            )
        return await interaction.followup.send(
            f"{tick} **{interaction.user.display_name},** successfully updated the bots profile in this server.",
            ephemeral=True,
        )


async def WLiteEmbed(interaction: discord.Interaction) -> discord.Embed:
    embed = discord.Embed(color=discord.Colour.dark_embed())
    embed.set_author(
        name="Edit Profile",
        icon_url=interaction.guild.icon,
    )
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = "> Customize your bot's profile in this server."
    embed.add_field(
        name="<:settings:1207368347931516928> Bot Profile",
        value=f"> **Nickname:** {interaction.guild.me.nick or 'Not Set'}",
        inline=False,
    )
    return embed
