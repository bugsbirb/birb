
from openai import OpenAI
import os
apikey = os.getenv('OPENAI_API_KEY')
clientapi = OpenAI(api_key="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")

import discord
from discord.ext import commands, tasks
import datetime
from emojis import *
import os
import re
import random
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
questiondb = db['qotd']
modules = db['Modules']


class qotd(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def fetch_question(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://randomword.com/question") as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    question_element = soup.find("div", id="random_word")
                    question = question_element.text.strip()
                    print(f"[❓] {question}")
                    return question
                else:
                    print("Failed to fetch the question. Status code:", response.status)
                    return None
    
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
          await asyncio.sleep(0.5)
          question = await self.fetch_question()
          
          
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
                
                if selected_response in results.get('messages', []):
                        print('[❓QOTD] This has already been sent before ffs.')
                        for _ in range(5):
                            try:
                             await asyncio.sleep(0.5)
                             question = await self.fetch_question()
                             
                            
                             responses.append(question)                        
                            except Exception as e:
                                print(f'CODE RED!!! QOTD GENERATION DID NOT WORK {e}') 
                                continue     
                selected_response = random.choice(responses)         
                                                      


                
                await questiondb.update_one(
                    {'guild_id': int(results['guild_id'])},
                    {'$set': {'nextdate': datetime.datetime.now() + datetime.timedelta(days=1)},
                    '$push': {'messages': selected_response}
                    }, upsert=True
)
                
            
                guild = self.client.get_guild(int(results.get('guild_id', None)))
                if guild is None:
                    print('QOTD Guild is none aborting')
                    continue
                channel = guild.get_channel(int(results.get('channel_id', None)))
                if channel is None:
                    print('QOTD Channel is none aborting')
                    continue
                pingmsg = ""
                if results.get('pingrole'):
                    pingmsg = f"<@&{results.get('pingrole')}>"

                embed = discord.Embed(title="<:Tip:1167083259444875264> Question of the Day", description=f"{selected_response}", color=discord.Color.yellow(), timestamp=datetime.datetime.now())
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

