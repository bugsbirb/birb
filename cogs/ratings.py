import discord
from discord.ext import commands, tasks
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from discord import app_commands
from typing import Literal


conn = sqlite3.connect('rating.db')
cursor = conn.cursor()

cursor = conn.cursor()
cursor.execute("""
            CREATE TABLE IF NOT EXISTS rating (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                staff_id INTEGER,
                rating TEXT
            )
        """)
conn.commit()

class Feedback(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_group()
    async def mod(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a subcommand.")  

    @mod.command(name="feedback", description="Rate a staff on their skills.")        
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def feedback(self, ctx, staff: discord.Member, rating: Literal['1/10', '2/10', '3/10', '4/10', '5/10', '6/10', '7/10', '8/10', '9/10', '10/10'], reason: str):
        if staff == ctx.author:
            await ctx.send(f"<:X_:1140286086883586150>**{ctx.author.display_name}**, you cannot rate yourself.")
            return



        rating_value = rating.split("/")[0]

        try:
            rating_value = int(rating_value)
        except ValueError:
            await ctx.send("Invalid rating value. Please provide a number between 1 and 10.", ephemeral=True)
            return

        if not 1 <= rating_value <= 10:
            await ctx.send("Invalid rating value. Please provide a number between 1 and 10.", ephemeral=True)
            return

        user_id = ctx.author.id
        cursor.execute("SELECT id FROM rating WHERE user_id=? AND staff_id=?", (user_id, staff.id))
        existing_rating = cursor.fetchone()

        if existing_rating:
            await ctx.send(f"<:X_:1140286086883586150> **{ctx.author.display_name}**, you have already rated {staff.display_name}.")
            return

        cursor.execute("INSERT INTO rating (user_id, staff_id, rating) VALUES (?, ?, ?)", (ctx.author.id, staff.id, rating))
        conn.commit()
        
        await ctx.send(f"<:Tick:1140286044114268242> **{ctx.author.display_name}**, you've rated **{staff.display_name}** a **{rating}**")
        try:
            await staff.send(f"<:Star:1133346299668873216> **{staff.display_name}**, you've been given a **{rating}** at **{ctx.guild.name}** for **{reason}**!")
        except discord.Forbidden:
                pass        

    def get_rating_text(self, average_rating):
        if average_rating >= 8:
            return "Great"
        elif average_rating >= 5:
            return "Moderate"
        else:
            return "Critical"

    @staticmethod
    def get_channel(guild_id, channel_type):
        cursor.execute("SELECT channel_id FROM channels WHERE guild_id=? AND name=?", (guild_id, channel_type.lower()))
        result = cursor.fetchone()
        if result:
            return int(result[0])
        return None



    @mod.command(name="rating", description="View a moderators staff rating")
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def full_rating(self, ctx, staff: discord.Member):
        cursor.execute("SELECT rating FROM rating WHERE staff_id=?", (staff.id,))
        ratings = cursor.fetchall()


        if not ratings:
            await ctx.send(f"<:X_:1140286086883586150> **{ctx.author.display_name}**, there is no ratings found for **{staff.display_name}**.")
            return

        total_ratings = len(ratings)
        sum_ratings = sum(int(rating[0].split("/")[0]) for rating in ratings)
        average_rating = sum_ratings / total_ratings


        total_ratings = len(ratings)
        sum_ratings = sum(int(rating[0].split("/")[0]) for rating in ratings)
        average_rating = int(sum_ratings / total_ratings)  

        rating_text = self.get_rating_text(average_rating)

        embed = discord.Embed(title=f"{staff.display_name} Rating", description=f"* **Total Ratings:** {total_ratings}\n* **Rating:** {average_rating}/10\n* **Overall Rating:** {rating_text}", colour=0x2b2d31)
        embed.set_thumbnail(url=staff.avatar.url) 
        await ctx.send(embed=embed)
            

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Feedback(client))    