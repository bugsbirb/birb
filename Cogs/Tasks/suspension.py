import discord
from discord.ext import commands, tasks
import os
from utils.emojis import *
from datetime import datetime


environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")


class EmptyCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.check_suspensions.start()
        client.Tasks.add("Suspension")

    @tasks.loop(minutes=5, reconnect=True)
    async def check_suspensions(self):

        print("[👀] Checking suspensions")
        current_time = datetime.now()
        if environment == "custom":
            filter = {
                "end_time": {"$lte": current_time},
                "action": "Suspension",
                "guild_id": str(guildid),
            }
        else:

            filter = {"end_time": {"$lte": current_time}, "action": "Suspension"}
        suspensions = self.client.db["Suspensions"]
        suspension_requests = suspensions.find(filter)

        async for request in suspension_requests:
            end_time = request["end_time"]
            user_id = request["staff"]
            guild_id = request["guild_id"]
            guild = self.client.get_guild(guild_id)

            if guild is None:
                await suspensions.delete_one(
                    {"guild_id": guild_id, "staff": user_id, "end_time": end_time}
                )
                continue

            try:
                member = await guild.fetch_member(user_id)
            except discord.NotFound:
                member = None

            if member is None:
                continue

            try:
                user = await self.client.fetch_user(user_id)
            except discord.NotFound:
                user = None

            if user is None:
                continue

            if current_time >= end_time:
                delete_filter = {
                    "guild_id": guild_id,
                    "staff": user_id,
                    "action": "Suspension",
                }

                await suspensions.delete_one(delete_filter)
                print(f"[Suspensions] @{user.name} suspension has concluded.")

                roles_removed = request.get("roles_removed", None)
                if roles_removed:
                    roles_to_return = [
                        discord.utils.get(guild.roles, id=role_id)
                        for role_id in roles_removed
                    ]
                    roles_to_return = [
                        role for role in roles_to_return if role is not None
                    ]

                    if roles_to_return:
                        try:
                            await member.add_roles(*roles_to_return, reason="Suspension roles returned.")
                        except discord.Forbidden:
                            print(
                                f"[⚠️] Failed to restore roles to {member.name} in {guild.name}"
                            )
                            continue

                if user:
                    try:
                        await user.send(
                            f"{tick} Your suspension in **@{guild.name}** has ended."
                        )
                    except discord.Forbidden:
                        print(
                            f"[⚠️] Failed to send message to {user.name} in {guild.name}"
                        )
                        continue
                if request.get("msg_id"):
                    config = await self.client.db["Config"].find_one(
                        {"_id": request.get("guild_id")}
                    )
                    if not config:
                        return
                    if not config.get("Suspensions", {}):
                        return
                    if (
                        not self.client.db["Config"]
                        .get("Suspensions", {})
                        .get("channel")
                    ):
                        return
                    channel = self.client.get_channel(
                        int(config.get("Suspensions", {}).get("channel"))
                    )
                    if channel:
                        try:
                            message = await channel.fetch_message(request.get("msg_id"))
                            await message.reply(
                                f"<:suspensions:1234998406938755122> The suspension has concluded. Any taken roles have been replenished."
                            )
                        except (discord.NotFound, discord.HTTPException):
                            continue
        del suspension_requests


async def setup(client):
    await client.add_cog(EmptyCog(client))
