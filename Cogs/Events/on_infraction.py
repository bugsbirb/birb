import discord
from discord.ext import commands
import os
from bson import ObjectId
import aiohttp
import logging
from utils.permissions import premium
from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed

logger = logging.getLogger(__name__)
MONGO_URL = os.getenv("MONGO_URL")


def Replacements(staff: discord.Member, Infraction: dict, manager: discord.Member):
    def get_attr_or_key(obj, key):
        return getattr(obj, key, None) if hasattr(obj, key) else obj.get(key, "N/A")

    replacements = {
        "{staff.mention}": staff.mention,
        "{staff.name}": staff.display_name,
        "{staff.avatar}": staff.display_avatar.url if staff.display_avatar else None,
        "{author.mention}": manager.mention,
        "{author.name}": manager.display_name,
        "{action}": get_attr_or_key(Infraction, "action"),
        "{reason}": get_attr_or_key(Infraction, "reason"),
        "{notes}": get_attr_or_key(Infraction, "notes"),
        "{author.avatar}": (
            manager.display_avatar.url if manager.display_avatar else None
        ),
        "{expiration}": (
            f"<t:{int(get_attr_or_key(Infraction, 'expiration').timestamp())}:R>"
            if get_attr_or_key(Infraction, "expiration")
            else "N/A"
        ),
    }
    return replacements


def DefaultEmbed(data, staff, manager):
    embed = discord.Embed(
        title="Staff Consequences & Discipline",
        description=f"- **Staff Member:** {staff.mention}\n- **Action:** {data.get('action')}\n- **Reason:** {data.get('reason')}",
        color=discord.Color.dark_embed(),
    )
    if data.get("notes"):
        embed.description += f"\n- **Notes:** {data.get('notes')}"
    if not data.get("annonymous"):
        embed.set_author(
            name=f"Signed, {manager.display_name}", icon_url=manager.display_avatar
        )
    embed.set_thumbnail(url=staff.display_avatar)
    embed.set_footer(text=f"Infraction ID | {data.get('random_string')}")
    return embed


