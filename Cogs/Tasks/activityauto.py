import os
import random
import string
import re

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv


from utils.format import strtotime
from utils.emojis import *
from utils.Module import ModuleCheck
from utils.permissions import *
from datetime import timedelta, datetime


load_dotenv()
environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")


class activityauto(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.quota_activity.start()

    @tasks.loop(minutes=15, reconnect=True)
    async def quota_activity(self):
        print("[INFO] Checking for quota activity")
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
        if autoactivityresult:

            for data in autoactivityresult:
                try:
                    if data.get("enabled", False) is False:
                        continue
                    if not await ModuleCheck(data.get("guild_id", 0), "Quota"):
                        continue
                    try:
                        channel = self.client.get_channel(data.get("channel_id", None))
                    except (discord.HTTPException, discord.NotFound):
                        print(
                            f"[ERROR] Channel {data.get('channel_id', None)} not found."
                        )
                        pass
                    if not channel:
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
                    nextdate = data.get("nextdate", None)
                    day = data.get("day", "").lower()
                    current_day_index = datetime.now().weekday()
                    if day not in days:
                        continue
                    Specified = days.index(day)
                    Days = (Specified - current_day_index) % 7
                    if Days == 0:
                        if datetime.now() < nextdate:
                            next_occurrence_date = datetime.now()
                        else:
                            next_occurrence_date = datetime.now() + timedelta(days=7)
                    else:
                        next_occurrence_date = datetime.now() + timedelta(days=Days)

                    if next_occurrence_date < datetime.now():
                        next_occurrence_date = datetime.now() + timedelta(days=7)

                    if not datetime.now() >= nextdate:
                        continue

                    if datetime.now() >= nextdate:

                        try:
                            guild = await self.client.fetch_guild(
                                data.get("guild_id", None)
                            )
                        except (discord.HTTPException, discord.NotFound):
                            continue
                        if not guild:
                            continue
                        await self.client.db["auto activity"].update_one(
                            {"guild_id": guild.id},
                            {
                                "$set": {
                                    "nextdate": next_occurrence_date,
                                    "lastposted": datetime.now(),
                                }
                            },
                        )

                        print(
                            f"[⏰] Sending Activity @{guild.name} next post is {next_occurrence_date}!"
                        )
                        if guild:
                            result = (
                                await self.client.qdb["auto activity"]
                                .find({"guild_id": guild.id})
                                .to_list(length=None)
                            )
                            passed = []
                            failed = []
                            on_loa = []
                            failedids = []
                            if result:
                                for data in result:
                                    OnLOA = False

                                    try:
                                        user = await guild.fetch_member(
                                            data.get("user_id", None)
                                        )
                                    except (discord.HTTPException, discord.NotFound):
                                        continue
                                    if not user:
                                        continue
                                    if user:
                                        if not await check_admin_and_staff(guild, user):
                                            continue
                                        result = await self.client.qdb[
                                            "messages"
                                        ].find_one(
                                            {"guild_id": guild.id, "user_id": user.id}
                                        )
                                        Config = await self.client.config.find_one(
                                            {"_id": guild.id}
                                        )
                                        if Config is None:
                                            continue
                                        if not Config.get("Message Quota"):
                                            return

                                        if not result:
                                            continue

                                        if Config.get("LOA", {}).get("role"):
                                            OnLOA = any(
                                                role.id
                                                == Config.get("LOA", {}).get("role")
                                                for role in user.roles
                                            )

                                        Quota = Config.get("Message Quota", {}).get(
                                            "quota", 0
                                        )
                                        MessageCount = result.get("message_count", 0)
                                        if OnLOA:
                                            on_loa.append(
                                                f"> **{user.name}** • `{MessageCount}` messages"
                                            )
                                            continue

                                        if int(MessageCount) >= int(Quota):
                                            passed.append(
                                                f"> **{user.name}** • `{MessageCount}` messages"
                                            )
                                        else:
                                            failed.append(
                                                f"> **{user.name}** • `{MessageCount}` messages"
                                            )
                                            failedids.append(user.id)

                            else:
                                continue
                            await self.client.AutoActivity.update_one(
                                {"guild_id": guild.id}, {"$set": {"failed": failedids}}
                            )
                            passed.sort(
                                key=lambda x: int(
                                    x.split("•")[-1].strip().split(" ")[0].strip("`")
                                ),
                                reverse=True,
                            )
                            failed.sort(
                                key=lambda x: int(
                                    x.split("•")[-1].strip().split(" ")[0].strip("`")
                                ),
                                reverse=True,
                            )
                            on_loa.sort(
                                key=lambda x: int(
                                    x.split("•")[-1].strip().split(" ")[0].strip("`")
                                ),
                                reverse=True,
                            )
                            passedembed = discord.Embed(
                                title="Passed", color=discord.Color.brand_green()
                            )
                            passedembed.set_image(
                                url="https://www.astrobirb.dev/invisble.png"
                            )
                            if passed:
                                passedembed.description = "\n".join(passed)
                            else:
                                passedembed.description = "> No users passed the quota."

                            loaembed = discord.Embed(
                                title="On LOA", color=discord.Color.purple()
                            )
                            loaembed.set_image(
                                url="https://www.astrobirb.dev/invisble.png"
                            )
                            if on_loa:
                                loaembed.description = "\n".join(on_loa)
                            else:
                                loaembed.description = "> No users on LOA."

                            failedembed = discord.Embed(
                                title="Failed", color=discord.Color.brand_red()
                            )
                            failedembed.set_image(
                                url="https://www.astrobirb.dev/invisble.png"
                            )
                            if failed:
                                failedembed.description = "\n".join(failed)
                            else:
                                failedembed.description = "> No users failed the quota."
                            if channel:
                                view = ResetLeaderboard(failedids)
                                try:
                                    await channel.send(
                                        embeds=[passedembed, loaembed, failedembed],
                                        view=view,
                                    )
                                    print(
                                        f"[Activity Auto] succesfully sent @{guild.name}"
                                    )
                                except discord.Forbidden:
                                    print("[ERROR] Channel not found")
                                    return
                            else:
                                print("[NOTFOUND] Channel not found")
                                continue
                except Exception as e:
                    print(f"[QUOTA ERROR] {e}")
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
                    f"  **{interaction.user.display_name}**, there are no failures to punish.",
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
                f"  **{interaction.user.display_name}**, the bot isn't setup you can do that in /config.",
                ephemeral=True,
            )
        if not Config.get("Infraction", None):
            return await interaction.followup.send(
                f"  **{interaction.user.display_name}**, the infraction module is not setup you can do that in /config.",
                ephemeral=True,
            )
        try:
            channel = await interaction.client.fetch_channel(
                Config.get("Infraction", {}).get("channel", None)
            )
        except (discord.NotFound, discord.HTTPException):
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** hey I can't find your infraction channel it is configured but I can't find it?",
                ephemeral=True,
            )
        if not channel:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** hey I can't find your infraction channel it is configured but I can't find it?",
                ephemeral=True,
            )
        client = await interaction.guild.fetch_member(interaction.client.user.id)
        if channel.permissions_for(client).send_messages is False:
            return await interaction.response.send_message(
                content=f"  **{interaction.user.display_name},** oi I can't send messages in the infraction channel!!",
                ephemeral=True,
            )
        if expiration and not re.match(r"^\d+[mhdws]$", expiration):
            await interaction.response.send_message(
                f"  **{interaction.user.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.",
                ephemeral=True,
            )
            return
        if expiration:
            expiration = await strtotime(expiration)
        for user in self.failures:
            user = await interaction.guild.fetch_member(user)
            if user is None:
                await interaction.followup.send(
                    f"  **{interaction.user.display_name}**, this user can not be found.",
                    ephemeral=True,
                )
                return

            random_string = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )

            InfractionResult = await self.client.db["infractions"].insert_one(
                {
                    "guild_id": interaction.guild.id,
                    "staff": user.id,
                    "management": interaction.user.id,
                    "action": action,
                    "reason": reason,
                    "notes": notes,
                    "expiration": expiration,
                    "random_string": random_string,
                    "annonymous": anonymous,
                    "timestamp": datetime.now(),
                }
            )
            if not InfractionResult.inserted_id:
                await interaction.response.send_message(
                    content=f"  **{interaction.user.display_name},** hi I had a issue submitting this infraction please head to support!",
                    ephemeral=True,
                )
                return
            interaction.client.dispatch(
                "infraction", InfractionResult.inserted_id, Config, TypeActions
            )
        view = ResetLeaderboard()
        view.punishfailures.label = "Punished"
        view.punishfailures.style = discord.ButtonStyle.success
        view.punishfailures.emoji =  None
        view.punishfailures.disabled = True
        await interaction.edit_original_response(view=view)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(activityauto(client))
