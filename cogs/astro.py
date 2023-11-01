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
import os
from dotenv import load_dotenv
from emojis import * 
MONGO_URL = os.getenv('MONGO_URL')
mongo = MongoClient(MONGO_URL)
db = mongo['astro']
badges = db['User Badges']


class HelpdeskDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='What is Astro Birb?', emoji='<:arrow:1166529434493386823>'),
            discord.SelectOption(label="What is Quota?", emoji="<:arrow:1166529434493386823>"),
            discord.SelectOption(label="How do I become staff here?", emoji="<:arrow:1166529434493386823>"),


        
            
        ]
        super().__init__(placeholder='Helpdesk', min_values=1, max_values=1, options=options, custom_id='persitent:HelpDeskDropwon')
    async def callback(self, interaction: discord.Interaction):

        selected = self.values[0] 
        if selected == 'What is Astro Birb?':
            embed = discord.Embed(title="<:Tip:1167083259444875264> What is Astro Birb?", description="> Astro Birb is a versatile bot designed for streamlining punishment and staff management tasks. It boasts a wide array of features, including but not limited to infractions, promotions, modmail, moderations, tags. What sets its infraction system apart is its comprehensive logging functionality, allowing you to effortlessly access and review the infraction history of your staff members with a simple command: /infractions {user}.")
        elif selected == 'What is Quota?':    
            embed = discord.Embed(title="<:Tip:1167083259444875264> What is Quota?", description="Quota is a Discord moderation bot designed to manage message quotas for staff members, ensuring their activity levels are met and helping identify potential areas for improvement or necessary punitive actions.")
        elif selected == 'How do I become staff here?':
            embed = discord.Embed(title="<:Tip:1167083259444875264> How do I become staff?", description="Currently support & QA is handpicked meaning you have to show your activity in the support server by either answering support forums or activily talking in the server.")

        embed.color = discord.Color.dark_embed()    
        await interaction.response.send_message(embed=embed, ephemeral=True)
            

class Helpdesk(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpdeskDropdown())

class management(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command()
    @commands.is_owner()    
    async def addbadge(self, ctx, user: discord.Member, *, badge):
        badge = {
            'user_id': user.id,
            'badge': badge
        }
        badges.insert_one(badge)  
        await ctx.send(f"{tick} added **`{badge}`** to **@{user.display_name}**")

    @commands.command()
    @commands.is_owner()
    async def removebadge(self, ctx, user: discord.Member, *, badge):
        badge = {
            'user_id': user.id,
            'badge': badge
        }
        badges.delete_one(badge)  
        await ctx.send(f"{tick} removed **`{badge}`** to **@{user.display_name}**")
  
    @commands.command()
    @commands.is_owner()
    async def helpdesk(self, ctx):
        banner = discord.Embed(title="", color=discord.Color.dark_embed())
        banner.set_image(url="https://cdn.discordapp.com/attachments/1104358043598200882/1169328494044528710/006_2.png?ex=65550106&is=65428c06&hm=392ce6de8fa7f60763c87ac8f2ee9cbad49ed5603ea6555d6be6da36fc8ce6ea&")

        main = discord.Embed(color=discord.Color.dark_embed(), title="<:forum:1162134180218556497> Astro Support", description="> Welcome to the support server for Astro Birb & Quota! These bots are useful and productive for staff management & message quotas.")
        main.set_thumbnail(url="https://cdn.discordapp.com/icons/1092976553752789054/f9f6b1924078f9487bda623e7f6d6d71.png?size=512")
        main.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")
        view = Helpdesk()
        await ctx.send(embeds=(banner, main), view=view)




async def setup(client: commands.Bot) -> None:
    await client.add_cog(management(client))     
