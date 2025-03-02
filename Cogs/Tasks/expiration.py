from discord.ext import commands
import os
import discord

from datetime import datetime
from discord.ext import tasks
from dotenv import load_dotenv


load_dotenv()
environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")


class expiration(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.CheckInfractions.start()
        print("[✅] Infraction Expiration loop started")

    @tasks.loop(minutes=30, reconnect=True)
    async def CheckInfractions(self):
        if not self.client.infractions_maintenance:
            return
        filter = {'expiration': {'$lte': datetime.now(), '$exists': True}, 'expired': {'$ne': True}}
        if environment == "custom":
            filter["guild_id"] = int(guildid)
        infractions = (
            await self.client.db["Infractions"].find(filter).to_list(length=None)
        )
        if not infractions:
            return
        for infraction in infractions:
            if not infraction.get("expiration"):
                continue
            if infraction.get("expiration") <= datetime.now():
                ActionType = await self.client.db["infractiontypeactions"].find_one(
                    {
                        "name": infraction.get("type"),
                        "guild_id": infraction.get("guild_id"),
                    }
                )
                if ActionType and ActionType.get("channel"):
                    Channel = self.client.get_channel(ActionType.get("channel"))
                else:

                    Channel = self.client.get_channel(infraction.get("channel_id"))
                if not Channel:
                    continue
                try:
                    message = await Channel.fetch_message(infraction.get("msg_id"))
                    if not message:
                        continue
                    embed = message.embeds[0]
                    exp = discord.Embed(
                        color=discord.Color.orange(),
                    ).set_author(
                        name="Infraction Expired",
                        icon_url="https://cdn.discordapp.com/emojis/1345821183328784506.webp?size=96",
                    )
                    await message.edit(
                        embeds=[embed, exp],
                    )
                except (discord.HTTPException, discord.NotFound):
                    pass
                await self.client.db["Infractions"].update_one(
                    {"_id": infraction.get("_id")}, {"$set": {"expired": True}}
                )

                del infraction
        del infractions


async def setup(client: commands.Bot) -> None:
    await client.add_cog(expiration(client))