def InfractItem(data):
    return InfractionItem(
        staff=data.get("staff"),
        management=data.get("management"),
        action=data.get("action"),
        reason=data.get("reason"),
        notes=data.get("notes"),
        expiration=data.get("expiration"),
        voided=data.get("voided"),
        expired=data.get("expired"),
        random_string=data.get("random_string"),
        guild_id=data.get("guild_id"),
        annonymous=data.get("annonymous"),
        msg_id=data.get("msg_id"),
        webhook_id=data.get("WebhookID"),
        escalated_from=data.get("EscalatedFrom"),
        skipExec=data.get("skipExec"),
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


class InfractionItem:
    def __init__(
        self,
        staff,
        management,
        action,
        reason,
        notes,
        expiration,
        voided,
        expired,
        random_string,
        guild_id,
        annonymous,
        msg_id,
        webhook_id,
        escalated_from,
        skipExec,
    ):
        self.staff = staff
        self.management = management
        self.action = action
        self.reason = reason
        self.notes = notes
        self.expiration = expiration
        self.voided = voided
        self.expired = expired
        self.random_string = random_string
        self.guild_id = guild_id
        self.annonymous = annonymous
        self.msg_id = msg_id
        self.webhook_id = webhook_id
        self.escalated_from = escalated_from
        self.skipExec = skipExec


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


class on_infractions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_infraction(
        self, objectid: ObjectId, Settings: dict, Actions: dict, Type: str = None
    ):
        logger.info("[on_infraction] Trigged", extra={"objectId": str(objectid)})
        if Type is None:
            InfractionData = await self.client.db["infractions"].find_one(
                {"_id": objectid}
            )
        else:
            InfractionData = await self.client.db["Suspensions"].find_one(
                {"_id": objectid}
            )
        Infraction = InfractItem(InfractionData)
        guild = await self.client.fetch_guild(Infraction.guild_id)
        if guild is None:
            logging.warning(
                f"[🏠 on_infraction] {Infraction.guild_id} is None and can't be found..?",
                extra={"objectId": str(objectid)},
            )
            return

        try:
            staff = await guild.fetch_member(int(Infraction.staff))
        except:
            staff = None
        if staff is None:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} staff member {Infraction.staff} can't be found.",
                extra={"objectId": str(objectid)},
            )
            return

        try:
            manager = await guild.fetch_member(int(Infraction.management))
        except:
            manager = None
        if manager is None:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} manager {Infraction.management} can't be found.",
                extra={"objectId": str(objectid)},
            )
            return

        ChannelID = Settings.get(
            "Infraction" if Type is None else "Suspension", {}
        ).get("channel")
        if not ChannelID:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} no channel ID found in settings.",
                extra={"objectId": str(objectid)},
            )
            return
        try:
            channel = await guild.fetch_channel(int(ChannelID))
        except Exception as e:
            logger.error(
                f"[🏠 on_infraction] @{guild.name} the infraction channel can't be found. [1]",
                extra={"objectId": str(objectid)},
            )
            return
        if channel is None:
            logging.warning(
                f"[🏠 on_infraction] @{guild.name} the infraction channel can't be found. [2]",
                extra={"objectId": str(objectid)},
            )
            return

        custom = await self.client.db["Customisation"].find_one(
            {
                "guild_id": Infraction.guild_id,
                "type": "Infractions" if Type is None else "Suspension",
            }
        )
        embed = discord.Embed()
        view = None
        if Settings.get("Module Options", {}).get("infractedbybutton"):
            view = InfractionIssuer()
            view.issuer.label = f"Issued By {manager.display_name}"

        if custom:
            replacements = Replacements(
                staff=staff, Infraction=Infraction, manager=manager
            )
            if Type == "Suspension":
                replacements.update(
                    {
                        "{start_time}": f"<t:{int(InfractionData.get('start_time').timestamp())}:f>",
                        "{end_time}": f"<t:{int(InfractionData.get('end_time').timestamp())}:f>",
                    }
                )
            embed = await DisplayEmbed(
                data=custom, user=staff, replacements=replacements
            )
        else:

            embed = DefaultEmbed(InfractionData, staff, manager)
        if not Type:
            embed.set_footer(text=f"Infraction ID | {Infraction.random_string}")

        ch = await self.InfractionTypes(
            Actions, staff, manager, config=Settings, Infraction=InfractionData
        )
        if ch and ch.get("Channel"):
            try:
                N = await self.client.fetch_channel(int(ch.get("Channel")))
            except (discord.Forbidden, discord.NotFound):
                N = None
            if N:
                channel = N

        embeds = [embed]

        if Infraction.escalated_from and not Infraction.skipExec:
            CheckedActions = InfractionData.get("EscalationChain", [])
            Org = Infraction.escalated_from
            action = Infraction.action

            parts = []
            for step in CheckedActions:
                count = step["count"]
                Action = step["action"]
                plural = "s" if count != 1 else ""
                parts.append(f"{count} {Action}{plural}")

            if len(parts) > 1:
                Text = " and ".join(parts[-2:])
            else:
                Text = parts[0]

            EscFrom = discord.Embed(color=discord.Color.blue()).set_author(
                name=f"Automatically escalated from {Text} to {action}",
                icon_url="https://cdn.discordapp.com/emojis/1401307998260822028.webp?size=96",
            )
            embeds.append(EscFrom)
        msg = None
        hook = None
        Status = await premium(guild.id)

        if (
            Settings.get("Infraction", {}).get("Webhook", None)
            and Status
            and Settings.get("Infraction", {}).get("Webhook", {}).get("Enabled") is True
        ):
            hook = None
            Webhook = await self.client.db["Webhooks"].find_one(
                {"Type": "IF", "Channel": channel.id, "Guild": guild.id}
            )

            async def CreateHook(channel: discord.TextChannel):
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.client.user.display_avatar.url) as resp:
                        if resp.status != 200:
                            return None
                        Btyes = await resp.read()
                try:
                    hook = await channel.create_webhook(name="Birb", avatar=Btyes)
                    await self.client.db["Webhooks"].update_one(
                        {"Type": "IF", "Channel": channel.id, "Guild": guild.id},
                        {"$set": {"Id": hook.id}},
                        upsert=True,
                    )
                    return hook
                except discord.Forbidden:
                    return None

            if not Webhook or not Webhook.get("Id"):
                hook = await CreateHook(channel)
            else:
                try:
                    hook = await self.client.fetch_webhook(Webhook.get("Id"))
                except discord.NotFound:
                    hook = await CreateHook(channel)

            if not hook:
                return
            WS = Settings.get("Infraction").get("Webhook", {})
            if view is not None:
                msg = await hook.send(
                    staff.mention,
                    embeds=embeds,
                    view=view,
                    allowed_mentions=discord.AllowedMentions(users=True),
                    avatar_url=WS.get("Avatar") or None,
                    username=WS.get("Username") or "Birb",
                    wait=True,
                )
            else:
                msg: discord.WebhookMessage = await hook.send(
                    staff.mention,
                    embeds=embeds,
                    allowed_mentions=discord.AllowedMentions(users=True),
                    avatar_url=WS.get("Avatar") or None,
                    username=WS.get("Username") or "Birb",
                    wait=True,
                )

        else:
            try:
                msg: discord.Message = await channel.send(
                    staff.mention,
                    embeds=[embed],
                    view=view,
                    allowed_mentions=discord.AllowedMentions(users=True),
                )

            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                return None

        if Type is None:
            await self.client.db["infractions"].update_one(
                {"_id": objectid},
                {
                    "$set": {
                        "jump_url": msg.jump_url,
                        "msg_id": msg.id,
                        "Updated": ch,
                        "WebhookID": hook.id if hook else None,
                    }
                },
            )
        else:
            await self.client.db["Suspensions"].update_one(
                {"_id": objectid},
                {"$set": {"jump_url": msg.jump_url, "msg_id": msg.id}},
            )
        self.client.dispatch("infraction_log", objectid, "create", manager)

        consreult = await self.client.db["consent"].find_one({"user_id": staff.id})
        if Settings.get("Module Options", {}).get("Direct Message", True):
            if not consreult or consreult.get("infractionalert") is not False:
                try:
                    await staff.send(
                        content=f"<:SmallArrow:1140288951861649418>From  **{guild.name}**",
                        embed=embed,
                    )
                except:
                    pass

    async def InfractionTypes(
        self,
        data,
        staff: discord.Member,
        manager: discord.Member,
        config: dict,
        Infraction: dict,
    ):
        print("1")
        if not data:
            return {}
        Actions = {}
        print("2")
        print(data)
        try:
            channel = False
            if data.get("givenroles"):
                roles = [
                    discord.utils.get(staff.guild.roles, id=role)
                    for role in data.get("givenroles")
                    if role is not None
                ]
                if roles:
                    try:
                        await staff.add_roles(
                            *roles,
                            reason=f"Infraction Types initated by {manager.name}.",
                        )
                    except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                        pass
                    Actions["AddedRoles"] = [role.id for role in roles]

            if data.get("DemotionRole"):
                print("omg")

                await DemotionSystem(
                    self=self.client,
                    DemotionData=Infraction,
                    settings=config,
                    guild=staff.guild,
                    member=manager,
                    manager=manager,
                )

            if data.get("changegrouprole") and data.get("grouprole"):
                from utils.roblox import UpdateMembership

                try:
                    await UpdateMembership(
                        user=staff,
                        role=data.get("grouprole"),
                        author=manager,
                        config=config,
                    )
                except Exception:
                    pass
                Actions["ChangedGroupRole"] = True

            if data.get("removedroles"):
                roles = [
                    discord.utils.get(staff.guild.roles, id=role)
                    for role in data.get("removedroles")
                    if role is not None
                ]
                if roles:
                    try:
                        await staff.remove_roles(
                            *roles,
                            reason=f"Infraction Types initated by {manager.name}.",
                        )
                    except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                        pass
                    Actions["RemovedRoles"] = [role.id for role in roles]

            if data.get("staffdatabaseremoval", False) is True:
                OriginalData = await self.client.db["staff database"].find_one(
                    {"staff_id": staff.id, "guild_id": staff.guild.id}
                )
                await self.client.db["staff database"].delete_one(
                    {"staff_id": staff.id, "guild_id": staff.guild.id}
                )
                Actions["DbRemoval"] = OriginalData

            if data.get("channel"):
                channel = await staff.guild.fetch_channel(data.get("channel"))
                Actions["Channel"] = data.get("channel")

            if channel:
                client = await staff.guild.fetch_member(self.client.user.id)
                if channel.permissions_for(client).send_messages is False:
                    return

            return Actions

        except Exception:
            return Actions


