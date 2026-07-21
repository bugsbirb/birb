import logging
from datetime import datetime

import aiohttp
import discord
from bson import ObjectId
from discord.ext import commands

from core.discord.CustomEmbed import DisplayEmbed
from core.discord.Variables import Variables
from core.discord.permissions import premium

logger = logging.getLogger(__name__)


def DefaultEmbed(data, staff, manager):
    embed = discord.Embed(
        title="Staff Promotion",
        description=f"- **Staff Member:** {staff.mention}\n- **Role:** <@&{data.get('new')}>\n- **Reason:** {data.get('reason')}",
        color=discord.Color.dark_embed(),
    )
    if data.get("notes"):
        embed.description += f"\n- **Notes:** {data.get('notes')}"
    if not data.get("annonymous"):
        embed.set_author(
            name=f"Signed, {manager.display_name}", icon_url=manager.display_avatar
        )
    embed.set_thumbnail(url=staff.display_avatar)
    embed.set_footer(text=f"Promotion ID | {data.get('random_string')}")
    return embed


def Promotion(data):
    return PromotionItem(
        staff=data.get("staff"),
        management=data.get("management"),
        new=data.get("new"),
        reason=data.get("reason"),
        random_string=data.get("random_string"),
        guild_id=data.get("guild_id"),
        notes=data.get("notes"),
        annonymous=data.get("annonymous"),
        previous=data.get("previous", None),
    )


def CustomItem(data):
    return Embed(
        author=data.get("author"),
        author_icon=data.get("author_icon"),
        color=data.get("color"),
        description=data.get("description"),
        image=data.get("image"),
        thumbnail=data.get("thumbnail"),
        title=data.get("title"),
    )


class PromotionItem:
    def __init__(
        self,
        staff,
        management,
        new,
        reason,
        random_string,
        guild_id,
        previous,
        notes="N/A",
        annonymous=False,
    ):
        self.staff = staff
        self.management = management
        self.new = new
        self.reason = reason
        self.notes = notes
        self.random_string = random_string
        self.guild_id = guild_id
        self.annonymous = annonymous
        self.previous = previous


class Embed:
    def __init__(
        self, author, author_icon, color, description, image, thumbnail, title
    ):
        self.author = author
        self.author_icon = author_icon
        self.color = color
        self.description = description
        self.image = image
        self.thumbnail = thumbnail
        self.title = title


async def PromotionSystem(self, PromotionData, guild, member, manager):
    newId = PromotionData.get("new") or 0
    prevId = PromotionData.get("previous") or 0
    new = guild.get_role(int(newId)) if newId else None
    prev = guild.get_role(int(prevId)) if prevId else None
    if new:
        try:
            await member.add_roles(new, reason=f"Promotion initiated by {manager.name}")
        except (discord.Forbidden, discord.HTTPException):
            logging.warning(f"Unable to add new promotion role to {member.name}")
            pass
    if prev:
        try:
            await member.remove_roles(
                prev, reason=f"Promotion initiated by {manager.name}"
            )

        except (discord.Forbidden, discord.HTTPException):
            logging.warning(
                f"Unable to remove previous promotion role to {member.name}"
            )
            pass

    return await self.db["promotions"].find_one({"_id": PromotionData.get("_id")})


