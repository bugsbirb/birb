from discord import app_commands
from discord.ext import commands


class BotMissingConfig(commands.CommandError, app_commands.CheckFailure):
    def __init__(self):
        super().__init__()


class ModuleMissingConfig(commands.CommandError, app_commands.CheckFailure):
    def __init__(self):
        super().__init__()
