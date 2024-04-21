
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


        word_array = [
            "music", "vacation", "sports", "workout", "movie", "memory", "hobby", "book", "recipe", "getaway",
            "career", "cuisine", "fashion", "TV", "lyrics", "playlist", "home", "business", "season", "video game",
            "adventure", "artist", "pet", "era", "game", "quote", "activity", "art", "genre", "team", "routine", "style", "show", "song", "idea", "work",

            "inspiration", "challenge", "creativity", "reflection", "motivation", "achievement", "growth", "exploration", "journey",
            "goal", "success", "experience", "wisdom", "perspective", "discovery", "imagination", "aspiration", "learning",
            "nature", "friendship", "health", "family", "dream", "passion", "advice", "confidence", "memory", "travel",
            "celebration", "culture", "entertainment", "achievement", "technology", "innovation", "happiness", "love", "insight",
            "community", "opportunity", "challenge", "resilience", "victory", "celebration", "effort", "tradition", "spirituality",
            "kindness", "compassion", "perseverance", "connection", "legacy", "inspiration", "reflection", "courage", "adaptability",
            "gratitude", "ambition", "balance", "wellness", "mindfulness", "leadership", "knowledge", "curiosity", "communication",
            "friendship", "motivation", "passion", "creativity", "learning", "growth", "confidence", "empathy", "achievement",
            "problem-solving", "determination", "humility", "optimism", "perseverance", "resilience", "positivity", "integrity",
            "teamwork", "collaboration", "compassion", "kindness", "innovation", "curiosity", "adaptability", "flexibility",
            "responsibility", "emotional intelligence", "self-awareness", "self-improvement", "grit", "dedication", "discipline",
            "focus", "patience", "open-mindedness", "tolerance", "acceptance", "forgiveness", "generosity", "self-reflection",
            "mindfulness", "meditation", "yoga", "well-being", "self-care", "growth mindset", "purpose", "meaning", "fulfillment",
            "connection", "communication", "leadership", "inclusivity", "diversity", "equality", "justice", "environment",
            "sustainability", "conservation", "climate change", "social responsibility", "ethical practices", "global citizenship",
            "volunteerism", "activism", "philanthropy", "education", "literacy", "STEM", "arts", "culture", "heritage", "tradition",
            "music", "literature", "art", "film", "theater", "dance", "photography", "design", "fashion", "architecture",
            "culinary arts", "visual arts", "performing arts", "fine arts", "digital arts", "creative expression", "imagination",
            "inspiration", "innovation", "creativity", "exploration", "experimentation", "discovery", "expression", "interpretation",
            "perspective", "vision", "idea", "concept", "design", "composition", "narrative", "storytelling", "symbolism",
            "metaphor", "analogy", "allegory", "mythology", "folklore", "legend", "fable", "paradox", "irony", "satire", "humor",
            "drama", "comedy", "tragedy", "romance", "adventure", "mystery", "suspense", "horror", "fantasy", "science fiction",
            "non-fiction", "biography", "autobiography", "memoir", "essay", "journalism", "reporting", "investigation", "analysis",
            "interpretation", "critique", "review", "discussion", "debate", "dialogue", "conversation", "communication", "collaboration",
            "interaction", "engagement", "participation", "community", "society", "culture", "tradition", "custom", "ritual",
            "ceremony", "celebration", "festivity", "holiday", "occasion", "event", "gathering", "assembly", "meeting", "conference",
            "symposium", "convention", "exhibition", "fair", "expo", "festival", "concert", "performance", "showcase", "presentation",
            "demonstration", "workshop", "seminar", "lecture", "lesson", "classroom", "education", "learning", "teaching", "instruction",
            "pedagogy", "curriculum", "lesson plan", "syllabus", "assessment", "evaluation", "grading", "feedback", "revision", "improvement",
            "development", "progress", "achievement", "success", "accomplishment", "victory", "triumph", "milestone", "landmark",
            "breakthrough", "discovery", "innovation", "invention", "creation", "artistry", "craftsmanship", "mastery", "expertise",
            "skill", "talent", "aptitude", "ability", "proficiency", "competence", "capability", "knowledge", "wisdom", "insight",
            "understanding", "awareness", "consciousness", "perception", "perspective", "interpretation", "appreciation", "gratitude",
            "admiration", "respect", "esteem", "honor", "pride", "dignity", "integrity", "character", "morality", "ethics",
            "values", "principles", "virtues", "justice", "fairness", "equity", "equality", "diversity", "inclusion",
            "compassion", "empathy", "kindness", "generosity", "altruism", "philanthropy", "service", "volunteerism",
            "activism", "advocacy", "solidarity", "collaboration", "cooperation", "unity", "peace", "harmony", "balance",
            "well-being", "health", "happiness", "joy", "contentment", "satisfaction", "fulfillment", "serenity", "tranquility",
            "peace of mind", "inner peace", "mindfulness", "meditation", "yoga", "self-care", "self-improvement", "growth mindset",
            "resilience", "perseverance", "determination", "grit", "optimism", "positivity", "confidence", "self-esteem",
            "self-confidence", "self-awareness", "self-discovery", "self-expression", "self-realization", "authenticity",
            "identity", "individuality", "autonomy", "freedom", "liberation", "empowerment", "agency", "self-determination",
            "self-actualization", "creativity", "imagination", "innovation", "experimentation", "exploration", "discovery",
            "expression", "inspiration", "passion", "enthusiasm", "drive", "motivation", "ambition", "dedication", "commitment",
            "persistence", "discipline", "focus", "concentration", "productivity", "efficiency", "effectiveness", "success",
            "achievement", "fulfillment", "satisfaction", "happiness", "joy", "contentment", "gratitude", "appreciation",
            "love", "kindness", "compassion", "generosity", "empathy", "tolerance", "acceptance", "forgiveness", "humility",
            "integrity", "honesty", "authenticity", "trust", "respect", "dignity", "fairness", "justice", "equality",
            "equity", "diversity", "inclusion", "solidarity", "community", "collaboration", "cooperation", "unity", "peace",
            "harmony", "balance", "well-being", "health", "resilience", "self-care", "self-improvement", "growth mindset",
            "consciousness", "awareness", "mindfulness", "meditation", "yoga", "wisdom", "knowledge", "learning", "education",
            "curiosity", "creativity", "innovation", "problem-solving", "critical thinking", "decision-making", "adaptability",
            "flexibility", "resilience", "perseverance", "determination", "grit", "optimism", "positivity", "confidence",
            "self-esteem", "self-confidence", "self-awareness", "emotional intelligence", "leadership", "communication",
            "collaboration", "teamwork", "empathy", "compassion", "kindness", "generosity", "tolerance", "acceptance",
            "forgiveness", "integrity", "honesty", "authenticity", "trust", "respect", "dignity", "fairness", "justice",
            "equality", "equity", "diversity", "inclusion", "solidarity", "community", "society", "culture", "heritage",
            "tradition", "custom", "ritual", "celebration", "festivity", "holiday", "occasion", "event", "gathering",
            "assembly", "meeting", "conference", "symposium", "convention", "exhibition", "fair", "expo", "festival",
            "concert", "performance", "showcase", "presentation", "demonstration", "workshop", "seminar", "lecture",
            "lesson", "classroom", "education", "learning", "teaching", "instruction", "pedagogy", "curriculum", "lesson plan",
            "syllabus", "assessment", "evaluation", "grading", "feedback", "revision", "improvement", "development", "progress",
            "achievement", "success", "accomplishment", "victory", "triumph", "milestone", "landmark", "breakthrough",
            "discovery", "innovation", "invention", "creation", "artistry", "craftsmanship", "mastery", "expertise",
            "skill", "talent", "aptitude", "ability", "proficiency", "competence", "capability", "knowledge", "wisdom",
            "insight", "understanding", "awareness", "consciousness", "perception", "perspective", "interpretation",
            "appreciation", "gratitude", "admiration", "respect", "esteem", "honor", "pride", "dignity", "integrity",
            "character", "morality", "ethics", "values", "principles", "virtues", "justice", "fairness", "equity",
            "equality", "diversity", "inclusion", "compassion", "empathy", "kindness", "generosity", "altruism",
            "philanthropy", "service", "volunteerism", "activism", "advocacy", "solidarity", "collaboration", "cooperation",
            "unity", "peace", "harmony", "balance", "well-being", "health", "happiness", "joy", "contentment",
            "satisfaction", "fulfillment", "serenity", "tranquility", "peace of mind", "inner peace", "mindfulness",
            "meditation", "yoga", "self-care", "self-improvement", "growth mindset", "resilience", "perseverance",
            "determination", "grit", "optimism", "positivity", "confidence", "self-esteem", "self-confidence",
            "self-awareness", "self-discovery", "self-expression", "self-realization", "authenticity", "identity",
            "individuality", "autonomy", "freedom", "liberation", "empowerment", "agency", "self-determination",
            "self-actualization", "creativity", "imagination", "innovation", "experimentation", "exploration",
            "discovery", "expression", "inspiration", "passion", "enthusiasm", "drive", "motivation", "ambition",
            "dedication", "commitment", "persistence", "discipline", "focus", "concentration", "productivity",
            "efficiency", "effectiveness", "success", "achievement", "fulfillment", "satisfaction", "happiness",
            "joy", "contentment", "gratitude", "appreciation", "love", "kindness", "compassion", "generosity",
            "empathy", "tolerance", "acceptance", "forgiveness", "humility", "integrity", "honesty", "authenticity",
            "trust", "respect", "dignity", "fairness", "justice", "equality", "equity", "diversity", "inclusion",
            "solidarity", "community", "collaboration", "cooperation", "unity", "peace", "harmony", "balance",
            "well-being", "health", "resilience", "self-care", "self-improvement", "growth mindset", "consciousness",
            "awareness", "mindfulness", "meditation", "yoga", "wisdom", "knowledge", "learning", "education",
            "curiosity", "creativity", "innovation", "problem-solving", "critical thinking", "decision-making",
            "adaptability", "flexibility", "resilience", "perseverance", "determination", "grit", "optimism",
            "positivity", "confidence", "self-esteem", "self-confidence", "self-awareness", "emotional intelligence",
            "leadership", "communication", "collaboration", "teamwork", "empathy", "compassion", "kindness",
            "generosity", "tolerance", "acceptance", "forgiveness", "integrity", "honesty", "authenticity",
            "trust", "respect", "dignity", "fairness", "justice", "equality", "equity", "diversity", "inclusion",
            "solidarity", "community", "society", "culture", "heritage", "tradition", "custom", "ritual",
            "celebration", "festivity", "holiday", "occasion", "event", "gathering", "assembly", "meeting",
            "conference", "symposium", "convention", "exhibition", "fair", "expo", "festival", "concert",
            "performance", "showcase", "presentation", "demonstration", "workshop", "seminar", "lecture",
            "lesson", "classroom", "education", "learning", "teaching", "instruction", "pedagogy", "curriculum",
            "lesson plan", "syllabus", "assessment", "evaluation", "grading", "feedback", "revision", "improvement",
            "development", "progress", "achievement", "success", "accomplishment", "victory", "triumph", "milestone",
            "landmark", "breakthrough", "discovery", "innovation", "invention", "creation", "artistry", "craftsmanship",
            "mastery", "expertise", "skill", "talent", "aptitude", "ability", "proficiency", "competence", "capability",
            "knowledge", "wisdom", "insight", "understanding", "awareness", "consciousness", "perception", "perspective",
            "interpretation", "appreciation", "gratitude", "admiration", "respect", "esteem", "honor", "pride",
            "dignity", "integrity", "character", "morality", "ethics", "values", "principles", "virtues", "justice",
            "fairness", "equity", "equality", "diversity", "inclusion", "compassion", "empathy", "kindness",
            "generosity", "altruism", "philanthropy", "service", "volunteerism", "activism", "advocacy", "solidarity",
            "collaboration", "cooperation", "unity", "peace", "harmony", "balance", "well-being", "health", "happiness",
            "joy", "contentment", "satisfaction", "fulfillment", "serenity", "tranquility", "peace of mind", "inner peace",
            "mindfulness", "meditation", "yoga", "self-care", "self-improvement", "growth mindset", "resilience",
            "perseverance", "determination", "grit", "optimism", "positivity", "confidence", "self-esteem",
            "self-confidence", "self-awareness", "self-discovery", "self-expression", "self-realization", "authenticity",
            "identity", "individuality", "autonomy", "freedom", "liberation", "empowerment", "agency", "self-determination",
            "self-actualization", "creativity", "imagination", "innovation", "experimentation", "exploration",
            "discovery", "expression", "inspiration", "passion", "enthusiasm", "drive", "motivation", "ambition",
            "dedication", "commitment", "persistence", "discipline", "focus", "concentration", "productivity",
            "efficiency", "effectiveness", "success", "achievement", "fulfillment", "satisfaction", "happiness",
            "joy", "contentment", "gratitude", "appreciation", "love", "kindness", "compassion", "generosity",
            "empathy", "tolerance", "acceptance", "forgiveness", "humility", "integrity", "honesty", "authenticity",
            "trust", "respect", "dignity", "fairness", "justice", "equality", "equity", "diversity", "inclusion",
            "solidarity", "community", "collaboration", "cooperation", "unity", "peace", "harmony", "balance",
            "well-being", "health", "resilience", "self-care", "self-improvement", "growth mindset", "consciousness",
            "awareness", "mindfulness", "meditation", "yoga", "wisdom", "knowledge", "learning", "education",
            "curiosity", "creativity", "innovation", "problem-solving", "critical thinking", "decision-making",
            "adaptability", "flexibility", "resilience", "perseverance", "determination", "grit", "optimism",
            "positivity", "confidence", "self-esteem", "self-confidence", "self-awareness", "emotional intelligence",
            "leadership", "communication", "collaboration", "teamwork", "empathy", "compassion", "kindness",
            "generosity", "tolerance", "acceptance", "forgiveness", "integrity", "honesty", "authenticity",
            "trust", "respect", "dignity", "fairness", "justice", "equality", "equity", "diversity", "inclusion",
            "solidarity", "community", "society", "culture", "heritage", "tradition", "custom", "ritual",
            "celebration", "festivity", "holiday", "occasion", "event", "gathering", "assembly", "meeting",
            "conference", "symposium", "convention", "exhibition", "fair", "expo", "festival", "concert",
            "performance", "showcase", "presentation", "demonstration", "workshop", "seminar", "lecture",
            "lesson", "classroom", "education", "learning", "teaching", "instruction", "pedagogy", "curriculum",
            "lesson plan", "syllabus", "assessment", "evaluation", "grading", "feedback", "revision", "improvement",
            "development", "progress", "achievement", "success", "accomplishment", "victory", "triumph", "milestone",
            "landmark", "breakthrough", "discovery", "innovation"
                ]
        word_array = list(set(word_array))

        for _ in range(2):
         try:
          topic = random.choice(word_array)
          response = clientapi.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt = f"Make a question of the day about {topic} and make it personal! And make these questions based towards a teenage/children audience",
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
                        prompt = f"Make a question of the day about {topic} and make it personal! And make these questions based towards a teenage/children audience",
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

