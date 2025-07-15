import os
import discord
from discord.ext import commands, tasks
import datetime
from utils.emojis import *
import random

import asyncio
from utils.Module import ModuleCheck

MONGO_URL = os.getenv("MONGO_URL")
environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")

import asyncio


class qotd(commands.Cog):
    def __init__(self, client: commands.Bot):

        self.client = client
        self.semaphore = asyncio.Semaphore(10)
        client.Tasks.add("QOTD")

    async def FetchQuestion(self, Used, server: discord.Guild):
        questionresult = (
            await self.client.db["Question Database"].find({}).to_list(length=None)
        )
        Unusued = [q for q in questionresult if q["question"] not in Used]

        if not Unusued:
            await self.client.db["qotd"].update_one(
                {"guild_id": server.id}, {"$set": {"messages": []}}
            )
            return random.choice(questionresult).get("question")
        del questionresult
        return random.choice(Unusued).get("question")

    async def ProcesssQOTD(self, results):
        async with self.semaphore:
            try:
                postdate = results.get("nextdate", None)
                if postdate is None or postdate > datetime.datetime.utcnow():
                    return

                guild_id = int(results.get("guild_id"))
                guild = await self.client.fetch_guild(guild_id)
                if guild is None:
                    await self.ProcessErrors(results, "Guild not found")
                    return

                messages = results.get("messages", [])
                question = await self.FetchQuestion(messages, guild)
                if question:
                    messages.append(question)

                ChannelID = results.get("channel_id", None)
                if ChannelID is None:
                    await self.ProcessErrors(results, "Channel not found")
                    return
                ChannelID = int(ChannelID)
                try:
                    channel = await guild.fetch_channel(ChannelID)
                except Exception:
                    await self.ProcessErrors(results, "Channel not found")
                    return
                if not await ModuleCheck(guild.id, "QOTD"):
                    await self.ProcessErrors(results, "Module not found")
                    return

                pingmsg = (
                    f"<@&{results.get('pingrole')}>" if results.get("pingrole") else ""
                )
                embed = discord.Embed(
                    title="<:Tip:1223062864793702431> Question of the Day",
                    description=f"{question}",
                    color=discord.Color.yellow(),
                    timestamp=datetime.datetime.utcnow(),
                )

                day = results.get("day", 0) + 1
                embed.set_footer(
                    text=f"Day #{day}",
                    icon_url="https://cdn.discordapp.com/emojis/1231270156647403630.webp?size=96&quality=lossless",
                )

                msg = await channel.send(
                    content=pingmsg,
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(roles=True),
                )

                await self.client.db["qotd"].update_one(
                    {"guild_id": guild_id},
                    {
                        "$set": {
                            "nextdate": datetime.datetime.utcnow()
                            + datetime.timedelta(days=1),
                            "messages": messages,
                            "day": day,
                            "LastMessage": {
                                "id": msg.id,
                                "channel_id": msg.channel.id,
                                "question": question,
                            },
                        }
                    },
                    upsert=True,
                )

                if results.get("qotdthread"):
                    await msg.create_thread(name="QOTD Discussion")

            except Exception as e:
                await self.ProcessErrors(results, e)

    async def ProcessErrors(self, results, e):
        GuildID = results.get("guild_id")
        attempts = results.get("attempts", 0) + 1
        if attempts > 10:
            await self.client.db["qotd"].delete_one({"guild_id": GuildID})
            return
        else:
            await self.client.db["qotd"].update_one(
                {"guild_id": GuildID},
                {"$set": {"attempts": attempts}, "$push": {"errors": str(e)}},
            )

    @tasks.loop(minutes=5, reconnect=True)
    async def sendqotd(self) -> None:
        result = None
        filter = {"nextdate": {"$lte": datetime.datetime.utcnow()}}
        if bool(environment == "custom"):
            filter["guild_id"] = int(guildid)
        result = await self.client.db["qotd"].find(filter).to_list(length=None)
        if not result:
            return

        tasks = [self.ProcesssQOTD(results) for results in result]
        await asyncio.gather(*tasks)

    @commands.Cog.listener()
    async def on_ready(self):
        self.sendqotd.start()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(qotd(client))
