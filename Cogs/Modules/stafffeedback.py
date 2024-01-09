import discord
from discord.ext import commands
from typing import Literal
from datetime import timedelta
from discord.ext import commands
from pymongo import MongoClient
from emojis import * 
from datetime import datetime
import os
from dotenv import load_dotenv
import Paginator
from permissions import *
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
stafffeedback = db['feedback']
feedbackch = db['Staff Feedback Channel']
scollection = db['staffrole']
modules = db['Modules']
class Feedback(commands.Cog):
    def __init__(self, client):
        self.client = client



    async def staffcheck(self, ctx, staff):
     filter = {
        'guild_id': ctx.guild.id
    }
     staff_data = scollection.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']

        if not isinstance(staff_role_ids, list):
            staff_role_ids = [staff_role_ids]

        staff_roles = [role.id for role in staff.roles]
        if any(role_id in staff_roles for role_id in staff_role_ids):
            return True

     return False

    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Feedback'] == True:   
        return True


    @commands.hybrid_group(description="Staff Feedback")
    async def feedback(self, ctx):
       pass
    

    @feedback.command(description="Remove feedback from a staff member")
    async def remove(self, ctx, id: int):
       if not await has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return          
       result = stafffeedback.find_one({'feedbackid': id, 'guild_id': ctx.guild.id})
       if result is None:
        await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find any feedback with that ID.")
        return
       
       stafffeedback.delete_one({'feedbackid': id, 'guild_id': ctx.guild.id})
       await ctx.send(f"{tick} **{ctx.author.display_name}**, I have removed the feedback.")


   
       

    @feedback.command(description="Rate a staff member", name="give")
    async def feedback2(self, ctx, staff: discord.Member, rating: Literal['1/10', '2/10', '3/10', '4/10', '5/10', '6/10', '7/10', '8/10', '9/10', '10/10'], feedback: str):
       existing_feedback = stafffeedback.find_one({'guild_id': ctx.guild.id, 'staff': staff.id, 'author': ctx.author.id})
       if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return          
       if staff == ctx.author:
            await ctx.send(f"{no} **{ctx.author.display_name}**, you cannot rate yourself.")
            return
       staff_role_data = scollection.find_one({'guild_id': ctx.guild.id})
       staff_role_id = staff_role_data['staffrole']  


       has_staff_role = await self.staffcheck(ctx, staff)

       if not has_staff_role:
        await ctx.send(f"{no} **{ctx.author.display_name}**, you can only rate staff members.")
        return

       if existing_feedback:
        await ctx.send(f"{no} You have already rated this staff member. You cannot rate them again.")
       else:
        await ctx.send(f"{tick} You've rated **@{staff.display_name}** {rating}!")
       rating_value = rating.split("/")[0]
       feedbackid = stafffeedback.count_documents({}) + 1
       feedbackdata = {
        'guild_id': ctx.guild.id,
        'rating': rating_value,
        'staff': staff.id,
        'author': ctx.author.id,
        'feedback': feedback,

        'date': datetime.now().timestamp(),
        'feedbackid': feedbackid
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
            embed.set_footer(text=f"Feedback ID: {feedbackid}")           
            try:
             await channel.send(f"{staff.mention}",embed=embed)
            except discord.Forbidden: 
               await ctx.send(f"{no} I don't have permission to view this channel.")
               return

         else:   
            pass

    @feedback.command(description="View a staff members rating")
    async def ratings(self, ctx, staff: discord.Member, scope: Literal["global", "server"]):
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
     view = ViewRatings(staff_ratings, staff, ctx, scope, ctx.author)
     await ctx.send(embed=embed, view=view)


class ViewRatings(discord.ui.View):
    def __init__(self, ratings, staff, ctx, scope, author):
        super().__init__(timeout=120)
        self.ratings = ratings
        self.staff = staff
        self.ctx = ctx
        self.scope = scope
        self.author = author





    @discord.ui.button(label='View Ratings', style=discord.ButtonStyle.grey)
    async def Ratings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        if self.scope == "global":
            staff_ratings = list(stafffeedback.find({'staff': self.staff.id}))
        elif self.scope == "server":
            staff_ratings = list(stafffeedback.find({'guild_id': interaction.guild.id, 'staff': self.staff.id}))
        embeds = []
        for idx, rating in enumerate(staff_ratings):
            if idx % 9 == 0: 
                embed = discord.Embed(title="Staff Ratings", color=discord.Color.dark_theme())
                embed.set_thumbnail(url=self.staff.display_avatar)
                embed.set_author(name=self.staff.display_name, icon_url=self.staff.display_avatar)
                embed.set_footer(text="If the feedback ID is invalid and you want to delete it contact support.", icon_url="https://media.discordapp.net/ephemeral-attachments/1129817866766663770/1194412760675651695/1192867080408682526.png?ex=65b04291&is=659dcd91&hm=411b4ce856699b19d6190f69b4692476f72673933e3828b71c83a6397a0ec09b&=&format=webp&quality=lossless")

            date = rating.get('date', 'N/A')
            Id = rating.get('feedbackid', 'N/A')
            feedback = rating.get('feedback', 'Non Given')


            if date == 'N/A':
                date_str = "N/A"
            else:
               date_str = datetime.utcfromtimestamp(date).strftime('%d/%m/%Y')

            embed.add_field(
    name=f"{rating['rating']}/10",
    value=f"**Date:** {date_str}\n**Feedback ID:** {Id}\n**Feedback:** {feedback}",
    inline=False
)

            if (idx + 1) % 9 == 0 or idx == len(staff_ratings) - 1:  
                embeds.append(embed)

        PreviousButton = discord.ui.Button(label="<")
        NextButton = discord.ui.Button(label=">")
        FirstPageButton = discord.ui.Button(label="<<")
        LastPageButton = discord.ui.Button(label=">>")
        InitialPage = 0
        timeout = 42069

        paginator = Paginator.Simple(
            PreviousButton=PreviousButton,
            NextButton=NextButton,
            FirstEmbedButton=FirstPageButton,
            LastEmbedButton=LastPageButton,
            InitialPage=InitialPage,
            timeout=timeout
        )

        await paginator.start(self.ctx, pages=embeds)
        button.disabled = True
        await interaction.response.edit_message(view=self)
        

                  

              


def get_rating_text(average_rating):
    if average_rating >= 8:
        return "Great"
    elif average_rating >= 5:
        return "Moderate"
    else:
        return "Critical"

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Feedback(client))        