async def DemotionSystem(
    self: commands.bot,
    DemotionData: dict,
    settings: dict,
    guild: discord.Guild,
    member: discord.Member,
    manager: discord.Member,
):
    logger.info(f"[Demotion] Started for member {member.id} in guild {guild.id}")

    if not settings.get("Promo"):
        logger.warning(f"[Demotion] No Promo settings found for guild {guild.id}")
        return await self.db["infractions"].find_one({"_id": DemotionData.get("_id")})

    DemoSystemType = settings.get("Promo", {}).get("System", {}).get("type", None)
    logger.info(f"[Demotion] Using system type: {DemoSystemType}")
    PrevRole = None
    SkipRole = None

    if not DemoSystemType:
        return await self.db["infractions"].find_one({"_id": DemotionData.get("_id")})

    if DemoSystemType == "multi":
        Department = DemotionData.get("multi", {}).get("Department")
        SkipTo = DemotionData.get("multi", {}).get("SkipTo")
        logger.info(
            f"[Demotion] Multi-department mode - Department: {Department}, SkipTo: {SkipTo}"
        )

        DepartmentHierarchies = [
            dept
            for sublist in settings.get("Promo", {})
            .get("System", {})
            .get("multi", {})
            .get("Departments", [])
            for dept in sublist
        ]
        if not DepartmentHierarchies or not Department:
            logger.warning(f"[Demotion] No department hierarchies or department found")
            return await self.db["infractions"].find_one(
                {"_id": DemotionData.get("_id")}
            )
        DepartmentHierarchy = next(
            (dept for dept in DepartmentHierarchies if dept.get("name") == Department),
            None,
        )
        if not DepartmentHierarchy:
            logger.warning(
                f"[Demotion] Department {Department} not found in hierarchies"
            )
            return await self.db["infractions"].find_one(
                {"_id": DemotionData.get("_id")}
            )

        RoleIDs = DepartmentHierarchy.get("ranks", [])
        logger.info(f"[Demotion] Found {len(RoleIDs)} roles in hierarchy")

        MemberRoles = set(member.roles)
        SortedRoles = [
            guild.get_role(int(RoleID))
            for RoleID in RoleIDs
            if guild.get_role(int(RoleID))
        ]
        SortedRoles.sort(key=lambda Role: Role.position)

        if SkipTo:
            SkipRole = guild.get_role(int(SkipTo))
            logger.info(
                f"[Demotion] SkipRole set: {SkipRole.name if SkipRole else 'None'}"
            )
            if SkipRole and SkipRole in SortedRoles:
                try:
                    await member.add_roles(
                        SkipRole,
                        reason=f"Staff Demotion (Skipped) in {Department} initiated by {manager.name}",
                    )
                    logger.info(
                        f"[Demotion] Added skip role {SkipRole.name} to {member.name}"
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(f"[Demotion] Failed to add skip role: {e}")
                    pass

                for Role in SortedRoles:
                    if Role in MemberRoles and Role != SkipRole:
                        try:
                            await member.remove_roles(
                                Role,
                                reason=f"Replaced by {SkipRole.name} initiated by {manager.name}",
                            )
                            logger.info(
                                f"[Demotion] Removed role {Role.name} from {member.name}"
                            )
                        except (discord.Forbidden, discord.HTTPException) as e:
                            logger.error(
                                f"[Demotion] Failed to remove role {Role.name}: {e}"
                            )
                            pass

                await self.db["infractions"].update_one(
                    {"_id": DemotionData.get("_id")}, {"$set": {"new": SkipRole.id}}
                )
                logger.info(f"[Demotion] Updated infraction with skip role ID")
                return await self.db["infractions"].find_one(
                    {"_id": DemotionData.get("_id")}
                )

        for Index, CurrentRole in enumerate(SortedRoles):
            if CurrentRole in MemberRoles and Index - 1 >= 0:
                PrevRole = SortedRoles[Index - 1]
                logger.info(
                    f"[Demotion] Demoting from {CurrentRole.name} to {PrevRole.name}"
                )
                try:
                    await member.add_roles(
                        PrevRole,
                        reason=f"Staff Demotion in {Department} initiated by {manager.name}",
                    )
                    logger.info(
                        f"[Demotion] Added role {PrevRole.name} to {member.name}"
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(f"[Demotion] Failed to add role {PrevRole.name}: {e}")
                    pass
                try:
                    await member.remove_roles(
                        CurrentRole, reason=f"Replaced by {PrevRole.name}"
                    )
                    logger.info(
                        f"[Demotion] Removed role {CurrentRole.name} from {member.name}"
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(
                        f"[Demotion] Failed to remove role {CurrentRole.name}: {e}"
                    )
                    pass
                break
            elif CurrentRole in MemberRoles and Index - 1 < 0:
                logger.info(
                    f"[Demotion] At bottom of hierarchy, removing {CurrentRole.name}"
                )
                try:
                    await member.remove_roles(
                        CurrentRole,
                        reason=f"Removed from bottom of hierarchy by {manager.name}",
                    )
                    logger.info(
                        f"[Demotion] Removed role {CurrentRole.name} from {member.name}"
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(
                        f"[Demotion] Failed to remove role {CurrentRole.name}: {e}"
                    )
                    pass
                break

        RoleID = SkipRole.id if SkipTo else PrevRole.id if PrevRole else None
        if RoleID:
            await self.db["infractions"].update_one(
                {"_id": DemotionData.get("_id")}, {"$set": {"new": RoleID}}
            )

    if DemoSystemType == "single":
        HierarchyRoles = (
            settings.get("Promo", {})
            .get("System", {})
            .get("single", {})
            .get("Hierarchy", [])
        )
        SkipTo = DemotionData.get("single", {}).get("SkipTo")
        logger.info(
            f"[Demotion] Single system mode - SkipTo: {SkipTo}, Hierarchy roles: {len(HierarchyRoles)}"
        )

        if not HierarchyRoles:
            logger.warning("[Demotion] No hierarchy roles found in single system")
            return await self.db["infractions"].find_one(
                {"_id": DemotionData.get("_id")}
            )

        MemberRoles = set(member.roles)
        SortedRoles = [
            guild.get_role(int(RoleID))
            for RoleID in HierarchyRoles
            if guild.get_role(int(RoleID))
        ]
        SortedRoles.sort(key=lambda Role: Role.position)

        if SkipTo:
            SkipRole = guild.get_role(int(SkipTo))
            logger.info(
                f"[Demotion] SkipRole set: {SkipRole.name if SkipRole else 'None'}"
            )

            if SkipRole and SkipRole in SortedRoles:
                try:
                    await member.add_roles(
                        SkipRole,
                        reason=f"Staff Demotion (Skipped) initiated by {manager.name}",
                    )
                    logger.info(
                        f"[Demotion] Added skip role {SkipRole.name} to {member.name}"
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(f"[Demotion] Failed to add skip role: {e}")
                    pass

                for Role in MemberRoles:
                    if Role in SortedRoles and Role != SkipRole:
                        try:
                            await member.remove_roles(
                                Role, reason=f"Replaced by {SkipRole.name}"
                            )
                            logger.info(
                                f"[Demotion] Removed role {Role.name} from {member.name}"
                            )
                        except (discord.Forbidden, discord.HTTPException) as e:
                            logger.error(
                                f"[Demotion] Failed to remove role {Role.name}: {e}"
                            )
                            pass

                await self.db["infractions"].update_one(
                    {"_id": DemotionData.get("_id")}, {"$set": {"new": SkipRole.id}}
                )
                return await self.db["infractions"].find_one(
                    {"_id": DemotionData.get("_id")}
                )

        for Index, CurrentRole in enumerate(SortedRoles):
            if CurrentRole in MemberRoles and Index - 1 >= 0:
                PrevRole = SortedRoles[Index - 1]
                logger.info(
                    f"[Demotion] Demoting from {CurrentRole.name} to {PrevRole.name}"
                )
                try:
                    await member.add_roles(
                        PrevRole, reason=f"Staff Demotion initiated by {manager.name}"
                    )
                    logger.info(
                        f"[Demotion] Added role {PrevRole.name} to {member.name}"
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(f"[Demotion] Failed to add role {PrevRole.name}: {e}")
                    pass
                try:
                    await member.remove_roles(
                        CurrentRole, reason=f"Replaced by {PrevRole.name}"
                    )
                    logger.info(
                        f"[Demotion] Removed role {CurrentRole.name} from {member.name}"
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(
                        f"[Demotion] Failed to remove role {CurrentRole.name}: {e}"
                    )
                    pass
                break
            elif CurrentRole in MemberRoles and Index - 1 < 0:
                logger.info(
                    f"[Demotion] At bottom of hierarchy, removing {CurrentRole.name}"
                )
                try:
                    await member.remove_roles(
                        CurrentRole,
                        reason=f"Removed from bottom of hierarchy by {manager.name}",
                    )
                    logger.info(
                        f"[Demotion] Removed role {CurrentRole.name} from {member.name}"
                    )
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(
                        f"[Demotion] Failed to remove role {CurrentRole.name}: {e}"
                    )
                    pass
                break
        RoleID = SkipRole.id if SkipTo else PrevRole.id if PrevRole else None
        if RoleID:
            await self.db["infractions"].update_one(
                {"_id": DemotionData.get("_id")}, {"$set": {"new": RoleID}}
            )

    logger.info(f"[Demotion] Completed for member {member.id}")
    return await self.db["infractions"].find_one({"_id": DemotionData.get("_id")})


class InfractionIssuer(discord.ui.View):
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
    await client.add_cog(on_infractions(client))
