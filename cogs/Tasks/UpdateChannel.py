from discord.ext import commands, tasks
import discord
import os


class UpdateChannel(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.UpdateChannelName.start()
        client.Tasks.add("Channel Name")

    @tasks.loop(minutes=10, reconnect=True)
    async def UpdateChannelName(self):
        if os.getenv("ENVIRONMENT") in ["development", "custom"]:
            return
        channel = self.client.get_channel(1131245978704420964)
        if not channel:
            return

        users = sum(guild.member_count or 0 for guild in self.client.guilds)
        try:
            await channel.edit(name=f"{len(self.client.guilds)} Guilds | {users} Users")
        except (discord.HTTPException, discord.Forbidden):
            pass


async def setup(client: commands.Bot) -> None:
    await client.add_cog(UpdateChannel(client))
