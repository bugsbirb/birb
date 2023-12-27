import discord
from discord.ext import commands

from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
load_dotenv()
PREFIX = os.getenv('PREFIX')
TOKEN = os.getenv('TOKEN')
STATUS = os.getenv('STATUS')
MONGO_URL = os.getenv('MONGO_URL')
SENTRY_URL = os.getenv('SENTRY_URL')
#quota
mongo = AsyncIOMotorClient(MONGO_URL)


db2 = mongo['quotab']

mccollection = db2["messages"]

MONGO_URL = os.getenv('MONGO_URL')
astro = AsyncIOMotorClient(MONGO_URL)
db = astro['astro']
modules = db['Modules']
scollection2 = db['staffrole']

class messageevent(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        staff_data = await scollection2.find_one({'guild_id': message.guild.id})
        if staff_data is None:
            return

        if 'staffrole' in staff_data:
            staff_role_ids = staff_data['staffrole']
            if not isinstance(staff_role_ids, list):
                staff_role_ids = [staff_role_ids]

            if any(role.id in staff_role_ids for role in message.author.roles):
                guild_id = message.guild.id
                author_id = message.author.id

                await mccollection.update_one(
                    {'guild_id': guild_id, 'user_id': author_id},
                    {'$inc': {'message_count': 1}},
                    upsert=True
                )

        

async def setup(client: commands.Bot) -> None:
    await client.add_cog(messageevent(client))        
