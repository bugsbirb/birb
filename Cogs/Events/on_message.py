from discord.ext import commands
import discord
class messageevent(commands.Cog):
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
        if config.get("Modules", {}).get("Quota", False) is False:
            return

        staff_role_ids = config.get("Permissions", {}).get("staffrole", [])
        admin_role_ids = config.get("Permissions", {}).get("adminrole", [])

        if message.channel.id in config.get("Message Quota", {}).get(
            "Ignored Channels", []
        ):
            return

        if not isinstance(staff_role_ids, list):
            staff_role_ids = [staff_role_ids]
        if not isinstance(admin_role_ids, list):
            admin_role_ids = [admin_role_ids]

        if any(role.id in staff_role_ids for role in message.author.roles):
            guild_id = message.guild.id
            author_id = message.author.id

            await self.client.db["messages"].update_one(
                {"guild_id": guild_id, "user_id": author_id},
                {"$inc": {"message_count": 1}},
                upsert=True,
            )
            return
        elif any(role.id in admin_role_ids for role in message.author.roles):
            guild_id = message.guild.id
            author_id = message.author.id

            await self.client.db["messages"].update_one(
                {"guild_id": guild_id, "user_id": author_id},
                {"$inc": {"message_count": 1}},
                upsert=True,
            )
            return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(messageevent(client))
