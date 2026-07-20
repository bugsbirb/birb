import discord
from bson import ObjectId
from discord.ext import commands


class on_promotion_log(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_promotion_log(
        self,
        _id: ObjectId,
        action: str,
        author: discord.Member,
        unmodified: dict = None,
    ):
        promotion = await self.client.db["promotions"].find_one({"_id": _id})
        if not promotion:
            return
        try:
            guild = await self.client.fetch_guild(promotion.get("guild_id"))
        except (discord.NotFound, discord.HTTPException):
            return
        try:
            staff = await guild.fetch_member(int(promotion.get("staff")))
        except (discord.NotFound, discord.HTTPException):
            return

        config = await self.client.config.find_one({"_id": guild.id})
        if not config:
            return
        if not config.get("Promo", None):
            return
        try:
            LogsChannel = await guild.fetch_channel(
                int(config.get("Promo", {}).get("LogChannel", None))
            )
        except (discord.Forbidden, discord.NotFound, TypeError):
            return
        if not LogsChannel:
            return

        view = None
        if promotion.get("jump_url"):
            view = discord.ui.View().add_item(
                discord.ui.Button(
                    label="Jump To",
                    style=discord.ButtonStyle.link,
                    url=promotion.get("jump_url"),
                )
            )
        color = {
            "create": discord.Color.brand_green(),
            "delete": discord.Color.brand_red(),
            "modify": discord.Color.dark_purple(),
        }
        E = discord.Embed(color=color.get(action), timestamp=discord.utils.utcnow())
        E.set_footer(text=f"@{author.name}", icon_url=author.display_avatar)

        if action == "create":
            E.title = "Promotion Created"
            E.description = f"> **ID:** `{promotion.get('random_string')}`\n> **Role:** <@&{promotion.get('new')}>\n> **Reason:** {promotion.get('reason')}\n> **Notes:** {promotion.get('notes', 'N/A')}"
        elif action == "modify":
            E.title = "Promotion Modified"
            E.add_field(
                name="Before",
                value=f"> **ID:** `{unmodified.get('random_string')}`\n> **Role:** <@&{unmodified.get('new')}>\n> **Reason:** {unmodified.get('reason')}\n> **Notes:** {unmodified.get('notes', 'N/A')}",
            )
            E.add_field(
                name="After",
                value=f"> **ID:** `{promotion.get('random_string')}`\n> **Role:** <@&{promotion.get('new')}>\n> **Reason:** {promotion.get('reason')}\n> **Notes:** {promotion.get('notes', 'N/A')}",
            )
        elif action == "delete":
            E.title = "Promotion Voided"
            E.description = f"> **ID:** `{promotion.get('random_string')}`\n> **Role:** <@&{promotion.get('new')}>\n> **Reason:** {promotion.get('reason')}\n> **Notes:** {promotion.get('notes', 'N/A')}"
        try:
            await LogsChannel.send(embed=E, view=view)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_promotion_log(client))
