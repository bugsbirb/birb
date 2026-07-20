import discord
from discord.ext import commands

from core.discord.Module import ModuleCheck
from core.discord.permissions import RequireStaff


class MessageCounter(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return
        if message.author.bot:
            return
        if message.author is None:
            return
        if message.channel is None:
            return
        config = await self.client.db["Config"].find_one({"_id": message.guild.id})
        if not config:
            return
        if message.author and message.channel is None:
            return
        if message.author.bot:
            return
        if not await ModuleCheck(message.guild.id, "Quota"):
            return

        if not RequireStaff(config, message.author):
            return

        if message.channel.id in config.get("Message Quota", {}).get(
            "Ignored Channels", []
        ):
            return

        await self.client.db["messages"].update_one(
            {"guild_id": message.guild.id, "user_id": message.author.id},
            {"$inc": {"message_count": 1}},
            upsert=True,
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(MessageCounter(client))
