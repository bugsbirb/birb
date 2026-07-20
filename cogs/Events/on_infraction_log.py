import discord
from bson import ObjectId
from discord.ext import commands


class on_infraction_log(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_infraction_log(
        self,
        _id: ObjectId,
        action: str,
        author: discord.Member,
        unmodified: dict = None,
    ):
        inf = await self.client.db["infractions"].find_one({"_id": _id})
        if not inf:
            return
        try:
            guild = await self.client.fetch_guild(inf.get("guild_id"))
        except (discord.NotFound, discord.HTTPException, discord.NotFound):
            return
        try:
            staff = await guild.fetch_member(int(inf.get("staff")))
        except (discord.NotFound, discord.HTTPException, discord.NotFound):
            return

        config = await self.client.config.find_one({"_id": guild.id})
        if not config:
            return
        if not config.get("Infraction", None):
            return
        try:
            LogsChannel = await guild.fetch_channel(
                int(config.get("Infraction", {}).get("LogChannel", None))
            )
        except (discord.Forbidden, discord.NotFound, TypeError):
            return
        if not LogsChannel:
            return

        view = None
        if inf.get("jump_url"):
            view = discord.ui.View().add_item(
                discord.ui.Button(
                    label="Jump To",
                    style=discord.ButtonStyle.link,
                    url=inf.get("jump_url"),
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
            E.title = "Infraction Created"
            E.description = f"> **ID:** `{inf.get('random_string')}`\n> **Action:** {inf.get('action')}\n> **Reason:** {inf.get('reason')}\n> **Notes:** {inf.get('notes', 'N/A')}"
            if inf.get("Updated"):
                UP = inf.get("Updated", {})
                if UP.get("AddedRoles"):
                    value = "> "
                    E.add_field(
                        name="Added Roles",
                        value=value.join(
                            [
                                f"<@&{role_id}>"
                                for role_id in inf["Updated"]["AddedRoles"]
                            ]
                        ),
                        inline=False,
                    )
                if UP.get("RemovedRoles"):
                    value = "> "
                    E.add_field(
                        name="Removed Roles",
                        value=value.join(
                            [
                                f"<@&{role_id}>"
                                for role_id in inf["Updated"]["RemovedRoles"]
                            ]
                        ),
                        inline=False,
                    )
                if (
                    UP.get("VoidedShift")
                    or UP.get("ChangedGroupRole")
                    or UP.get("DbRemoval")
                ):
                    Extra = ""
                    if UP.get("VoidedShift"):
                        Extra += "> Voided Shift"
                    if UP.get("ChangedGroupRole"):
                        Extra += "> Changed Group Role"
                    if UP.get("DbRemoval"):
                        Extra += "> Staff Database Removal"
                    if not Extra == "":
                        E.add_field(name="Additional", value=Extra, inline=False)

        elif action == "modify":
            E.title = "Infraction Modified"
            E.add_field(
                name="Before",
                value=f"> **ID:** `{unmodified.get('random_string')}`\n> **Action:** {unmodified.get('action')}\n> **Reason:** {unmodified.get('reason')}\n> **Notes:** {unmodified.get('notes', 'N/A')}",
            )
            E.add_field(
                name="After",
                value=f"> **ID:** `{inf.get('random_string')}`\n> **Action:** {inf.get('action')}\n> **Reason:** {inf.get('reason')}\n> **Notes:** {inf.get('notes', 'N/A')}",
            )
        if action == "delete":
            E.title = "Infraction Voided"
            E.description = f"> **ID:** `{inf.get('random_string')}`\n> **Action:** {inf.get('action')}\n> **Reason:** {inf.get('reason')}\n> **Notes:** {inf.get('notes', 'N/A')}"
        try:
            await LogsChannel.send(embed=E, view=view)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_infraction_log(client))
