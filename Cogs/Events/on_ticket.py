import discord
from discord.ext import commands, tasks
import os
from bson import ObjectId
from utils.emojis import *
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from utils.erm import voidShift
from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed
import datetime
import asyncio
from utils.format import strtotime

logger = logging.getLogger(__name__)

# MONGO_URL = os.getenv("MONGO_URL")
# client = AsyncIOMotorClient(MONGO_URL)
# db = client["astro"]
# Transcripts = db["Transcripts"]
# Panel = db["Panels"]
# interaction.client.db['Tickets'] = db["Tickets"]


async def TicketPermissions(interaction: discord.Interaction):
    t = await interaction.client.db['Tickets'].find_one({"ChannelID": interaction.channel.id})
    if not t:
        return False
    P = await interaction.client.db['Panels'].find_one({"name": t.get("panel"), "guild": interaction.guild.id})
    if not P:
        return False
    if not P.get("permissions"):
        return False
    for role in P.get("permissions"):
        if role in [r.id for r in interaction.user.roles]:
            return True


async def DefaultEmbed(Member: discord.Member, Ticket: dict) -> discord.Embed:

    embed = (
        discord.Embed(
            description="Welcome to Support! Please include information about your issue and a staff member will be with you shortly.",
            color=discord.Color.dark_embed(),
        )
        .add_field(
            name="` 👤 ` User Info",
            value=f"{replytop} `User:` {Member.mention} (`{Member.id}`)\n {replymiddle} `Created:` <t:{int(Member.created_at.timestamp())}:R>\n {replybottom} `Joined:` <t:{int(Member.joined_at.timestamp())}:R>",
        )
        .set_author(name="Support", icon_url=Member.guild.icon)
    )
    return embed


