import os
import uvicorn
from fastapi import FastAPI, Security, Depends
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import threading
from fastapi.security.api_key import APIKeyHeader












MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
infractions_collection = db['infractions']



app = FastAPI()




class Api(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app.get("/checkguild/{guild_id}")
    async def check_guild(guild_id):
            guild = Api.instance.client.get_guild(int(guild_id))
            if guild is not None:
                return {"message": True}
            else:
                return {"message": False}
            

        
    
   
    @staticmethod
    @app.get("/ping")
    async def ping():
            discord_latency = f"{Api.instance.client.latency * 1000:.0f}ms" 
            if not discord_latency:
                return {"message": "Discord client is not ready"}
            
            return {"latency": discord_latency}

    
    @staticmethod
    @app.get("/stats")
    async def stats(): 
            return {"users": len(Api.instance.client.users), "guilds": len(Api.instance.client.guilds)}
      

        
        
    def run_server(self):
        uvicorn.run(app, host='0.0.0.0', port=3000)

async def setup(client: commands.Bot) -> None:
    api_instance = Api(client)  
    Api.instance = api_instance    
    await client.add_cog(Api(client))         
    api = Api(api_instance)
    threading.Thread(target=api.run_server).start()


