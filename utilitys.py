import discord
from typing import Literal
import datetime
from datetime import timedelta
import asyncio
from discord import app_commands
from discord.ext import commands
import pytz
import pymongo
from pymongo import MongoClient
import Paginator
class utils(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command()
    @commands.is_owner()    
    async def operational(self, ctx):
        embed = discord.Embed(title="Quota - Operational", description="Quota is currently operational and online.", color=discord.Color.brand_green())
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1139907646963597423/1148682178205589534/585894182128975914.png")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()    
    async def unstable(self, ctx):
        embed = discord.Embed(title="Quota - Unstable", description="Quota is currently unstable.", color=discord.Color.orange())
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1139907646963597423/1148682557618147391/1140809567865933824.png")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()    
    async def downtime(self, ctx):
        embed = discord.Embed(title="Quota - Offline", description="Quota is currently experiencing downtime.", color=discord.Color.red())
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1139907646963597423/1148682781321330789/1140809593598005358.png")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def restarting(self, ctx):
        embed = discord.Embed(title="Quota - Restarting", description="Quota is currently restarting.", color=discord.Color.orange())
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1139907646963597423/1148682557618147391/1140809567865933824.png")
        await ctx.send(embed=embed)



async def setup(client: commands.Bot) -> None:
    await client.add_cog(utils(client))   