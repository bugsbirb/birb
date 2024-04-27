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

   
    @staticmethod
    @app.get("/ping")
    async def ping():
        if Api.instance.client.is_ready(): 
            discord_latency = f"{Api.instance.client.latency * 1000:.0f}ms" 
            
            return {"latency": discord_latency}
        else:
            return {"message": "Discord client is not ready"}
    
    @staticmethod
    @app.get("/stats")
    async def stats():
        if Api.instance.client.is_ready(): 
            return {"users": len(Api.instance.client.users), "guilds": len(Api.instance.client.guilds)}
        else:
            return {"message": "Discord client is not ready"}

        
        
    def run_server(self):
        uvicorn.run(app, host='0.0.0.0', port=3000)

async def setup(client: commands.Bot) -> None:
    api_instance = Api(client)  
    Api.instance = api_instance    
    await client.add_cog(Api(client))         
    api = Api(api_instance)
    threading.Thread(target=api.run_server).start()


