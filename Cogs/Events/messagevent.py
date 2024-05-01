from discord.ext import commands
import discord
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
ignoredchannels = db2['Ignored Quota Channels']
mccollection = db2["messages"]
ignoredchannels = db2['Ignored Quota Channels']
MONGO_URL = os.getenv('MONGO_URL')
astro = AsyncIOMotorClient(MONGO_URL)
db = astro['astro']
modules = db['Modules']
scollection2 = db['staffrole']
arole = db['adminrole']

class messageevent(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return
        module = await modules.find_one({'guild_id': message.guild.id})

        if module:
         if module.get('Quota', False) is False:
            return
        else:
           return 
        if message.author.bot:
            return
        if message.author is None:
           return



        staff_data = await scollection2.find_one({'guild_id': message.guild.id})
        admin_data = await arole.find_one({'guild_id': message.guild.id})
        ignoredchannelsresult = await ignoredchannels.find_one({'guild_id': message.guild.id})
        if ignoredchannelsresult:
         if message.channel.id in ignoredchannelsresult.get('channel_ids', []):
           return

        if staff_data is None or 'staffrole' not in staff_data:
            return
        if admin_data is None or 'staffrole' not in admin_data:
            return

        staff_role_ids = staff_data['staffrole']
        admin_role_ids = admin_data['staffrole']
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
        else:
           if any(role.id in admin_role_ids for role in message.author.roles):    
            guild_id = message.guild.id
            author_id = message.author.id

            await mccollection.update_one(
                {'guild_id': guild_id, 'user_id': author_id},
                {'$inc': {'message_count': 1}},
                upsert=True
            )
        

async def setup(client: commands.Bot) -> None:
    await client.add_cog(messageevent(client))        
