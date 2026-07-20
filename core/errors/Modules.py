from discord import app_commands
from discord.ext import commands


class ModuleDisabled(commands.CommandError, app_commands.CheckFailure):
    def __init__(self):
        super().__init__()
