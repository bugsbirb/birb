from random import random
import discord


def get_attr(obj, key, default="N/A"):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class Variables:
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
    def guild(guild: discord.Guild) -> dict:
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
        extra = {
            "{newrank}": f"<@&{promotion.new}>",
            "{previous_rank}": f"<@&{promotion.previous}>",
            "{reason}": get_attr(promotion, "reason"),
            "{notes}": get_attr(promotion, "notes", ""),
            "{promotion.id}": get_attr(promotion, "random_string", ""),
        }
        return Variables.build(staff=staff, author=manager, extra=extra, guild=guild)
