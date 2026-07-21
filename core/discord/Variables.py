from random import random
import discord


def get_attr(obj, key, default="N/A"):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class Variables:

    @staticmethod
    def role(prefix: str, role: discord.Role) -> dict:
        if not role:
            return {}
        return {
            f"{{{prefix}.mention}}": role.mention,
            f"{{{prefix}.name}}": role.name,
            f"{{{prefix}.id}}": str(role.id),
            f"{{{prefix}.color}}": str(role.color),
            f"{{{prefix}.position}}": str(role.position),
            f"{{{prefix}.member_count}}": str(len(role.members)),
            f"{{{prefix}.hoisted}}": "Yes" if role.hoist else "No",
            f"{{{prefix}.mentionable}}": "Yes" if role.mentionable else "No",
            f"{{{prefix}.created_at}}": f"<t:{int(role.created_at.timestamp())}:D>",
        }

    @staticmethod
    def message(message: discord.Message) -> dict:
        if not message:
            return {}
        return {
            "{message.id}": str(message.id),
            "{message.content}": message.content or "N/A",
            "{message.jump_url}": message.jump_url,
            "{message.created_at}": f"<t:{int(message.created_at.timestamp())}:R>",
            "{message.attachment_count}": str(len(message.attachments)),
            "{message.attachment_url}": (
                message.attachments[0].url if message.attachments else "N/A"
            ),
            **Variables.member("message.author", message.author),
        }

    @staticmethod
    def member(prefix: str, member: discord.Member) -> dict:
        if not member:
            return {}
        return {
            f"{{{prefix}.mention}}": member.mention,
            f"{{{prefix}.name}}": member.display_name,
            f"{{{prefix}.id}}": str(member.id),
            f"{{{prefix}.global_name}}": member.global_name,
            f"{{{prefix}.tag}}": (
                member.primary_guild.tag if member.primary_guild else "N/A"
            ),
            f"{{{prefix}.avatar}}": (
                member.display_avatar.url if member.display_avatar else None
            ),
            f"{{{prefix}.created_at}}": f"<t:{int(member.created_at.timestamp())}:D>",
            f"{{{prefix}.joined_at}}": (
                f"<t:{int(member.joined_at.timestamp())}:D>"
                if getattr(member, "joined_at", None)
                else "N/A"
            ),
            f"{{{prefix}.top_role}}": (
                member.top_role.mention if getattr(member, "top_role", None) else "N/A"
            ),
            f"{{{prefix}.role_count}}": (
                str(len(member.roles) - 1) if hasattr(member, "roles") else "0"
            ),
            f"{{{prefix}.boosting}}": (
                "Yes" if getattr(member, "premium_since", None) else "No"
            ),
            f"{{{prefix}.bot}}": "Yes" if member.bot else "No",
            f"{{{prefix}.status}}": str(getattr(member, "status", "N/A")),
        }

    @staticmethod
    def channel(channel: discord.TextChannel) -> dict:
        if not channel:
            return {}
        return {
            "{channel.name}": channel.name,
            "{channel.id}": str(channel.id),
            "{channel.mention}": channel.mention,
            "{channel.topic}": getattr(channel, "topic", None) or "N/A",
            "{channel.category}": channel.category.name if channel.category else "N/A",
            "{channel.jump_url}": channel.jump_url,
            "{channel.nsfw}": str(getattr(channel, "nsfw", False)),
            "{channel.slowmode}": str(getattr(channel, "slowmode_delay", 0)),
            "{channel.position}": str(getattr(channel, "position", 0)),
            "{channel.created_at}": f"<t:{int(channel.created_at.timestamp())}:D>",
        }

    @staticmethod
    def tools() -> dict:
        now = discord.utils.utcnow()
        ts = int(now.timestamp())
        return {
            "{date}": now.strftime("%Y-%m-%d"),
            "{time}": now.strftime("%H:%M:%S"),
            "{year}": str(now.year),
            "{timestamp}": str(ts),
            "{timestamp.short_time}": f"<t:{ts}:t>",
            "{timestamp.long_time}": f"<t:{ts}:T>",
            "{timestamp.short_date}": f"<t:{ts}:d>",
            "{timestamp.long_date}": f"<t:{ts}:D>",
            "{timestamp.short_datetime}": f"<t:{ts}:f>",
            "{timestamp.long_datetime}": f"<t:{ts}:F>",
            "{timestamp.relative}": f"<t:{ts}:R>",
            "{newline}": "\n",
            "{blank}": "\u200b",
        }

    @staticmethod
    async def guild(guild: discord.Guild) -> dict:
        if not guild:
            return {}
        return {
            "{guild.name}": guild.name,
            "{guild.id}": str(guild.id),
            "{guild.icon}": guild.icon.url if guild.icon else None,
            "{guild.banner}": guild.banner.url if guild.banner else None,
            "{guild.member_count}": str(
                guild.member_count or guild.approximate_member_count
            ),
            "{guild.created_at}": f"<t:{int(guild.created_at.timestamp())}:D>",
            "{guild.description}": guild.description or "N/A",
            "{guild.boost_tier}": str(guild.premium_tier),
            "{guild.boost_count}": str(guild.premium_subscription_count),
            "{guild.role_count}": str(len(guild.roles)),
            "{guild.channel_count}": str(len(guild.channels)),
            "{guild.emoji_count}": str(len(guild.emojis)),
            "{guild.verification_level}": str(guild.verification_level).title(),
            "{guild.vanity_url}": guild.vanity_url or "N/A",
        }

    @staticmethod
    def build(
        staff: discord.Member = None,
        author: discord.Member = None,
        guild: discord.Guild = None,
        extra: dict = None,
    ) -> dict:
        return {
            **Variables.guild(guild),
            **Variables.tools(),
            **Variables.member("staff", staff),
            **Variables.member("author", author),
            **(extra or {}),
        }

    @staticmethod
    def infraction(staff, Infraction, manager, guild) -> dict:
        expiration = get_attr(Infraction, "expiration", None)
        extra = {
            "{action}": get_attr(Infraction, "action"),
            "{reason}": get_attr(Infraction, "reason"),
            "{notes}": get_attr(Infraction, "notes"),
            "{expiration}": (
                f"<t:{int(expiration.timestamp())}:R>" if expiration else "N/A"
            ),
        }
        return Variables.build(staff=staff, author=manager, extra=extra, guild=guild)

    @staticmethod
    def promotion(staff, promotion, manager, guild) -> dict:
        newRole = guild.get_role(promotion.new) if guild else None
        previousRole = guild.get_role(promotion.previous) if guild else None

        extra = {
            "{newrank}": f"<@&{promotion.new}>",
            "{previous_rank}": f"<@&{promotion.previous}>",
            "{reason}": get_attr(promotion, "reason"),
            "{notes}": get_attr(promotion, "notes", ""),
            "{promotion.id}": get_attr(promotion, "random_string", ""),
            **Variables.role("new", newRole),
            **Variables.role("previous", previousRole),
        }
        return Variables.build(staff=staff, author=manager, extra=extra, guild=guild)
