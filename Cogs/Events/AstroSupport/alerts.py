
from discord.ext import commands, tasks
import psutil
from emojis import *


class Alerts(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.last_alert = {}
        self.check_alerts.start()
 
    @tasks.loop(minutes=60)
    async def check_alerts(self):
        
        if self.last_alert == 'Alert Ram':
            return
        if self.last_alert == 'Alert Ram 2':
            return        
        if self.last_alert == 'Alert CPU':
            return
        owner = await self.client.fetch_user(795743076520820776)
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        if cpu > 80:
            await owner.send(f"{no} High CPU usage detected: {cpu}%")
            self.last_alert = 'Alert CPU'

        elif ram > 600:
            if self.last_alert == 'Alert Ram':
             return            
            await owner.send(f"{no} High RAM usage detected: {ram}%\n{psutil.virtual_memory()}")
            self.last_alert = 'Alert Sent'

        elif ram > 1000:
            await owner.send(f"{no} Very high RAM usage detected: {ram}%\n{psutil.virtual_memory()}")
            self.last_alert = 'Alert Ram2'  
        else:
            print(f'Ram is fine {ram}%')    

    
     





async def setup(client: commands.Bot) -> None:
    await client.add_cog(Alerts(client))   
