
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
        responses = []
        for _ in range(5):
         try:
          question = await self.fetch_question()
          print(f"[❓QOTD] {question}")
          
          
          responses.append(question)
         except Exception as e:
            print(f'CODE RED!!! QOTD GENERATION DID NOT WORK {e}') 
            continue

        selected_response = random.choice(responses) 
        for results in result:
            postdate = results.get('nextdate', None)
            moduleddata = await modules.find_one({'guild_id': results.get('guild_id')})
            if moduleddata is None:
                continue
            if moduleddata.get('QOTD', False) == False:
                    continue
            if postdate:
             if postdate and postdate <= datetime.datetime.now():
                
                print("[👀] Sending QOTD")
                if selected_response in results.get( 'messages', []):
                        print('[❓QOTD] This has already been sent before ffs.')
                        for _ in range(5):
                            try:
                             question = await self.fetch_question()
                             print(f"[❓QOTD Again] {question}")                             
                            
                             responses.append(question)                        
                            except Exception as e:
                                print(f'CODE RED!!! QOTD GENERATION DID NOT WORK {e}') 
                                continue     
                selected_response = random.choice(responses)         
                                                      
            
                guild = self.client.get_guild(int(results.get('guild_id', None)))
                if guild is None:
                    print('QOTD Guild is none aborting')
                    continue
                await questiondb.update_one(
                    {'guild_id': int(results['guild_id'])},
                    {'$set': {'nextdate': datetime.datetime.now() + datetime.timedelta(days=1)},
                    '$push': {'messages': selected_response}
                    }, upsert=True
)                
                channel = guild.get_channel(int(results.get('channel_id', None)))
                if channel is None:
                    print('QOTD Channel is none aborting')
                    continue
                pingmsg = ""
                if results.get('pingrole'):
                    pingmsg = f"<@&{results.get('pingrole')}>"

                embed = discord.Embed(title="<:Tip:1223062864793702431> Question of the Day", description=f"{selected_response}", color=discord.Color.yellow(), timestamp=datetime.datetime.now())
                embed.set_footer(text=f"Day #{len(results.get('messages', ['none']))}", icon_url="https://cdn.discordapp.com/emojis/1231270156647403630.webp?size=96&quality=lossless")
                try:
                 msg = await channel.send(pingmsg, embed=embed)
                except Exception as e:
                    print(f"I could not send the qotd message to {guild.name}")
                    continue           
                try:  
                 await msg.create_thread(name="QOTD Discussion")
                except Exception as e:
                    print(f"I could not create a thread to the qotd message in {guild.name}")
                    continue      
                await asyncio.sleep(2)
                

    @commands.Cog.listener()
    async def on_ready(self):
        self.sendqotd.stop()
        self.sendqotd.start()
        




async def setup(client: commands.Bot) -> None:
    await client.add_cog(qotd(client))    

