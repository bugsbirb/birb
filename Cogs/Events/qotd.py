
import os
import discord
from discord.ext import commands, tasks
import datetime
from emojis import *
import os
import random
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
questiondb = db['qotd']
modules = db['Modules']
questionsa = db['Question Database']

class qotd(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def fetch_question(self):
        questionresult = await questionsa.find({}).to_list(
            length=None
        )
        if not questionresult:
            return
        question = random.choice(questionresult)
        return question.get('question', None)

        
    
    @tasks.loop(hours=1)
    async def sendqotd(self) -> None:
        print("[👀] Checking QOTD")
        
        result = await questiondb.find({}).to_list(
            length=None
        )
        if not result:
            return

        for results in result:
            postdate = results.get('nextdate', None)
            moduleddata = await modules.find_one({'guild_id': results.get('guild_id')})
            if moduleddata is None:
                continue
            if not moduleddata.get('QOTD', False):
                continue
            if postdate and postdate <= datetime.datetime.now():
                print("[👀] Sending QOTD")
                messages = []
                messages = results.get('messages', [])
                question = await self.fetch_question()
                while question in messages:
                    question = await self.fetch_question()
                messages.append(question)
                print(f"[👀] {question}")
                
                guild = self.client.get_guild(int(results.get('guild_id', None)))
                if guild is None:
                    print('[👀] QOTD Guild is none, aborting')
                    continue

                await questiondb.update_one(
                    {'guild_id': int(results['guild_id'])},
                    {'$set': {'nextdate': datetime.datetime.now() + datetime.timedelta(days=1),
                              'messages': messages}
                    }, upsert=True)
                
                channelid = results.get('channel_id', None)
                if channelid is None:
                    continue
                channelid = int(channelid)
                channel = guild.get_channel(channelid)
                if channel is None:
                    print('QOTD Channel is none, aborting')
                    continue

                pingmsg = ""
                if results.get('pingrole'):
                    pingmsg = f"<@&{results.get('pingrole')}>"

                embed = discord.Embed(title="<:Tip:1223062864793702431> Question of the Day",
                                      description=f"{question}",
                                      color=discord.Color.yellow(),
                                      timestamp=datetime.datetime.now())
                embed.set_footer(text=f"Day #{len(messages)}",
                                 icon_url="https://cdn.discordapp.com/emojis/1231270156647403630.webp?size=96&quality=lossless")
                try:
                    msg = await channel.send(pingmsg, embed=embed)
                except Exception as e:
                    print(f"I could not send the QOTD message to {guild.name}")
                    continue
                try:  
                    await msg.create_thread(name="QOTD Discussion")
                except Exception as e:
                    print(f"I could not create a thread for the QOTD message in {guild.name}")
                    continue
                await asyncio.sleep(2)
                

    @commands.Cog.listener()
    async def on_ready(self):
        self.sendqotd.stop()
        self.sendqotd.start()
        




async def setup(client: commands.Bot) -> None:
    await client.add_cog(qotd(client))    

