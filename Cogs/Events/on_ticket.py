import discord
from discord.ext import commands, tasks
import os
from bson import ObjectId
from utils.emojis import *

import logging
from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed
import datetime
from utils.format import Replace
import asyncio
from utils.r2 import upload_file_to_r2, ClearOldFiles


async def TicketPermissions(interaction: discord.Interaction):
    t = await interaction.client.db["Tickets"].find_one(
        {"ChannelID": interaction.channel.id}
    )
    if not t:
        return False
    P = await interaction.client.db["Panels"].find_one(
        {"name": t.get("panel"), "guild": interaction.guild.id, "type": "single"}
    )
    if not P:
        return False
    if not P.get("permissions"):
        return False
    if any(role.id in P.get("permissions") for role in interaction.user.roles):
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

        Result = await interaction.client.db["Tickets"].find_one(
            {"MessageID": int(interaction.message.id)}
        )
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
        Result = await interaction.client.db["Tickets"].find_one(
            {"MessageID": int(interaction.message.id)}
        )
        Panel = await interaction.client.db["Panels"].find_one(
            {
                "name": Result.get("panel"),
                "guild": interaction.guild.id,
                "type": "single",
            }
        )
        if not Result:
            return await interaction.followup.send(
                "This isn't a ticket channel.", ephemeral=True
            )
        if Result.get("claimed").get("claimer"):
            return await interaction.followup.send(
                "This ticket is already claimed.", ephemeral=True
            )
        await interaction.client.db["Tickets"].update_one(
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
        name = f"claimed-{interaction.channel.name.split('-')[1]}"
        if Panel.get("TicketNames", {}).get("Claimed", None):
            replacements = {
                "{author.name}": interaction.user.name,
                "{author.id}": str(interaction.user.id),
                "{user.id}": str(Result.get("UserID")),
            }
            try:
                name = Replace(
                    Panel.get("TicketNames").get("Claimed"),
                    replacements=replacements,
                )
            except Exception as e:
                name = f"claimed-{interaction.channel.name.split('-')[1]}"

        try:
            await interaction.channel.edit(
                name=name,
            )
        except discord.Forbidden:
            return logging.critical(
                f"[on_pticket_claim] Bot does not have permission to edit the channel {interaction.channel.id}"
            )


class TicketsPublic(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.AutomAtions.start()
        self.ClearOld.start()

    @tasks.loop(seconds=360)
    async def AutomAtions(self):
        Filter = {"closed": None}
        if os.getenv("ENVIRONMENT") == "custom":
            Filter["GuildID"] = int(os.getenv("CUSTOM_GUILD"))
        Tickets = await self.client.db["Tickets"].find(Filter).to_list(length=None)

        async def SendAutoMation(Ticket, semaphore):
            async with semaphore:
                await asyncio.sleep(0.4)
                if Ticket.get("lastMessenger") == int(self.client.user.id):
                    return
                Guild = self.client.get_guild(Ticket.get("GuildID"))
                if not Guild:
                    return
                Channel = Guild.get_channel(Ticket.get("ChannelID"))
                if not Channel:
                    return
                P = await self.client.db["Panels"].find_one(
                    {"name": Ticket.get("panel"), "guild": Guild.id}
                )
                if not P:
                    return
                if not P.get("Automations"):
                    return
                ActivityReminder = P.get("Automations", {}).get("Inactivity", {})
                if not ActivityReminder:
                    return

                if Ticket.get("LastMessageWasBot", False) is True:
                    return

                LastMessagSent = Ticket.get("lastMessageSent", None)
                if not Ticket.get("automations", True):
                    return
                if (
                    not LastMessagSent
                    or datetime.datetime.utcnow() - LastMessagSent
                    > datetime.timedelta(minutes=ActivityReminder)
                ):
                    await self.client.db["Tickets"].update_one(
                        {"_id": Ticket.get("_id")},
                        {
                            "$set": {
                                "lastMessageSent": datetime.datetime.utcnow(),
                                "LastMessageWasBot": True,
                            }
                        },
                    )
                    try:
                        await Channel.send(
                            embed=discord.Embed(
                                title="⏰️ Activity Reminder",
                                description="It's been a while since we've heard from you. If you still need assistance, please respond to this message.",
                                color=discord.Color.dark_embed(),
                            ),
                            content=f"<@{Ticket.get('UserID')}>",
                        )

                    except discord.Forbidden:
                        return logging.critical(
                            f"[AutomAtions] Bot does not have permission to send messages in the channel {Channel.id}"
                        )

        semaphore = asyncio.Semaphore(5)
        await asyncio.gather(*[SendAutoMation(Ticket, semaphore) for Ticket in Tickets])

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        Ticket = await self.client.db["Tickets"].find_one(
            {"ChannelID": message.channel.id}
        )
        if not Ticket:
            return
        if not int(Ticket.get("UserID")) == int(message.author.id):
            return
        await self.client.db["Tickets"].update_one(
            {"ChannelID": message.channel.id},
            {
                "$set": {
                    "lastMessageSent": datetime.datetime.utcnow(),
                    "lastMessenger": message.author.id,
                    "LastMessageWasBot": False,
                }
            },
        )

    @commands.Cog.listener()
    async def on_pticket_review(
        self, objectID: ObjectId, rating: int, member: discord.Member
    ):
        Result = await self.client.db["Tickets"].find_one({"_id": objectID})
        if not Result:
            return logging.critical(f"[TICKETS] Ticket with ID {objectID} not found")
        Guild = self.client.get_guild(Result.get("GuildID"))
        if not Guild:
            return logging.critical(
                f"[TICKETS] Guild with ID {Result.get('GuildID')} not found"
            )
        Channel = Guild.get_channel(Result.get("ReviewChannel"))
        if not Channel:
            return logging.critical(
                f"[TICKETS] Channel with ID {Result.get('ReviewChannel')} not found"
            )
        Message = await Channel.fetch_message(Result.get("ReviewMSG"))
        if not Message:
            return logging.critical(
                f"[TICKETS] Message with ID {Result.get('ReviewMSG')} not found"
            )
        embed = Message.embeds[0]
        embed.add_field(
            name="Rating",
            value=f"` ⭐ ` {rating}\n` 💬 ` {Result.get('review', 'N/A')}",
            inline=False,
        )
        try:
            await Message.edit(embed=embed)
        except discord.Forbidden:
            return logging.critical(
                f"[on_pticket_review] Bot does not have permission to edit the message {Message.id}"
            )

    @commands.Cog.listener()
    async def on_pticket_claim(self, objectID: ObjectId, member: discord.Member):
        Result = await self.client.db["Tickets"].find_one({"_id": objectID})
        if not Result:
            return logging.critical(f"[TICKETS] Ticket with ID {objectID} not found")

        Panel = await self.client.db["Panels"].find_one(
            {"name": Result.get("panel"), "guild": int(Result.get("GuildID"))}
        )
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
        name = f"claimed-{Channel.name.split('-')[1]}"
        if Panel.get("TicketNames", {}).get("Claimed", None):
            replacements = {
                "{author.name}": member.name,
                "{author.id}": str(member.id),
                "{user.name}": member.name,
                "{user.id}": str(member.id),
            }
            try:
                name = Replace(
                    Panel.get("TicketNames").get("Claimed"),
                    replacements=replacements,
                )
            except Exception as e:
                name = f"claimed-{Channel.name.split('-')[1]}"

        try:
            await Channel.edit(
                name=name,
            )
        except discord.Forbidden:
            return logging.critical(
                f"[on_pticket_claim] Bot does not have permission to edit the channel {Channel.id}"
            )

    @tasks.loop(hours=12)
    async def ClearOld(self):
        if not (
            os.getenv("R2_URL")
            and os.getenv("ACCESS_KEY_ID")
            and os.getenv("SECRET_ACCESS_KEY")
            and os.getenv("BUCKET")
        ):
            return
        if os.getenv("ENVIRONMENT") in ["development", "custom"] and (
            not os.getenv("VIDEO_DAYS") or not os.getenv("IMAGE_DAYS")
        ):
            return
        await ClearOldFiles()

    @commands.Cog.listener()
    async def on_unclaim(self, objectID: ObjectId):
        Result = await self.client.db["Tickets"].find_one({"_id": objectID})
        if not Result:
            return logging.critical(f"[TICKETS] Ticket with ID {objectID} not found")
        P = await self.client.db["Panels"].find_one(
            {
                "name": Result.get("panel"),
                "type": "single",
                "guild": Result.get("GuildID"),
            }
        )
        if not P:
            return logging.critical(f"[Tickets] panel is not found.")
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
        try:
            author = await self.client.fetch_user(Result.get("UserID"))
        except (discord.HTTPException, discord.NotFound):
            return logging.critical(f"[TICKETS] Authors account is not found")
        if not author:
            return
        view = PTicketControl()
        view.claim.disabled = False
        view.claim.label = "Claim"
        try:
            await Message.edit(view=view)
        except discord.Forbidden:
            return logging.critical(
                f"[on_unclaim] Bot does not have permission to edit the message {Message.id}"
            )
        name = f"ticket-{author.name}"
        if P.get("TicketNames", {}).get("Open", None):
            replacements = {
                "{author.name}": author.name,
                "{author.id}": str(author.id),
                "{user.name}": author.name,
                "{user.id}": str(author.id),
            }
            try:
                name = Replace(
                    P.get("TicketNames").get("Open"),
                    replacements=replacements,
                )
            except Exception as e:
                name = f"ticket-{author.name}"

        try:
            await Channel.edit(
                name=name,
            )
        except discord.Forbidden:
            return logging.critical(
                f"[on_unclaim] Bot does not have permission to edit the channel {Channel.id}"
            )

    @commands.Cog.listener()
    async def on_pticket_open(self, objectID: ObjectId, Panelled: str):
        Ticket = await self.client.db["Tickets"].find_one({"_id": objectID})
        if not Ticket:
            return logging.critical("[on_pticket_open] I can't find the ticket.")

        P = await self.client.db["Panels"].find_one(
            {"name": Panelled, "type": "single", "guild": Ticket.get("GuildID")}
        )
        if not P:
            await self.client.db["Tickets"].update_one(
                {"_id": objectID}, {"$set": {"error.message": "Panel not found."}}
            )
            return logging.critical("[on_pticket_open] I can't find the panel.")
        guild_id = Ticket.get("GuildID")
        guild = await self.client.fetch_guild(guild_id)
        if not guild:
            await self.client.db["Tickets"].update_one(
                {"_id": objectID}, {"$set": {"error.message": "Guild not found."}}
            )
            return logging.critical(
                f"[on_pticket_open] I can't find the server with ID {guild_id}."
            )

        author_id = Ticket.get("UserID", {})
        author = await guild.fetch_member(author_id)
        if not author:
            await self.client.db["Tickets"].update_one(
                {"_id": objectID}, {"$set": {"error.message": "Author not found."}}
            )
            return logging.critical(
                f"[on_pticket_open] can't find the author with ID {author_id}."
            )

        welcome_message = P.get("Welcome Message")
        replacements = {
            "{author.mention}": author.mention,
            "{author.name}": author.name,
            "{author.created_at.relative}": f"<t:{int(author.created_at.timestamp())}:R>",
            "{author.created_at.absolute}": f"<t:{int(author.created_at.timestamp())}:F>",
            "{author.joined_at.relative}": f"<t:{int(author.joined_at.timestamp())}:R>",
            "{author.joined_at.absolute}": f"<t:{int(author.joined_at.timestamp())}:F>",
            "{author.id}": str(author.id),
            "{author.avatar}": str(author.avatar.url) if author.avatar else "",
            "{author.display_name}": author.display_name,
            "{guild.name}": guild.name,
            "{guild.id}": str(guild.id),
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
        CategoryID = P.get("Category")
        if not CategoryID:
            await self.client.db["Tickets"].update_one(
                {"_id": objectID},
                {
                    "$set": {
                        "error.message": "The category isn't setup. Make sure to set the category in config."
                    }
                },
            )
            return logging.critical("[on_pticket_open] can't find the category ID.")
        try:
            category = await guild.fetch_channel(CategoryID)
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            await self.client.db["Tickets"].update_one(
                {"_id": objectID},
                {
                    "$set": {
                        "error.message": "The bot can't find the category. Make sure to give the bot permission to view the category."
                    }
                },
            )
            return logging.critical(
                f"[on_pticket_open] can't find the category with ID {CategoryID}."
            )
        if not category:
            await self.client.db["Tickets"].update_one(
                {"_id": objectID}, {"$set": {"error.message": "Category not found."}}
            )
            return logging.critical(
                f"[on_pticket_open] can't find the category with ID {CategoryID}."
            )

        if not isinstance(category, discord.CategoryChannel):
            await self.client.db["Tickets"].update_one(
                {"_id": objectID}, {"$set": {"error.message": "Category not found."}}
            )
            return logging.critical(
                f"[on_pticket_open] The fetched channel with ID {CategoryID} is not a valid category."
            )

        if category.guild is None:
            await self.client.db["Tickets"].update_one(
                {"_id": objectID},
                {
                    "$set": {
                        "error.message": f"The category with the ID {CategoryID} does not belong to a valid guild."
                    }
                },
            )
            return logging.critical(
                f"[on_pticket_open] The category with ID {CategoryID} does not belong to a valid guild."
            )
        cli = await guild.fetch_member(self.client.user.id)
        if cli is None or not category.permissions_for(cli).manage_channels:
            await self.client.db["Tickets"].update_one(
                {"_id": objectID},
                {
                    "$set": {
                        "error.message": "Bot does not have permission to manage channels in the category."
                    }
                },
            )
            return logging.critical(
                f"[on_pticket_open] Bot does not have permission to manage channels in the category {CategoryID}."
            )
        Roles = [guild.get_role(role_id) for role_id in P.get("permissions", [])]
        Roles = [role for role in Roles if role]
        Overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            author: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, read_message_history=True
            ),
            cli: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, read_message_history=True
            ),
        }

        for role in Roles:
            Overwrites[role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True, read_message_history=True
            )
        name = f"ticket-{author.name}"
        if P.get("TicketNames", {}).get("Open", None):
            replacements = {
                "{author.name}": author.name,
                "{author.id}": str(author.id),
                "{user.name}": author.name,
                "{user.id}": str(author.id),
            }
            try:
                name = Replace(
                    P.get("TicketNames").get("Open"),
                    replacements=replacements,
                )
            except Exception as e:
                name = f"claimed-{channel.name.split('-')[1]}"
        try:
            channel = await category.create_text_channel(
                name=name, overwrites=Overwrites
            )
        except discord.Forbidden as e:
            await self.client.db["Tickets"].update_one(
                {"_id": objectID},
                {
                    "$set": {
                        "error.message": f"Bot does not have permission to create a text channel: {e}"
                    }
                },
            )
            return logging.critical(
                f"[on_pticket_open] The bot does not have permission to create a text channel: {e}"
            )
        except Exception as e:
            await self.client.db["Tickets"].update_one(
                {"_id": objectID},
                {"$set": {"error.message": f"Failed to create text channel: {e}"}},
            )
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

        ResponseEmbed = None
        if Ticket.get("responses"):
            ResponseEmbed = discord.Embed(color=discord.Color.dark_embed())
            ResponseEmbed.set_image(url="https://www.astrobirb.dev/invisble.png")
            responses = Ticket.get("responses")
            for question, answer in responses.items():
                ResponseEmbed.add_field(
                    name=question, value=f"> {answer}", inline=False
                )
                if len(ResponseEmbed.fields) == 25:
                    break
        view = PTicketControl()
        try:
            msg = await channel.send(
                embeds=[Embed, ResponseEmbed] if ResponseEmbed else [Embed],
                content=" ".join(Mentions),
                allowed_mentions=discord.AllowedMentions(roles=True, users=True),
                view=view,
            )
        except discord.Forbidden:
            await self.client.db["Tickets"].update_one(
                {"_id": objectID},
                {
                    "$set": {
                        "error.message": "Bot does not have permission to send messages in the channel."
                    }
                },
            )
            return logging.critical(
                f"[on_pticket_open] Bot does not have permission to send messages in the channel {channel.id}"
            )
        await self.client.db["Tickets"].update_one(
            {"_id": objectID}, {"$set": {"ChannelID": channel.id, "MessageID": msg.id}}
        )

    @commands.Cog.listener()
    async def on_pticket_close(
        self, ObjectID: ObjectId, reason: str, member: discord.Member
    ):
        Result = await self.client.db["Tickets"].find_one({"_id": ObjectID})
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
        msg = await Channel.send("<a:Loading:1167074303905386587> Ticket closing...")
        messages = []
        compact = []

        P = await self.client.db["Panels"].find_one(
            {"name": Result.get("panel"), "guild": Guild.id}
        )
        if not P:
            return logging.critical("[on_pticket_close] I can't find the panel.")
        try:
            await self.client.db["Ticket Quota"].update_one(
                {
                    "GuildID": Guild.id,
                    "UserID": Result.get("claimed", {}).get("claimer"),
                },
                {"$inc": {"ClaimedTickets": 1}},
                upsert=True,
            )
        except:
            pass

        if P.get("TranscriptChannel"):
            await msg.edit(
                content=f"<a:Loading:1167074303905386587> Ticket closing... (Saving transcript this may take a second.)"
            )
            async for message in Channel.history(limit=None):
                if not message:
                    continue
                messages.append(
                    f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author.name}: {message.content}"
                )

                compact.append(
                    {
                        "author_id": message.author.id,
                        "content": message.content,
                        "author_name": message.author.name,
                        "message_id": message.id,
                        "author_avatar": str(
                            message.author.avatar.url if message.author.avatar else ""
                        ),
                        "attachments": [
                            await upload_file_to_r2(
                                await attachment.read(), attachment.filename, message
                            )
                            for attachment in message.attachments
                        ],
                        "embeds": [embed.to_dict() for embed in message.embeds],
                        "timestamp": message.created_at.timestamp(),
                    }
                )

            await self.client.db["Tickets"].update_one(
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
            TranscriptChannel = Guild.get_channel(P.get("TranscriptChannel"))
            if TranscriptChannel:
                Users = {
                    msg.get("author_id"): msg.get("author_name") for msg in compact
                }
                List = "\n".join(
                    [
                        f"<@{user_id}> ({user_name})"
                        for user_id, user_name in Users.items()
                    ]
                )

                embed = discord.Embed(
                    title="Ticket Closed",
                    color=discord.Color.dark_embed(),
                )
                embed.set_author(name=Guild.name, icon_url=Guild.icon)
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
                embed.add_field(name="Participants", value=List, inline=False)

                ButtonLink = discord.ui.View()
                ButtonLink.add_item(
                    discord.ui.Button(
                        label="View Transcript",
                        url=f"https://astrobirb.dev/transcript/{Result.get('_id')}",
                        emoji="<:Website:1132252914082127882>",
                        style=discord.ButtonStyle.blurple,
                    )
                )
                ReviewerMsg = None
                if user:
                    if P.get("AllowReviews", False):
                        view = discord.ui.View()
                        view.add_item(Review())
                        try:
                            ReviewerMsg = await user.send(embed=embed, view=view)
                        except:
                            pass

                    else:
                        try:
                            ReviewerMsg = await user.send(embed=embed)
                        except:
                            pass
                try:
                    if TranscriptChannel:
                        msg = await TranscriptChannel.send(embed=embed, view=ButtonLink)
                        if P.get("AllowReviews", False):
                            if msg:
                                await self.client.db["Tickets"].update_one(
                                    {"_id": ObjectID},
                                    {
                                        "$set": {
                                            "ReviewMSG": msg.id if msg else None,
                                            "ReviewChannel": (
                                                TranscriptChannel.id
                                                if TranscriptChannel
                                                else None
                                            ),
                                            "ReviewerMsg": (
                                                ReviewerMsg.id if ReviewerMsg else None
                                            ),
                                        }
                                    },
                                )
                except discord.Forbidden:
                    pass

        try:
            await Channel.delete()
        except discord.Forbidden:
            return logging.critical(
                f"[on_pticket_close] Bot does not have permission to delete the channel {Channel.id}"
            )


class Review(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="How would you rate the support?",
            options=[
                discord.SelectOption(label="1", value="1"),
                discord.SelectOption(label="2", value="2"),
                discord.SelectOption(label="3", value="3"),
                discord.SelectOption(label="4", value="4"),
                discord.SelectOption(label="5", value="5"),
                discord.SelectOption(label="6", value="6"),
                discord.SelectOption(label="7", value="7"),
                discord.SelectOption(label="8", value="8"),
                discord.SelectOption(label="9", value="9"),
                discord.SelectOption(label="10", value="10"),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        Ticket = await interaction.client.db["Tickets"].find_one(
            {"ReviewerMsg": interaction.message.id}
        )
        if not Ticket:
            return await interaction.response.send_message(
                "This isn't a review message.", ephemeral=True
            )
        if not Ticket.get("closed"):
            return await interaction.response.send_message(
                "This ticket is not closed.", ephemeral=True
            )
        if Ticket.get("review"):
            return await interaction.response.send_message(
                f"{no} **{interaction.user.display_name},** you've already reviewed this.",
                ephemeral=True,
            )

        await interaction.response.send_modal(FormalReview(Ticket, self.values[0]))


class FormalReview(discord.ui.Modal):
    def __init__(self, ticket: dict, rating: int):
        super().__init__(timeout=None, title="Exit Review", custom_id="REVIEW")

        self.ticket = ticket
        self.rating = rating
        self.review = discord.ui.TextInput(
            label="Review",
            placeholder="Write your review here.",
            min_length=10,
            max_length=500,
            required=False,
        )

        self.add_item(self.review)

    async def on_submit(self, interaction: discord.Interaction):
        review = self.review.value if not self.review.value == "" else "N/A"
        if not self.ticket.get("closed"):
            return await interaction.response.send_message(
                "This ticket is not closed.", ephemeral=True
            )
        if self.ticket.get("review"):
            return await interaction.response.send_message(
                f"{no} **{interaction.user.display_name},** you've already reviewed this.",
                ephemeral=True,
            )

        await interaction.client.db["Tickets"].update_one(
            {"_id": self.ticket.get("_id")},
            {"$set": {"review": review, "rating": self.rating}},
        )
        Result = await interaction.client.db["Tickets"].find_one(
            {"_id": self.ticket.get("_id")}
        )
        if not Result:
            return await interaction.response.send_message(
                "I can't find the ticket.", ephemeral=True
            )
        interaction.client.dispatch(
            "pticket_review", Result.get("_id"), self.rating, interaction.user
        )
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Reviewed",
                style=discord.ButtonStyle.success,
                disabled=True,
                emoji="<:whitecheck:1190819388941668362>",
            )
        )
        await interaction.response.edit_message(view=view)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(TicketsPublic(client))
