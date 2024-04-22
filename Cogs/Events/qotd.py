
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
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
questiondb = db['qotd']
modules = db['Modules']


class qotd(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        
    
    @tasks.loop(hours=6)
    async def sendqotd(self) -> None:
        print("[👀] Checking QOTD")
        
        result = await questiondb.find({}).to_list(
            length=None
        )
        if not result:
            return
        responses = []

        word_array = []
        word_array += [
            "concert", "music festival", "streetwear", "sneaker culture", "skateboarding", "surfing", "snowboarding", 
            "gaming", "esports",  "karaoke", "party", "hangout", "selfie", "vlog", 
            "blog", "podcast", "playlist", "tattoo", "piercing", "hairstyle", "makeup", "video game", "streaming", 
            "social media", "viral", "challenge", "memes", "jokes", "prank", "dance", "hip-hop", "rap", "rock", 
            "pop", "indie", "alternative", "graffiti", "street art", "skate park", "parkour", "extreme sports", 
            "biking", "outdoor adventure", "urban exploration", "thrill-seeking", "travel", "wanderlust", 
            "technology", "coding", "gadgets", "smartphones", "apps", "virtual reality", "augmented reality", 
            "gaming console", "PC gaming", "social networking", "texting", "emojis", "hashtags", "tiktok", 
            "instagram", "snapchat", "twitter", "reddit", "discord", "youtube", "spotify", "netflix", "amazon prime", 
            "binge-watching", "photography", "graphic design", "fashion design", "street photography", "digital art", 
            "skateboard design", "music production", "beatboxing", "songwriting", "dance choreography", "DJing", 
            "painting", "drawing", "creative writing", "poetry", "short stories", "novel writing", "filmmaking", 
            "video editing", "animation", "web development", "app development", "game development", "coding bootcamp",
            "rollerblading", "board games", "card games", "arcade games", "video game tournaments", "online communities", 
            "fan fiction", "urban fashion", "sneaker collecting", "comic books", "meme culture", "internet trends", 
            "street performance", "graffiti art", "photography challenges", "DIY crafts", "DIY fashion", 
            "DIY home decor", "DIY projects", "thrifting", "exploring abandoned places", "photography scavenger hunts", 
            "concert photography", "food challenges", "food blogging", "street food", "food festivals", 
            "cooking competitions", "food photography", "baking", "DIY cooking videos", "online gaming communities", 
            "LAN parties", "retro gaming", "board game cafes", "arcade bars", "escape rooms", "paintball", 
            "laser tag", "trampoline parks", "water parks", "amusement parks", "concert merchandise", "festival fashion"
        ]

        word_array = list(set(word_array))

        for _ in range(2):
         try:
          topic = random.choice(word_array)
          response = clientapi.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt = f"Make a short simple question of the day about {topic} and make it a personal opinionated question! And make these questions based towards a child audience. Also don't assume people have done stuff.  And don't make the question too complicated keep it simple. Do not assume people like stuff or have stuff or use stuff or assume anything about anyone!",
            temperature=0.7,
            max_tokens=200)
          text = str(response.choices[0].text).lstrip('"')
          text = text.rstrip('"')
          text = text.replace('"', "")
          responses.append(text)
         except Exception as e:
            print(f'CODE RED!!! QOTD GENERATION DID NOT WORK {e}') 
            continue

        
         
        

        
        for results in result:
            postdate = results.get('nextdate', None)
            selected_response = random.choice(responses)
            moduleddata = await modules.find_one({'guild_id': int(results.get('guild_id', None))})
            if moduleddata.get('QOTD', False) == False:
                    continue
            if postdate:
             if postdate and postdate <= datetime.datetime.now():
                
                print("[👀] Sending QOTD")
                messages = results.get('messages')
                if not isinstance(messages, list):
                    messages = [messages]
                if selected_response in messages:
                    print("Bruh")
                    topic = random.choice(word_array)
                    response = clientapi.completions.create(
                        model="gpt-3.5-turbo-instruct",
                        prompt = f"Make a short simple of the day about {topic} and make it a personal opinionated question! And make these questions based towards a children audience.  Also don't assume people have done stuff. And don't make the question too complicated keep it simple.",
                        temperature=0.7,
                        max_tokens=100,
                    )
                    text = str(response.choices[0].text).lstrip('"')
                    text = text.rstrip('"')
                    text = text.replace('"', "")               
                    selected_response = text
                    
        



        
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
        self.sendqotd.start()
        




async def setup(client: commands.Bot) -> None:
    await client.add_cog(qotd(client))    

