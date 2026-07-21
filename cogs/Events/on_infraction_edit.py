import logging

import discord
from discord.ext import commands

from cogs.Events.on_infraction import DefaultEmbed
from core.bot.CustomEmbed import DisplayEmbed
from core.bot.Variables import Variables
from datamodels.Infractions import InfractionItem

logger = logging.getLogger(__name__)


class on_infraction_edit(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_infraction_edit(self, after: dict):
        InfractionData = await self.client.db["infractions"].find_one(
            {"_id": after.get("_id")}
        )
        Infraction = InfractionItem(**InfractionData)
        guild = await self.client.fetch_guild(Infraction.guild_id)
        if guild is None:
            logging.warning(
                f"[🏠 on_infraction_edit] {Infraction.guild_id} is None and can't be found..?"
            )
            return

        try:
            staff = await guild.fetch_member(int(Infraction.staff))
        except:
            staff = None
        if staff is None:
            logging.warning(
                f"[🏠 on_infraction_edit] @{guild.name} staff member {Infraction.staff} can't be found."
            )
            return

        try:
            manager = await guild.fetch_member(int(Infraction.management))
        except:
            manager = None
        if manager is None:
            logging.warning(
                f"[🏠 on_infraction_edit] @{guild.name} manager {Infraction.management} can't be found."
            )
            return

        Settings = await self.client.config.find_one({"_id": Infraction.guild_id})
        ChannelID = Settings.get("Infraction", {}).get("channel")
        if not ChannelID:
            logging.warning(
                f"[🏠 on_infraction_edit] @{guild.name} no channel ID found in settings."
            )
            return
        try:
            channel = await guild.fetch_channel(int(ChannelID))
        except Exception as e:
            logger.error(
                f"[🏠 on_infraction_edit] @{guild.name} the infraction channel can't be found. [1]"
            )
            return
        if channel is None:
            logging.warning(
                f"[🏠 on_infraction_edit] @{guild.name} the infraction channel can't be found. [2]"
            )
            return

        custom = await self.client.db["Customisation"].find_one(
            {
                "guild_id": Infraction.guild_id,
                "type": "Infractions",
            }
        )
        if custom:
            replacements = await Variables.infraction(
                staff=staff, Infraction=Infraction, manager=manager, guild=guild
            )
            embed = await DisplayEmbed(
                data=custom, user=staff, replacements=replacements
            )
        else:
            embed = DefaultEmbed(InfractionData, staff, manager)
        embed.set_footer(text=f"Infraction ID | {Infraction.random_string}")

        try:
            if Infraction.webhook_id:
                webhook = await self.client.fetch_webhook(Infraction.webhook_id)
                msg = await webhook.fetch_message(Infraction.msg_id)
            else:
                msg = await channel.fetch_message(Infraction.msg_id)

            await msg.edit(embed=embed)
            logger.info(
                f"[✅] Updated infraction message with ID: {Infraction.random_string}"
            )
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_infraction_edit(client))
