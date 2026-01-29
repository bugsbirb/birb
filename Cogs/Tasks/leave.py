import asyncio
from datetime import datetime
from bson import ObjectId
from typing import Union
from discord.ext import commands, tasks
import os
import sentry_sdk

async def TimeLeftz(loa: dict) -> Union[int, str]:
    if not loa or not loa.get("start_time") or not loa.get("end_time"):
        return "N/A"

    Added = 0
    if loa.get("AddedTime"):
        Added = int(loa["AddedTime"].get("Time", 0))

    Removed = 0
    if loa.get("RemovedTime"):
        Removed = int(loa["RemovedTime"].get("Time", 0))

    End = loa["end_time"].timestamp() + Added - Removed
    return int(End - datetime.now().timestamp())


class Leave(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        self.ExpTask.start()
        self.SchTasks.start()
        self.client.Tasks.add("ExpTask")
        self.client.Tasks.add("SchTask")

    @tasks.loop(seconds=10)
    @sentry_sdk.trace()
    async def ExpTask(self):
        if os.getenv("CUSTOM_GUILD"):
            LOAs = (
                await self.client.db["loa"]
                .find(
                    {
                        "start_time": {"$exists": True},
                        "end_time": {"$exists": True},
                        "active": True,
                        "guild_id": int(os.getenv("CUSTOM_GUILD")),
                    }
                )
                .to_list(length=None)
            )
        else:

            LOAs = (
                await self.client.db["loa"]
                .find(
                    {
                        "start_time": {"$exists": True},
                        "end_time": {"$exists": True},
                        "active": True,
                    }
                )
                .to_list(length=None)
            )
        semaphore = asyncio.Semaphore(3)

        async def Process(loa):
            async with semaphore:
                TimeLeft = await TimeLeftz(loa)
                if TimeLeft in {None, "N/A"}:
                    return

                if TimeLeft <= 0:
                    await self.client.db["loa"].update_one(
                        {"_id": ObjectId(loa["_id"])}, {"$set": {"active": False}}
                    )
                    self.client.dispatch("leave_end", loa.get("_id"))

        await asyncio.gather(*(Process(loa) for loa in LOAs))
        del LOAs

    @tasks.loop(seconds=10)
    @sentry_sdk.trace()
    async def SchTasks(self):
        if os.getenv("CUSTOM_GUILD"):
            LOAs = (
                await self.client.db["loa"]
                .find(
                    {
                        "start_time": {"$exists": True},
                        "end_time": {"$exists": True},
                        "scheduled": True,
                        "active": False,
                        "request": False,
                        "guild_id": int(os.getenv("CUSTOM_GUILD")),
                    }
                )
                .to_list(length=None)
            )
        else:
            LOAs = (
                await self.client.db["loa"]
                .find(
                    {
                        "start_time": {"$exists": True},
                        "end_time": {"$exists": True},
                        "scheduled": True,
                        "active": False,
                        "request": False,
                    }
                )
                .to_list(length=None)
            )

        semaphore = asyncio.Semaphore(3)

        async def Process(loa):
            async with semaphore:
                if not loa.get("start_time"):
                    return
                if int(datetime.now().timestamp()) >= int(
                    loa["start_time"].timestamp()
                ):
                    await self.client.db["loa"].update_one(
                        {"_id": ObjectId(loa["_id"])},
                        {"$set": {"active": True, "scheduled": False}},
                    )
                    self.client.dispatch("leave_start", loa.get("_id"))

        await asyncio.gather(*(Process(loa) for loa in LOAs))
        del LOAs


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Leave(client))
