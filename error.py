import discord
import discord
from discord.ext import commands
from typing import Literal
import datetime
from datetime import timedelta
import asyncio
from discord import app_commands
from discord.ext import commands, tasks
import pytz
from pymongo import MongoClient
import platform
import random
from discord.ui import Button
import string
from emojis import *
import os
MONGO_URL = os.getenv('MONGO_URL')
astro = MongoClient(MONGO_URL)
db = astro['astro']
errors = db['Errors']
class errorcog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener(name="on_command_error")
    async def appcommanderror(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return 

        error_id = ''.join(random.choices(string.digits, k=6))
        embed = discord.Embed(title=f"<:crossX:1140623638207397939> An Error Occured", description=f"**Error ID:** `{error_id}`", color=discord.Color.brand_red())
        view = Support()
        await ctx.send(embed=embed, view=view)
        errors.insert_one({'error_id': error_id, 'error_message': str(error)})


    @commands.command()
    @commands.is_owner()
    async def sentry(self, ctx, error: str):
        errorsearch = errors.find_one({'error_id': error})
        if errorsearch:
            errormessage = errorsearch['error_message']
            embed = discord.Embed(title=f"Error | {error}", description=f"```py\n{errormessage}```", color=discord.Color.dark_embed())
            await ctx.send(embed=embed)
        else:    
            await ctx.send(f"{no} **Error** couldn't be found.")

class Support(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = f'https://discord.gg/DhWdgfh3hN'
        self.add_item(discord.ui.Button(label='Get Support', url=url, style=discord.ButtonStyle.blurple))

async def setup(client: commands.Bot) -> None:
    await client.add_cog(errorcog(client))     