class PTicketControl(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.red,
        custom_id="PTICKET:CLOSE",
        emoji="🔒",
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not await TicketPermissions(interaction):
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name}** you don't have permission to close this ticket.",
                ephemeral=True,
            )

        Result = await interaction.client.db['Tickets'].find_one({"MessageID": int(interaction.message.id)})
        if not Result:
            return await interaction.followup.send(
                "This isn't a ticket channel.", ephemeral=True
            )
        interaction.client.dispatch(
            "pticket_close", Result.get("_id"), "No reason provided", interaction.user
        )

    @discord.ui.button(
        label="Claim",
        style=discord.ButtonStyle.green,
        custom_id="PTICKET:CLAIM",
        emoji="✋",
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not await TicketPermissions(interaction):
            return await interaction.followup.send(
                f"{no} **{interaction.user.display_name}** you don't have permission to close this ticket.",
                ephemeral=True,
            )
        Result = await interaction.client.db['Tickets'].find_one({"MessageID": int(interaction.message.id)})
        if not Result:
            return await interaction.followup.send(
                "This isn't a ticket channel.", ephemeral=True
            )
        if Result.get("claimed").get("claimer"):
            return await interaction.followup.send(
                "This ticket is already claimed.", ephemeral=True
            )
        await interaction.client.db['Tickets'].update_one(
            {"ChannelID": interaction.channel.id},
            {
                "$set": {
                    "claimed": {
                        "claimer": interaction.user.id,
                        "claimedAt": datetime.datetime.now(),
                    }
                }
            },
        )
        embed = discord.Embed(
            color=discord.Color.green(),
            title="Ticket Claimed",
            description=f"This ticket has been claimed by {interaction.user.mention}!",
        ).set_author(
            name=interaction.user.display_name, icon_url=interaction.user.display_avatar
        )
        view = PTicketControl()
        view.claim.disabled = True
        view.claim.label = f"Claimed by @{interaction.user.name}"
        await interaction.followup.send(embed=embed)
        await interaction.edit_original_response(view=view)
        try:
         await interaction.channel.edit(name=f"claimed-{interaction.channel.name.split('-')[1]}")
        except discord.Forbidden:
            return logging.critical(
                f"[on_pticket_claim] Bot does not have permission to edit the channel {interaction.channel.id}"
            )


class TicketsPublic(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.AutomAtions.start()

    @tasks.loop(seconds=360)
    async def AutomAtions(self):
        Tickets = await self.client.db['Tickets'].find({"closed": None}).to_list(length=None)
        async def SendAutoMation(Ticket, semaphore):
            async with semaphore:
                await asyncio.sleep(0.4)
                Guild = self.client.get_guild(Ticket.get("GuildID"))
                if not Guild:
                    return 
                Channel = Guild.get_channel(Ticket.get("ChannelID"))

                if not Channel:
                    return 
                P = await self.client.db['Panels'].find_one({"name": Ticket.get("panel"), "guild": Guild.id})
                if not P:
                    return
                if not P.get("Automations"):
                    return
                ActivityReminder = P.get("Automations", {}).get("Inactivity", {})
                if not ActivityReminder:
                    return

                LastMessagSent = Ticket.get("lastMessageSent", None)
                if not Ticket.get('automations', True):
                    return
                if not LastMessagSent or datetime.datetime.utcnow() - LastMessagSent > datetime.timedelta(minutes=ActivityReminder):
                    await self.client.db['Tickets'].update_one(
                        {"_id": Ticket.get("_id")},
                        {"$set": {"lastMessageSent": datetime.datetime.utcnow()}},
                    )
                    try:
                        await Channel.send(
                            embed=discord.Embed(
                                title="⏰️ Activity Reminder",
                                description="It's been a while since we've heard from you. If you still need assistance, please respond to this message.",
                                color=discord.Color.dark_embed()
                            ),
                            content=f"<@{Ticket.get('UserID')}>"
                        )
                        
                    except discord.Forbidden:
                        return logging.critical(
                            f"[AutomAtions] Bot does not have permission to send messages in the channel {Channel.id}"
                        )
                    
        semaphore = asyncio.Semaphore(5)
        await asyncio.gather(*[SendAutoMation(Ticket, semaphore) for Ticket in Tickets])
                
                
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        Ticket = await self.client.db['Tickets'].find_one({"ChannelID": message.channel.id})
        if not Ticket:
            return
        if not int(Ticket.get("UserID")) == int(message.author.id):
            return
        await self.client.db['Tickets'].update_one(
            {"ChannelID": message.channel.id},
            {"$set": {"lastMessageSent": datetime.datetime.utcnow()}},
        )

    @commands.Cog.listener()
    async def on_pticket_claim(self, objectID: ObjectId, member: discord.Member):
        Result = await self.client.db['Tickets'].find_one({"_id": objectID})
        if not Result:
            return logging.critical(f"[TICKETS] Ticket with ID {objectID} not found")
        Channel = await self.client.fetch_channel(Result.get("ChannelID"))
        if not Channel:
            return logging.critical(
                f"[TICKETS] Channel with ID {Result.get('ChannelID')} not found"
            )
        Message = await Channel.fetch_message(Result.get("MessageID"))

        if not Message:
            return logging.critical(
                f"[TICKETS] Message with ID {Result.get('MessageID')} not found"
            )
        view = PTicketControl()
        view.claim.disabled = True
        view.claim.label = f"Claimed by @{member.name}"
        try:
            await Message.edit(view=view)
        except discord.Forbidden:
            return logging.critical(
                f"[on_pticket_claim] Bot does not have permission to edit the message {Message.id}"
            )
        try:
            await Channel.edit(
                name=f"claimed-{Channel.name.split('-')[1]}",
            )
        except discord.Forbidden:
            return logging.critical(
                f"[on_pticket_claim] Bot does not have permission to edit the channel {Channel.id}"
            )

    @commands.Cog.listener()
    async def on_unclaim(self, objectID: ObjectId):
        Result = await self.client.db['Tickets'].find_one({"_id": objectID})
        if not Result:
            return logging.critical(f"[TICKETS] Ticket with ID {objectID} not found")
        Channel = await self.client.fetch_channel(Result.get("ChannelID"))
        if not Channel:
            return logging.critical(
                f"[TICKETS] Channel with ID {Result.get('ChannelID')} not found"
            )
        Message = await Channel.fetch_message(Result.get("MessageID"))
        if not Message:
            return logging.critical(
                f"[TICKETS] Message with ID {Result.get('MessageID')} not found"
            )
        view = PTicketControl()
        view.claim.disabled = False
        view.claim.label = "Claim"
        try:
            await Message.edit(view=view)
        except discord.Forbidden:
            return logging.critical(
                f"[on_unclaim] Bot does not have permission to edit the message {Message.id}"
            )
        try:
            await Channel.edit(
                name=f"ticket-{Channel.name.split('-')[1]}",
            )
        except discord.Forbidden:
            return logging.critical(
                f"[on_unclaim] Bot does not have permission to edit the channel {Channel.id}"
            )

    @commands.Cog.listener()
    async def on_pticket_open(self, objectID: ObjectId, Panelled: str):
        Ticket = await self.client.db['Tickets'].find_one({"_id": objectID})
        if not Ticket:
            return logging.critical("[on_pticket_open] I can't find the ticket.")

        P = await self.client.db['Panels'].find_one({"name": Panelled, "type": "single", "guild": Ticket.get("GuildID")})
        if not P:
            return logging.critical("[on_pticket_open] I can't find the panel.")
        guild_id = Ticket.get("GuildID")
        guild = await self.client.fetch_guild(guild_id)
        if not guild:
            return logging.critical(
                f"[on_pticket_open] I can't find the server with ID {guild_id}."
            )

        author_id = Ticket.get("UserID", {})
        author = await guild.fetch_member(author_id)
        if not author:
            return logging.critical(
                f"[on_pticket_open] can't find the author with ID {author_id}."
            )

        welcome_message = P.get("Welcome Message")
        replacements = {
            "{author.mention}": author.mention,
            "{author.name}": author.name,
            "{time.relative}": f"<t:{int(datetime.datetime.utcnow().timestamp())}:R>",
            "{time.absolute}": f"<t:{int(datetime.datetime.utcnow().timestamp())}:F>",
            "{ticket.id}": str(Ticket.get("_id")),
        }
        Embed = (
            await DisplayEmbed(welcome_message, replacements=replacements)
            if welcome_message
            else await DefaultEmbed(author, Ticket)
        )

        if not Embed:
            Embed = await DefaultEmbed(author, Ticket)
        logging.debug(f"[on_pticket_open] Data: {P}")

        CategoryID = P.get("Category")
        if not CategoryID:
            return logging.critical("[on_pticket_open] can't find the category ID.")

        category = await guild.fetch_channel(CategoryID)
        if not category:
            return logging.critical(
                f"[on_pticket_open] can't find the category with ID {CategoryID}."
            )

        if not isinstance(category, discord.CategoryChannel):
            return logging.critical(
                f"[on_pticket_open] The fetched channel with ID {CategoryID} is not a valid category."
            )

        if category.guild is None:
            return logging.critical(
                f"[on_pticket_open] The category with ID {CategoryID} does not belong to a valid guild."
            )
        cli = await guild.fetch_member(self.client.user.id)
        if cli is None or not category.permissions_for(cli).manage_channels:
            return logging.critical(
                f"[on_pticket_open] Bot does not have permission to manage channels in the category {CategoryID}."
            )
        Roles = [guild.get_role(role_id) for role_id in P.get("permissions", [])]
        Roles = [role for role in Roles if role]
        Overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            author: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            cli: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }

        for role in Roles:
            Overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)
        try:
            channel = await category.create_text_channel(
                name=f"ticket-{author.name}", overwrites=Overwrites
            )
        except discord.Forbidden as e:
            return logging.critical(
                f"[on_pticket_open] The bot does not have permission to create a text channel: {e}"
            )
        except Exception as e:
            return logging.critical(
                f"[on_pticket_open] Failed to create text channel: {e}"
            )

        Mentions = P.get("MentionsOnOpen", [])
        Mentions = [
            guild.get_role(role_id).mention
            for role_id in Mentions
            if guild.get_role(role_id)
        ]
        Mentions.append(author.mention)
        try:
            msg = await channel.send(
                embed=Embed,
                content=" ".join(Mentions),
                allowed_mentions=discord.AllowedMentions(roles=True, users=True),
                view=PTicketControl(),
            )
        except discord.Forbidden:
            return logging.critical(
                f"[on_pticket_open] Bot does not have permission to send messages in the channel {channel.id}"
            )
        await self.client.db['Tickets'].update_one(
            {"_id": objectID}, {"$set": {"ChannelID": channel.id, "MessageID": msg.id}}
        )

    @commands.Cog.listener()
    async def on_pticket_close(
        self, ObjectID: ObjectId, reason: str, member: discord.Member
    ):
        Result = await self.client.db['Tickets'].find_one({"_id": ObjectID})
        if not Result:
            return logging.critical(f"[TICKETS] Ticket with ID {ObjectID} not found")

        Guild = self.client.get_guild(Result.get("GuildID"))
        if not Guild:
            return logging.critical(
                f"[TICKETS] Guild with ID {Result.get('GuildID')} not found"
            )

        Channel = Guild.get_channel(Result.get("ChannelID"))
        if not Channel:
            return logging.critical(
                f"[TICKETS] Channel with ID {Result.get('ChannelID')} not found"
            )
        try:
            user = await Guild.fetch_member(Result.get("UserID"))
        except (discord.NotFound, discord.HTTPException):
            user = None
        await Channel.send(f"<a:Loading:1167074303905386587> Ticket closing...")
        messages = []
        compact = []
        async for message in Channel.history(limit=None):
            messages.append(
                f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author.name}: {message.content}"
            )
            compact.append(
                {
                    "author_id": message.author.id,
                    "content": message.content,
                    "author_name": message.author.name,
                    "message_id": message.id,
                    "author_avatar": str(message.author.avatar.url if message.author.avatar else ""),
                    "attachments": [
                        attachment.url for attachment in message.attachments
                    ],
                    "embeds": [embed.to_dict() for embed in message.embeds],
                    "timestamp": message.created_at.timestamp(),
                }
            )
        await self.client.db['Tickets'].update_one(
            {"_id": ObjectID},
            {
                "$push": {"transcript": {"messages": messages, "compact": compact}},
                "$set": {
                    "closed": datetime.datetime.utcnow(),
                    "closed": {
                        "reason": reason,
                        "closer": member.id,
                        "closedAt": datetime.datetime.now(),
                    },
                },
            },
        )
        P = await self.client.db['Panels'].find_one({"name": Result.get("panel"), "guild": Guild.id})
        if not P:
            return logging.critical("[on_pticket_close] I can't find the panel.")
        try:
            await self.client.db['Ticket Quota'].update_one(
                {"GuildID": Guild.id, "UserID": Result.get('claimed', {}).get('claimer')},
                {"$inc": {"ClaimedTickets": 1}},
                upsert=True
            )
        except:
            pass
        if P.get("TranscriptChannel"):
            TranscriptChannel = Guild.get_channel(P.get("TranscriptChannel"))
            if TranscriptChannel:
                embed = discord.Embed(
                    title="Ticket Closed",
                    color=discord.Color.dark_embed(),
                )
                embed.set_author(name=Guild.name, icon_url=Guild.icon.url)
                embed.add_field(name="ID", value=Result.get("_id"), inline=True)
                embed.add_field(
                    name="Opened By", value=f"<@{Result.get('UserID')}>", inline=True
                )
                embed.add_field(name="Closed By", value=member.mention, inline=True)
                embed.add_field(
                    name="Time Created",
                    value=f"<t:{int(Result.get('opened'))}:R>",
                    inline=True,
                )
                embed.add_field(name="Reason", value=reason, inline=True)
                embed.add_field(name="Channel", value=Channel.name)

                ButtonLink = discord.ui.View()
                ButtonLink.add_item(
                    discord.ui.Button(
                        label="View Transcript",
                        url=f"https://astrobirb.dev/transcript/{Result.get('_id')}",
                        emoji="<:Website:1132252914082127882>",
                        style=discord.ButtonStyle.blurple,
                    )
                )
                if user:
                    await user.send(embed=embed)
                try:
                    await TranscriptChannel.send(embed=embed, view=ButtonLink)
                except discord.Forbidden:
                    pass
        try:
            await Channel.delete()
        except discord.Forbidden:
            return logging.critical(
                f"[on_pticket_close] Bot does not have permission to delete the channel {Channel.id}"
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(TicketsPublic(client))
