import discord
from core.format import ReplaceVariables


async def ReplaceData(data, replacements):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = await ReplaceData(value, replacements)
        return data
    if isinstance(data, list):
        return [await ReplaceData(item, replacements) for item in data]
    if isinstance(data, str):
        return ReplaceVariables(data, replacements)
    return data


async def DisplayEmbed(
    data: dict, user: discord.User = None, replacements: dict = None
):
    if not data:
        return None
    replacements = replacements or {}

    data = await ReplaceData(data, replacements)
    emdata = data.get("embed", {})
    embed = discord.Embed(color=discord.Color.dark_embed())

    if title := emdata.get("title"):
        embed.title = title

    if description := emdata.get("description"):
        embed.description = description

    if thumbnail := emdata.get("thumbnail"):
        if thumbnail == "{staff.avatar}":
            if user:
                embed.set_thumbnail(url=user.display_avatar)
        else:
            embed.set_thumbnail(url=thumbnail)

    if (image := emdata.get("image")) and image != "{image}":
        embed.set_image(url=image)

    if author := emdata.get("author"):
        if name := author.get("name"):
            icon_url = author.get("icon_url")
            if icon_url == "{author.avatar}":
                icon_url = replacements.get("author.avatar")
            if isinstance(icon_url, (tuple, list)):
                icon_url = icon_url[0] if icon_url else None
            embed.set_author(name=name, icon_url=str(icon_url) if icon_url else None)

    for field in emdata.get("fields", [])[:25]:
        name, value = field.get("name"), field.get("value")
        if name and value:
            embed.add_field(name=name, value=value, inline=field.get("inline", False))

    color = emdata.get("color", "2b2d31")
    if (
        isinstance(color, str)
        and len(color) == 6
        and all(c in "0123456789abcdefABCDEF" for c in color)
    ):
        embed.color = discord.Color(int(color, 16))

    if not any(
        [
            embed.title,
            embed.description,
            embed.author.name if embed.author else None,
            embed.fields,
        ]
    ):
        embed.description = "You need at least one of the following: Title, Description, Author, or Fields."

    return embed
