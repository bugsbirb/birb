import os
from utils.emojis import *
from motor.motor_asyncio import AsyncIOMotorClient

ENVIRONMENT = os.getenv("ENVIRONMENT")

client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
DB = client["BETA"] if ENVIRONMENT and ENVIRONMENT.lower() == "development" else client["astro"]
Configuration = DB["Config"]


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
