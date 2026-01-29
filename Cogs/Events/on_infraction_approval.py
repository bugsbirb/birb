import discord
from discord.ext import commands
from bson import ObjectId

import logging
from Cogs.Events.on_infraction import InfractItem
from utils.emojis import *

logger = logging.getLogger(__name__)

async def CaseEmbed(data: str, staff: discord.Member, guild: discord.Guild):
    embed = discord.Embed(
        color=discord.Color.dark_embed(), timestamp=discord.utils.utcnow()
    )
    Roles = ", ".join(
        [role.mention for role in reversed(staff.roles) if role != guild.default_role][
            :20
        ]
    )
    embed.set_author(name=f"Infraction Case | #{data.get('random_string')}")
    value = f"> **User:** <@{data.get('staff')}> (`{data.get('staff')}`)\n> **Roles:** {Roles}"[
        :1024
    ]
    embed.add_field(
        name="User Information",
        value=value,
        inline=False,
    )
    embed.add_field(
        name="Case Information",
        value=f"> **Manager:** <@{data.get('management')}>\n> **Action:** {data.get('action')}\n> **Reason:** {data.get('reason')}\n",
        inline=False,
    )

    embed.set_thumbnail(url=staff.display_avatar)
    embed.set_footer(
        text="Case",
        icon_url=staff.display_avatar,
    )
    return embed


class on_infraction_approval(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_infraction_approval(self, objectid: ObjectId, Settings: dict):
        InfractionData = await self.client.db['infractions'].find_one({"_id": objectid})
        if not InfractionData:
            return
        Infraction = InfractItem(InfractionData)

        guild = await self.client.fetch_guild(Infraction.guild_id)
        if guild is None:
            logging.warning(
                f"[🏠 on_infraction] {Infraction.guild_id} is None and can't be found..?"
            )
            return

        try:
            staff = await guild.fetch_member(int(Infraction.staff))
        except:
            staff = None
        if staff is None:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} staff member {Infraction.staff} can't be found."
            )
            return
        try:
            manager = await guild.fetch_member(int(Infraction.management))
        except:
            manager = None
        if manager is None:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} manager {Infraction.management} can't be found."
            )
            return
        ChannelID = Settings.get("Infraction", {}).get("Approval", {}).get("channel")
        if not ChannelID:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} no channel ID found in settings."
            )
            return
        try:
            channel = await guild.fetch_channel(int(ChannelID))
        except Exception as e:
            logger.error(
                f"[🏠 on_infraction] @{guild.name} the infraction channel can't be found. [1]"
            )
            return
        if channel is None:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} the infraction channel can't be found. [2]"
            )
            return
        embed = await CaseEmbed(InfractionData, staff, guild)
        if not embed:
            logger.warning("[on_infraction_approval] couldn't send embed.")
            return
        DataPing = Settings.get("Infraction", {}).get("Approval", {}).get("Ping", None)

        RolePing = f"<@&{DataPing}>" if DataPing else ""
        try:
            view = CaseApproval()
            msg = await channel.send(
                embed=embed,
                view=view,
                content=RolePing,
                allowed_mentions=discord.AllowedMentions.all(),
            )
        except (discord.Forbidden, discord.NotFound):
            logger.warning("[on_infraction_approval] couldn't send approval.")

            return
        try:
            await msg.create_thread(
                name=f"Infraction Discussion | #{Infraction.random_string}"
            )
        except (discord.Forbidden, discord.NotFound):
            logger.warning("[on_infraction_approval] couldn't set thread.")
            pass
        await self.client.db['infractions'].update_one(
            {"_id": objectid}, {"$set": {"ApprovalMSG": msg.id}}
        )


class CaseApproval(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Accept (Send)",
        style=discord.ButtonStyle.green,
        custom_id="AcceptInf:Persistent",
    )
    async def Accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        Result = await interaction.client.db['infractions'].find_one({"ApprovalMSG": interaction.message.id})
        Settings = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Result:
            return await interaction.followup.send(
                content=f"{no} **{interaction.user.display_name}**, I couldn't find the data for this."
            )
        Infraction = InfractItem(Result)

        guild = await interaction.client.fetch_guild(Infraction.guild_id)
        if guild is None:
            logging.warning(
                f"[🏠 on_infraction] {Infraction.guild_id} is None and can't be found..?"
            )
            return

        try:
            staff = await guild.fetch_member(int(Infraction.staff))
        except:
            staff = None
        if staff is None:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} staff member {Infraction.staff} can't be found."
            )
            return

        try:
            manager = await guild.fetch_member(int(Infraction.management))
        except:
            manager = None
        if manager is None:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} manager {Infraction.management} can't be found."
            )
            return
        embed: discord.Embed = await CaseEmbed(Result, staff, guild)
        embed.color = discord.Color.brand_green()
        embed.set_footer(text=f"Accepted by @{interaction.user.name}", icon_url=interaction.user.display_avatar)
        view = CaseApproval()
        view.Accept.label = "Accepted"
        view.Accept.disabled = True
        view.remove_item(view.Deny)
        await interaction.edit_original_response(embed=embed, view=view)
        await interaction.client.db['infractions'].update_one({"_id": Result.get("_id")}, {"$set": {"ApprovalStatus": False}})
        TypeActions = await interaction.client.db['infractiontypeactions'].find_one(
            {"guild_id": interaction.guild.id, "name": Infraction.action}
        )
        interaction.client.dispatch(
            "infraction", Result.get("_id"), Settings, TypeActions
        )

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.red,
        custom_id="DenyVoid:Persistent",
    )
    async def Deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        Result = await interaction.client.db['infractions'].find_one({"ApprovalMSG": interaction.message.id})
        Settings = await interaction.client.config.find_one({"_id": interaction.guild.id})
        if not Result:
            return await interaction.followup.send(
                content=f"{no} **{interaction.user.display_name}**, I couldn't find the data for this."
            )
        Infraction = InfractItem(Result)

        guild = await interaction.client.fetch_guild(Infraction.guild_id)
        if guild is None:
            logging.warning(
                f"[🏠 on_infraction] {Infraction.guild_id} is None and can't be found..?"
            )
            return

        try:
            staff = await guild.fetch_member(int(Infraction.staff))
        except:
            staff = None
        if staff is None:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} staff member {Infraction.staff} can't be found."
            )
            return

        try:
            manager = await guild.fetch_member(int(Infraction.management))
        except:
            manager = None
        if manager is None:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} manager {Infraction.management} can't be found."
            )
            return
        embed: discord.Embed = await CaseEmbed(Result, staff, guild)
        embed.set_footer(text=f"Denied by @{interaction.user.name}", icon_url=interaction.user.display_avatar)
        embed.color = discord.Color.brand_red()
        view = CaseApproval()
        view.Deny.label = "Denied"
        view.Deny.disabled = True
        view.remove_item(view.Accept)
        await interaction.edit_original_response(embed=embed, view=view)
        await interaction.client.db['infractions'].delete_one({"_id": Result.get("_id")})


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_infraction_approval(client))
