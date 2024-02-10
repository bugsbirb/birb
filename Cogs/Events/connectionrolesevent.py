
from discord.ext import commands
from emojis import *
import os
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
connectionroles = db['connectionroles']

class ConnectionRolesEvent(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
     added_roles = set(after.roles) - set(before.roles)
     removed_roles = set(before.roles) - set(after.roles)

     for role in added_roles:
        parent_roles_data = await connectionroles.find({"parent": role.id}).to_list(length=1000)
        for parent_role_data in parent_roles_data:
            child_role_id = parent_role_data["child"]
            child_role = after.guild.get_role(child_role_id)
            if child_role:
                await after.add_roles(child_role)

     for role in removed_roles:
        parent_roles_data = await connectionroles.find({"parent": role.id}).to_list(length=1000)
        for parent_role_data in parent_roles_data:
            child_role_id = parent_role_data["child"]
            child_role = after.guild.get_role(child_role_id)
            if child_role:
                await after.remove_roles(child_role)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(ConnectionRolesEvent(client))   