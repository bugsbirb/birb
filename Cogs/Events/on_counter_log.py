import discord
from discord.ext import commands
from bson import ObjectId
from typing import Literal


class on_counter_log(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_counter_reset(
        self,
        serverId: int,
        action: str,
        author: discord.Member,
        type: Literal["Tickets", "Messages", "Both"],
    ):
        try:
            guild = await self.client.fetch_guild(serverId)
        except (discord.NotFound, discord.HTTPException, discord.NotFound):
            return

        config = await self.client.config.find_one({"_id": guild.id})
        if not config:
            return
        if type in ("Messages", "Both") and not config.get("Message Quota"):
            print('2')
            return

        if type in ("Tickets", "Both") and not config.get("Tickets"):
            return
        MLogsChannel = None
        TLogsChannel = None
        try:
            if type in ("Messages", "Both"):
                MLogsChannel = await guild.fetch_channel(
                    int(config.get("Message Quota", {}).get("LogChannel", None))
                )
            if type in ("Tickets", "Both"):
                TLogsChannel = await guild.fetch_channel(
                    int(config.get("Tickets", {}).get("LogChannel", None))
                )

        except (discord.Forbidden, discord.NotFound, TypeError):
            return
        
        view = None
        color = {
            "reset": discord.Color.brand_red(),
        }
        E = discord.Embed(color=color.get(action), timestamp=discord.utils.utcnow())
        E.set_footer(text=f"@{author.name}", icon_url=author.display_avatar)

        if MLogsChannel:
            if action == "reset":
                E.title = "Quota Reset"
                E.description = f"> Message counters has been reset. All counters have been reset to 0."
            try:
                await MLogsChannel.send(embed=E, view=view)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                return
        if TLogsChannel:
            if action == "reset":
                E.title = "Quota Reset"
                E.description = f"> Ticket counters has been reset. All counters have been reset to 0."
            try:
                await TLogsChannel.send(embed=E, view=view)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_counter_log(client))