class on_promotion(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_promotion(
        self, objectid: ObjectId, Settings: dict, edit: bool = False
    ):
        PromotionData = await self.client.db["promotions"].find_one({"_id": objectid})
        promotion = Promotion(PromotionData)
        guild = await self.client.fetch_guild(promotion.guild_id)

        if guild is None:
            logging.warning(
                f"[🏠 on_promotion] {promotion.guild_id} is None and can't be found..?",
                extra={"objectId": str(objectid)},
            )
            return

        try:
            staff = await guild.fetch_member(int(promotion.staff))
        except:
            staff = None
        if staff is None:
            logging.warning(
                f"[🏠 on_promotion] @{guild.name} staff member {promotion.staff} can't be found.",
                extra={"objectId": str(objectid)},
            )
            return
        await self.client.db["Cooldown"].update_one(
            {"User": staff.id, "Guild": guild.id},
            {"$set": {"LastPromoted": datetime.now()}},
            upsert=True,
        )

        try:
            manager = await guild.fetch_member(int(promotion.management))
        except:
            manager = None
        if manager is None:
            logging.warning(
                f"[🏠 on_promotion] @{guild.name} manager {promotion.management} can't be found.",
                extra={"objectId": str(objectid)},
            )
            return

        ChannelID = Settings.get("Promo", {}).get("channel")
        if not ChannelID:
            logging.warning(
                f"[🏠 on_promotion] @{guild.name} no channel ID found in settings.",
                extra={"objectId": str(objectid)},
            )
            return
        try:
            channel = await guild.fetch_channel(int(ChannelID))
        except Exception as e:
            logger.error(
                f"[🏠 on_promotion] @{guild.name} the promotion channel can't be found. [1]",
                extra={"objectId": str(objectid)},
            )
            return
        if channel is None:
            logging.warning(
                f"[🏠 on_promotion] @{guild.name} the promotion channel can't be found. [2]",
                extra={"objectId": str(objectid)},
            )
            return
        Options = Settings.get("Module Options", {})
        view = None
        if Options.get("promotionissuer", False) is True:
            view = PromotionIssuer()
            view.issuer.label = f"Issued By {manager.display_name}"
        custom = await self.client.db["Customisation"].find_one(
            {"guild_id": promotion.guild_id, "type": "Promotions"}
        )
        PromotionData = await PromotionSystem(
            self.client, PromotionData, guild, staff, manager
        )
        if PromotionData:
            promotion = Promotion(PromotionData)
        if custom:
            replacements = await Variables.promotion(
                staff=staff, promotion=promotion, manager=manager, guild=guild
            )
            embed = await DisplayEmbed(
                data=custom, user=staff, replacements=replacements
            )
        else:
            embed = DefaultEmbed(PromotionData, staff, manager)
        if not edit:
            msg = None
            hook = None
            Status = await premium(guild.id)

            if (
                Settings.get("Promo", {}).get("Webhook", None)
                and Status
                and Settings.get("Promo", {}).get("Webhook", {}).get("Enabled") is True
            ):
                Webhook = await self.client.db["Webhooks"].find_one(
                    {"Type": "IP", "Channel": channel.id, "Guild": guild.id}
                )

                async def CreateHook(channel: discord.TextChannel):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            self.client.user.display_avatar.url
                        ) as resp:
                            if resp.status != 200:
                                return None
                            Btyes = await resp.read()
                    try:
                        hook = await channel.create_webhook(name="Birb", avatar=Btyes)

                        await self.client.db["Webhooks"].update_one(
                            {"Type": "IP", "Channel": channel.id, "Guild": guild.id},
                            {"$set": {"Id": hook.id}},
                            upsert=True,
                        )
                        return hook
                    except discord.Forbidden:
                        return

                if not Webhook or Webhook.get("Id"):
                    hook = await CreateHook(channel)

                hook = (
                    hook
                    or await self.client.fetch_webhook(webhook_id=Webhook.get("Id"))
                    or await CreateHook(channel)
                )

                if not hook:
                    return

                hook: discord.Webhook

                WS = Settings.get("Promo").get("Webhook", {})
                if view is not None:
                    msg = await hook.send(
                        staff.mention,
                        embed=embed,
                        view=view,
                        allowed_mentions=discord.AllowedMentions(users=True),
                        avatar_url=WS.get("Avatar") or None,
                        username=WS.get("Username") or "Birb",
                        wait=True,
                    )
                else:
                    msg: discord.WebhookMessage = await hook.send(
                        staff.mention,
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions(users=True),
                        avatar_url=WS.get("Avatar") or None,
                        username=WS.get("Username") or "Birb",
                        wait=True,
                    )

            else:
                try:
                    msg: discord.Message = await channel.send(
                        staff.mention,
                        embed=embed,
                        view=view,
                        allowed_mentions=discord.AllowedMentions(users=True),
                    )

                except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                    return None

        else:
            try:
                msg = await channel.fetch_message(PromotionData.get("msg_id"))

                if not msg:
                    return
                await msg.edit(embed=embed, view=view)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return
        await self.client.db["promotions"].update_one(
            {"_id": objectid},
            {"$set": {"jump_url": msg.jump_url, "msg_id": msg.id}},
        )
        self.client.dispatch("promotion_log", objectid, "create", manager)
        try:
            await staff.send(
                content=f"<:SmallArrow:1140288951861649418>From **@{guild.name}**",
                embed=embed,
            )
        except:
            pass


class PromotionIssuer(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(
        label=f"",
        style=discord.ButtonStyle.grey,
        disabled=True,
        emoji="<:flag:1223062579346145402>",
    )
    async def issuer(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_promotion(client))
