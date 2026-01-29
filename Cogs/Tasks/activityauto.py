import os
import random
import string
import re
import asyncio
from utils.HelpEmbeds import *
import discord
from discord.ext import commands, tasks
from Cogs.Modules.staff import quota as QUOTA

from utils.format import strtotime
from utils.emojis import *
from utils.Module import ModuleCheck
from utils.permissions import *
from datetime import timedelta, datetime
import logging
import sentry_sdk

logger = logging.getLogger(__name__)

environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")


class activityauto(commands.Cog):
    def __init__(self, client: commands.Bot):

        self.client = client
        self.Task.start()
        client.Tasks.add("Activity Expiration")

    @tasks.loop(minutes=5, reconnect=True)
    @sentry_sdk.trace()
    async def Task(self):

        if environment == "custom":
            autoactivityresult = (
                await self.client.db["auto activity"]
                .find({"guild_id": int(guildid)})
                .to_list(length=None)
            )
        else:
            autoactivityresult = (
                await self.client.db["auto activity"].find({}).to_list(length=None)
            )

        if not autoactivityresult:
            return

        for data in autoactivityresult:
            try:
                IsGod = bool(data.get("guild_id", 0) == 1092976553752789054)  # Temp
                if not data.get("enabled", False):
                    continue
                if not await ModuleCheck(data.get("guild_id", 0), "Quota"):
                    continue

                channel = self.client.get_channel(data.get("channel_id"))
                if not channel:
                    if IsGod:
                        logger.debug("[]")
                    continue

                days = [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]
                nextdate = data.get("nextdate")
                day = data.get("day", "").lower()
                CurrentDay = datetime.now().weekday()
                if day not in days:
                    continue

                specified = days.index(day)
                DayTill = (specified - CurrentDay) % 7
                if DayTill == 0:
                    if datetime.now() < nextdate:
                        NextDate = datetime.now()
                    else:
                        NextDate = datetime.now() + timedelta(days=7)
                else:
                    NextDate = datetime.now() + timedelta(days=DayTill)

                if NextDate < datetime.now():
                    NextDate = datetime.now() + timedelta(days=7)

                if datetime.now() < nextdate:
                    continue

                guild = await self.client.fetch_guild(data.get("guild_id"))
                if not guild:
                    continue

                await self.client.db["auto activity"].update_one(
                    {"guild_id": guild.id},
                    {"$set": {"nextdate": NextDate, "lastposted": datetime.now()}},
                )

                logger.info(f"[⏰] Sending Activity @{guild.name} next post is {NextDate}!")

                result = (
                    await self.client.qdb["messages"]
                    .find({"guild_id": guild.id})
                    .to_list(length=None)
                )
                if not result:
                    logger.debug("e")
                    continue

                passed = []
                failed = []
                OnLOA = []
                failedids = []

                semaphore = asyncio.Semaphore(2)

                async def Process(userdata):
                    async with semaphore:
                        try:
                            user = await guild.fetch_member(userdata.get("user_id"))
                        except:
                            return
                        if not user or not await check_admin_and_staff(guild, user):
                            return

                        message_data = await self.client.qdb["messages"].find_one(
                            {"guild_id": guild.id, "user_id": user.id}
                        )
                        config = await self.client.config.find_one({"_id": guild.id})
                        if (
                            not config
                            or not config.get("Message Quota")
                            or not message_data
                        ):
                            return

                        LoaRole = config.get("LOA", {}).get("role")
                        LoaStatus = (
                            any(role.id == LoaRole for role in user.roles)
                            if LoaRole
                            else False
                        )

                        quota, Name = QUOTA.GetQuota(self, user, config)
                        Messages = message_data.get("message_count", 0)

                        entry = f"> **{user.mention}** • `{Messages}` messages{Name}"

                        if LoaStatus:
                            OnLOA.append(entry)
                        elif Messages >= quota:
                            passed.append(entry)
                        else:
                            failed.append(entry)
                            failedids.append(user.id)

                await asyncio.gather(*(Process(userdata) for userdata in result))

                await self.client.db["auto activity"].update_one(
                    {"guild_id": guild.id}, {"$set": {"failed": failedids}}
                )

                def sort_key(entry):
                    return int(entry.split("•")[-1].strip().split(" ")[0].strip("`"))

                passed.sort(key=sort_key, reverse=True)
                failed.sort(key=sort_key, reverse=True)
                OnLOA.sort(key=sort_key, reverse=True)

                embeds = []

                passedembed = discord.Embed(
                    title="Passed", color=discord.Color.brand_green()
                )
                passedembed.set_image(url="https://www.astrobirb.dev/invisble.png")
                passedembed.description = (
                    "\n".join(passed) if passed else "> No users passed the quota."
                )

                loaembed = discord.Embed(title="On LOA", color=discord.Color.purple())
                loaembed.set_image(url="https://www.astrobirb.dev/invisble.png")
                loaembed.description = (
                    "\n".join(OnLOA) if OnLOA else "> No users on LOA."
                )

                failedembed = discord.Embed(
                    title="Failed", color=discord.Color.brand_red()
                )
                failedembed.set_image(url="https://www.astrobirb.dev/invisble.png")
                failedembed.description = (
                    "\n".join(failed) if failed else "> No users failed the quota."
                )
                
                failedembed.description = failedembed.description[:4096]
                loaembed.description = loaembed.description[:4096]
                passedembed.description = passedembed.description[:4096]

                embeds.append(passedembed)
                embeds.append(loaembed)
                embeds.append(failedembed)

                if channel:
                    view = ResetLeaderboard(failedids)
                    try:
                        await channel.send(embeds=embeds, view=view)
                        logger.info(f"[Activity Auto] successfully sent @{guild.name}")
                    except discord.Forbidden:
                        logger.error("[ERROR] Cannot send to channel.")
                else:
                    logger.warning("[NOTFOUND] Channel not found")

            except Exception as e:
                logger.error(f"[QUOTA ERROR] {e}")
                continue

        del autoactivityresult


