import discord
from discord.ext import commands
import datetime
from emojis import *
import string
import os
import random
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
errors = db['errors']

class On_error(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{no} **{ctx.author.display_name}**, you are missing a requirement.")
            return
        if isinstance(error, commands.BadArgument):
            return
        if ctx.guild is None:
            return
        error_id = ''.join(random.choices(string.digits, k=24))
        error_id = f"error-{error_id}"
        await errors.insert_one({'error_id': error_id, 'error': str(error), 'timestamp': datetime.datetime.now(), 'guild_id': ctx.guild.id})
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Contact Support", style=discord.ButtonStyle.link, url="https://discord.gg/DhWdgfh3hN"))
        embed = discord.Embed(title="<:x21:1214614676772626522> Command Error", description=f"Error ID: `{error_id}`", color=discord.Color.brand_red())
        await ctx.send(embed=embed, view=view)
        return
        



async def setup(client: commands.Bot) -> None:
    await client.add_cog(On_error(client))     
