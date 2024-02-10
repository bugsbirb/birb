from discord.ext import commands, tasks
from emojis import *
import topgg




class Topgg(commands.Cog):
    def __init__(self, client):
        self.client = client

        dbl_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjExMTMyNDU1Njk0OTA2MTY0MDAiLCJib3QiOnRydWUsImlhdCI6MTcwMzk1NTE5Mn0.gy2qbNrCCAmi84QPw9UYqSdlQMEaBnumVv7b1qtfEo4"
        self.client.topggpy = topgg.DBLClient(self.client, dbl_token)
        self.update_stats.start()



    @tasks.loop(minutes=30)
    async def update_stats(self):
      try:
        await self.client.topggpy.post_guild_count()
        print(f"Posted server count ({self.client.topggpy.guild_count})")
      except Exception as e:
        print(f"Failed to post server count\n{e.__class__.__name__}: {e}")





async def setup(client: commands.Bot) -> None:
    await client.add_cog(Topgg(client))   