class ResetLeaderboard(discord.ui.View):
    def __init__(self, failures: list = None):
        super().__init__(timeout=None)
        self.failures = failures

    @discord.ui.button(
        label="Reset Leaderboard",
        style=discord.ButtonStyle.danger,
        custom_id="persistent:resetleaderboard",
        emoji="<:staticload:1206248311280111616>",
    )
    async def reset_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not await has_admin_role(interaction):
            return
        button.label = f"Reset By @{interaction.user.display_name}"
        button.disabled = True
        await interaction.client.qdb["messages"].update_many(
            {"guild_id": interaction.guild.id}, {"$set": {"message_count": 0}}
        )
        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        label="Punish Failures",
        style=discord.ButtonStyle.danger,
        custom_id="persistent:punishfailures",
        emoji="<:hammer:1280559940788031663>",
    )
    async def punishfailures(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not await has_admin_role(interaction):
            return
        if not self.failures:
            result = await interaction.client.db["auto activity"].find_one(
                {"guild_id": interaction.guild.id}
            )
            self.failures = result.get("failed", [])
            if not result or self.failures is None or len(self.failures) == 0:
                await interaction.response.send_message(
                    f"{no} **{interaction.user.display_name}**, there are no failures to punish.",
                    ephemeral=True,
                )
                return

        await interaction.response.send_modal(ActionModal(self.failures))


class ActionModal(discord.ui.Modal, title="Action"):
    def __init__(self, failures: list = None):
        super().__init__(timeout=None)
        self.failures = failures
        self.action = discord.ui.TextInput(
            label="Action",
            placeholder="What action would you like to take?",
            style=discord.TextStyle.short,
            required=True,
        )
        self.add_item(self.action)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        action = self.action.value
        reason = "Failing message quota."
        notes = None
        expiration = None
        anonymous = True
        TypeActions = await interaction.client.db["infractiontypeactions"].find_one(
            {"guild_id": interaction.guild.id, "name": action}
        )
        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Config:
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name}**, the bot isn't setup you can do that in /config.",
                ephemeral=True,
            )
        if not Config.get("Infraction", None):
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name}**, the infraction module is not setup you can do that in /config.",
                ephemeral=True,
            )

        if Config.get("group", {}).get("id", None):
            from utils.roblox import GetValidToken
            from utils.HelpEmbeds import NotRobloxLinked

            Roblox = await GetValidToken(user=interaction.user)
            if not Roblox:
                return await interaction.followup.send(
                    embed=NotRobloxLinked(),
                    ephemeral=True,
                )
        try:
            channel = await interaction.client.fetch_channel(
                int(Config.get("Infraction", {}).get("channel", 0))
            )
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            return await interaction.followup.send(
                content=f"{crisis} **{interaction.user.display_name},** I can't find your infraction channel.",
                ephemeral=True,
            )
        if not channel:
            return await interaction.followup.send(
                content=f"{crisis} **{interaction.user.display_name},** I can't find your infraction channel.",
                ephemeral=True,
            )
        client = await interaction.guild.fetch_member(interaction.client.user.id)
        if (
            channel.permissions_for(client).send_messages is False
            or channel.permissions_for(client).view_channel is False
        ):
            return await interaction.followup.send(
                content=f"{crisis} **{interaction.user.display_name},** I don't have permissions to send messages in the infraction channel.",
                ephemeral=True,
            )
        if expiration and not re.match(r"^\d+[mhdws]$", expiration):
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name}**, invalid duration format. Use e.g. '1d', '2h'.",
                ephemeral=True,
            )
        if expiration:
            expiration = await strtotime(expiration)

        for Ids in self.failures:
            user = await interaction.guild.fetch_member(Ids)
            if user is None:
                await interaction.followup.send(
                    f"{no} **{interaction.user.display_name}**, user {Ids} not found.",
                    ephemeral=True,
                )
                continue

            Org = action
            action = Org
            escalated = False

            if TypeActions and TypeActions.get("Escalation", None):
                Escalation = TypeActions.get("Escalation")
                Threshold = Escalation.get("Threshold", None)
                NextType = Escalation.get("Next Type")
                if Threshold and NextType:
                    count = await interaction.client.db["infractions"].count_documents(
                        {
                            "guild_id": interaction.guild.id,
                            "staff": Ids,
                            "action": Org,
                            "Upscaled": {"$exists": False},
                        }
                    )
                    if isinstance(Threshold, str):
                        if count + 1 >= int(Threshold):
                            escalated = True
                            action = NextType

            random_string = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
            FormeData = {
                "guild_id": interaction.guild.id,
                "staff": user.id,
                "management": interaction.user.id,
                "action": action,
                "reason": reason,
                "notes": notes if notes else "`N/A`",
                "expiration": expiration,
                "random_string": random_string,
                "annonymous": anonymous,
                "timestamp": datetime.now(),
            }
            if escalated:
                FormeData[
                    "reason"
                ] += f"\n-# Automatically escalated to **{action}** from **{Org}**"

            InfractionResult = await interaction.client.db["infractions"].insert_one(
                FormeData
            )
            if not InfractionResult.inserted_id:
                await interaction.followup.send(
                    f"{crisis} **{interaction.user.display_name},** error submitting infraction.",
                    ephemeral=True,
                )
                continue

            if (
                Config.get("Infraction", {}).get("Approval", None)
                and Config.get("Infraction", {}).get("Approval", {}).get("channel")
                is not None
            ):
                try:
                    ApprovChannel = await interaction.client.fetch_channel(
                        int(
                            Config.get("Infraction", {})
                            .get("Approval", {})
                            .get("channel")
                        )
                    )
                except (discord.Forbidden, discord.NotFound):
                    await interaction.followup.send(
                        embed=ChannelNotFound(), ephemeral=True
                    )
                    continue
                if not ApprovChannel:
                    await interaction.followup.send(
                        embed=ChannelNotFound(), ephemeral=True
                    )
                    continue
                interaction.client.dispatch(
                    "infraction_approval", InfractionResult.inserted_id, Config
                )
                await interaction.followup.send(
                    f"{tick} **{interaction.user.display_name},** sent infraction to approval.",
                    ephemeral=True,
                )
                continue

            interaction.client.dispatch(
                "infraction", InfractionResult.inserted_id, Config, TypeActions
            )

            if escalated:
                await interaction.client.db["infractions"].update_many(
                    {
                        "guild_id": interaction.guild.id,
                        "staff": user.id,
                        "action": Org,
                        "Upscaled": {"$exists": False},
                    },
                    {"$set": {"Upscaled": True}},
                )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(activityauto(client))
