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
from emojis import * 
import os
from dotenv import load_dotenv
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
stafffeedback = db['feedback']
feedbackch = db['Staff Feedback Channel']
scollection = db['staffrole']
class Feedback(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_group()    
    async def staff(self, ctx):
        pass

    @staff.command(description="Rate a staff membr")
    async def feedback(self, ctx, staff: discord.Member, rating: Literal['1/10', '2/10', '3/10', '4/10', '5/10', '6/10', '7/10', '8/10', '9/10', '10/10'], feedback: str):
       existing_feedback = stafffeedback.find_one({'guild_id': ctx.guild.id, 'staff': staff.id, 'author': ctx.author.id})
       if staff == ctx.author:
            await ctx.send(f"{no} **{ctx.author.display_name}**, you cannot rate yourself.")
            return
       staff_role_data = scollection.find_one({'guild_id': ctx.guild.id})
       staff_role_id = staff_role_data['staffrole']  


       has_staff_role = discord.utils.get(staff.roles, id=staff_role_id) is not None

       if not has_staff_role:
        await ctx.send(f"{no} **{ctx.author.display_name}**, you can only rate staff members.")
        return

       if existing_feedback:
        await ctx.send(f"{no} You have already rated this staff member. You cannot rate them again.")
       else:
        await ctx.send(f"{tick} You've rated **@{staff.display_name}** {rating}!")
       rating_value = rating.split("/")[0]
       feedbackdata = {
        'guild_id': ctx.guild.id,
        'rating': rating_value,
        'staff': staff.id,
        'author': ctx.author.id
       }
       stafffeedback.insert_one(feedbackdata)
       data = feedbackch.find_one({'guild_id': ctx.guild.id})
       if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
            embed = discord.Embed(title="Staff Feedback", description=f"* **Staff:** {staff.mention}\n* **Rating:** {rating}\n* **Feedback:** {feedback}", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=staff.display_avatar)
            embed.set_author(name=staff.display_name, icon_url=staff.display_avatar)            
            await channel.send(f"{staff.mention}",embed=embed)

         else:   
            pass

    @staff.command(description="View a staff members rating")
    async def rating(self, ctx, staff: discord.Member, scope: Literal["global", "server"]):
     if scope == "global":
        staff_ratings = list(stafffeedback.find({'staff': staff.id}))
     elif scope == "server":
        staff_ratings = list(stafffeedback.find({'guild_id': ctx.guild.id, 'staff': staff.id}))
     else:
        await ctx.send(f"{no} Invalid scope. Please use 'global' or 'server'.")
        return

     total_ratings = len(staff_ratings)

     if total_ratings == 0:
        await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find any rating for this user.")
        return

     sum_ratings = sum(int(rating['rating'].split('/')[0]) for rating in staff_ratings)
     average_rating = int(sum_ratings / total_ratings) 

     if total_ratings > 0:
        last_rating = staff_ratings[-1]['rating']
     else:
        last_rating = "N/A"

     rating_text = get_rating_text(average_rating)

     embed = discord.Embed(title="", description=f"* **Average Rating**: {average_rating}/10\n* **Last Rating**: {last_rating}/10\n* **Overall**: {rating_text}", color=discord.Color.dark_embed())
     embed.set_thumbnail(url=staff.display_avatar)
     embed.set_author(name=staff.display_name, icon_url=staff.display_avatar)
     await ctx.send(embed=embed)

def get_rating_text(average_rating):
    if average_rating >= 8:
        return "Great"
    elif average_rating >= 5:
        return "Moderate"
    else:
        return "Critical"

async def setup(client: commands.Bot) -> None:

    await client.add_cog(Feedback(client))                