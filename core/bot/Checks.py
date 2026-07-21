from discord.ext import commands

from core.errors.Config import ModuleMissingConfig
from core.errors.Permissions import MissingSetup


async def EnsureConfig(ctx: commands.Context, module: str):
    Config = await ctx.bot.db["Config"].find_one({"_id": ctx.guild.id})
    if Config is None:
        raise MissingSetup()
    if Config.get(module) is None:
        raise ModuleMissingConfig()
    return Config
