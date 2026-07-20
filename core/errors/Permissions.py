from discord import app_commands
from typing import Literal
from discord.ext import commands


class MissingPermission(commands.CommandError, app_commands.CheckFailure):
    def __init__(self, permission):
        self.permission = permission
        super().__init__(permission)


class MissingAdvancedPermissions(commands.CommandError, app_commands.CheckFailure):
    def __init__(self):
        super().__init__()


class MissingSetup(commands.CommandError, app_commands.CheckFailure):
    def __init__(self):
        super().__init__()


class MissingPermissionSetup(commands.CommandError, app_commands.CheckFailure):
    def __init__(self, perm: Literal["Admin", "Staff", "All"]):
        self.permission = perm
        super().__init__(perm)
