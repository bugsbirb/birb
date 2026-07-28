import os
from datetime import timedelta, datetime
from typing import NamedTuple, Optional, Union, Callable, Awaitable, Any

import discord
from discord.ext import commands

from core.bot import Paginator
from core.bot.emojis import Emojis


def DefaultTypes():
    return [
        "Activity Notice",
        "Verbal Warning",
        "Warning",
        "Strike",
        "Demotion",
        "Termination",
    ]


def IsSeperateBot():
    return any(
        [
            os.getenv("CUSTOM_GUILD"),
            os.getenv("DEFAULT_ALLOWED_SERVERS"),
            os.getenv("REMOVE_EMOJIS"),
        ]
    )


class ContextClass(NamedTuple):
    author: Optional[Union[discord.Member, discord.User]]
    guild: Optional[discord.Guild]
    send: Optional[Callable[..., Awaitable[Any]]]
    command: Optional[Union[commands.Command, discord.app_commands.Command]]
    client: Optional[discord.Client]
    channel: Optional[discord.TextChannel]


def CommandType(
    ctx: Union[commands.Context, discord.Interaction],
) -> ContextClass:
    if isinstance(ctx, commands.Context):
        return ContextClass(
            author=ctx.author,
            guild=ctx.guild,
            send=ctx.send,
            command=ctx.command,
            client=ctx.bot,
            channel=ctx.channel,
        )

    if isinstance(ctx, discord.Interaction):
        send = (
            ctx.followup.send if ctx.response.is_done() else ctx.response.send_message
        )
        return ContextClass(
            author=ctx.user,
            guild=ctx.guild,
            send=send,
            command=ctx.command,
            client=ctx.client,
            channel=ctx.channel,
        )

    raise TypeError(f"Unsupported type")


async def PaginatorButtons(extra: list = None):
    Sep = IsSeperateBot()
    emojis = {
        "first": f"{Emojis.chevrons_left}",
        "previous": f"{Emojis.chevron_left}",
        "next": f"{Emojis.chevron_right}",
        "last": f"{Emojis.chevrons_right}",
    }
    paginator = Paginator.Simple(
        PreviousButton=discord.ui.Button(
            emoji=emojis["previous"] if not Sep else None,
            label="<<" if Sep else None,
        ),
        NextButton=discord.ui.Button(
            emoji=emojis["next"] if not Sep else None,
            label=">>" if Sep else None,
        ),
        FirstEmbedButton=discord.ui.Button(
            emoji=emojis["first"] if not Sep else None,
            label="<<" if Sep else None,
        ),
        LastEmbedButton=discord.ui.Button(
            emoji=emojis["last"] if not Sep else None,
            label=">>" if Sep else None,
        ),
        InitialPage=0,
        timeout=360,
        extra=extra or [],
    )
    return paginator


async def TimeReformat(
    duration: str,
    *,
    back: bool = False,
    Interger: bool = False,
    DifferentNow: bool = False,
):

    now = datetime.now() if not DifferentNow else DifferentNow
    units = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
        "w": 604800,
    }

    duration = duration.lower().strip()
    TotalS = 0
    current = ""
    for char in duration:
        if char.isdigit():
            current += char
        elif char in units:
            if not current:
                raise ValueError("Invalid format: missing number before unit.")
            TotalS += int(current) * units[char]
            current = ""
        else:
            raise ValueError(f"Unknown character '{char}' in duration.")

    if Interger:
        return TotalS
    elif back:
        return now - timedelta(seconds=TotalS)
    else:
        return now + timedelta(seconds=TotalS)


def LeaderboardPlace(n):
    if 10 <= n % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def ReplaceVariables(data, replacements: dict):
    if data is None:
        return data
    if isinstance(data, str):
        for placeholder, replacement in replacements.items():
            if isinstance(replacement, (str, int, float, bool)):
                value = str(replacement)
            elif isinstance(replacement, (tuple, list)) and len(replacement) > 0:
                value = str(replacement[0])
            else:
                value = ""
            data = data.replace(placeholder, value)
        return data

    if isinstance(data, dict):
        return {
            ReplaceVariables(key, replacements): ReplaceVariables(value, replacements)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [ReplaceVariables(item, replacements) for item in data]

    if isinstance(data, tuple):
        return tuple(ReplaceVariables(item, replacements) for item in data)

    return data
