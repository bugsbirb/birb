import discord
from discord.ext import commands
import asyncio
from pymongo import MongoClient
from emojis import *

import os
from dotenv import load_dotenv
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
forumsconfig = db['Forum Configuration']
modules = db['Modules']

class ForumCreaton(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        guild_id = thread.guild.id
        config_data = forumsconfig.find_one({"guild_id": guild_id, "channel_id": thread.parent_id})
        if not config_data or "channel_id" not in config_data:
         return

        if thread.guild.id != guild_id:
            return
        if thread.parent_id != config_data['channel_id']:
            return
        await asyncio.sleep(1)
        if config_data:
          color_str = config_data.get("color", "2b2d31") 
          color = discord.Color(int(color_str, 16))
          embed = discord.Embed(title=config_data["title"], description=config_data["description"], color=color)
          thumbnail_url = config_data['thumbnail']
          image_urll = config_data['image']
          if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
          if image_urll:
                embed.set_image(url=image_urll)

          role_ids = config_data['role']
          role_id = int(role_ids) if role_ids else None

          role = discord.utils.get(thread.guild.roles, id=role_id)


          mention = f"<@&{role_id}>" if role else ""
          msg = await thread.send(content=f"{mention}", embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
          await msg.pin()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ForumCreaton(client))   