import discord


async def StaffListEmbed(interaction: discord.Interaction, embed: discord.Embed):
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    embed.description = (
        "> The Staff Panel displays a list of staff members, sorted by rank. "
        "You can view individual staff details, including their roles and join dates. "
        "For more information, visit [the documentation](https://docs.astrobirb.dev)."
    )
    return embed
