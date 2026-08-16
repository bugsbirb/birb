from discord import app_commands
from discord.ext import commands
from pymongo import AsyncMongoClient

from core.bot.emojis import *
from core.errors.Modules import ModuleDisabled

ENVIRONMENT = os.getenv("ENVIRONMENT")

client = AsyncMongoClient(os.getenv("MONGO_URL"))
DB = (
    client["BETA"]
    if ENVIRONMENT and ENVIRONMENT.lower() == "development"
    else client["astro"]
)
Configuration = DB["Config"]


def ModuleIsEnabled(module: str):
    async def predicate(ctx: commands.Context) -> bool:
        config = await Configuration.find_one({"_id": ctx.guild.id})
        if config is None:
            config = {"_id": id, "Modules": {}}
        elif "Modules" not in config:
            config["Modules"] = {}

        if bool(config.get("Modules", {}).get(module)):
            return True
        else:
            raise ModuleDisabled()

    def decorator(func):
        func = app_commands.check(predicate)(func)
        func = commands.check(predicate)(func)
        return func

    return decorator


async def ModuleCheck(id, module: str):
    config = await Configuration.find_one({"_id": id})
    if config is None:
        config = {"_id": id, "Modules": {}}
    elif "Modules" not in config:
        config["Modules"] = {}

    if bool(config.get("Modules", {}).get(module)):
        return True
    else:
        return False
