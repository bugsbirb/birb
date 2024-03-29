import discord
from discord.ext import commands
from typing import Literal
from discord.ext import commands
from emojis import * 
from datetime import datetime
import os
import Paginator
from permissions import *

from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
stafffeedback = db['feedback']
feedbackch = db['Staff Feedback Channel']
scollection = db['staffrole']
modules = db['Modules']
options = db['module options']
class Feedback(commands.Cog):
    def __init__(self, client):
        self.client = client



    async def staffcheck(self, ctx: commands.Context, staff):
     filter = {
        'guild_id': ctx.guild.id
    }
     staff_data = await scollection.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']

        if not isinstance(staff_role_ids, list):
            staff_role_ids = [staff_role_ids]

        staff_roles = [role.id for role in staff.roles]
        if any(role_id in staff_roles for role_id in staff_role_ids):
            return True

     return False

    async def modulecheck(self, ctx: commands.Context): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Feedback'] == True:   
        return True


    @commands.hybrid_group(description="Staff Feedback")
    async def feedback(self, ctx: commands.Context):
       pass
    

    @feedback.command(description="Remove feedback from a staff member")
    @app_commands.describe(id="The ID of the feedback you want to remove.")
    async def remove(self, ctx: commands.Context, id: int):
       if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the feedback module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return               
       if not await has_admin_role(ctx):
        
         return          
       result = await stafffeedback.find_one({'feedbackid': id, 'guild_id': ctx.guild.id})
       if result is None:
        await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find any feedback with that ID.")
        return
       
       await stafffeedback.delete_one({'feedbackid': id, 'guild_id': ctx.guild.id})
       await ctx.send(f"{tick} **{ctx.author.display_name}**, I have removed the feedback.", allowed_mentions=discord.AllowedMentions.none())


   
       

    @feedback.command(description="Rate a staff member", name="give")
    @app_commands.describe(staff="The staff member you want to rate.", rating="The rating you want to give (1-10).", feedback="The feedback you want to give.")
    async def feedback2(self, ctx: commands.Context, staff: discord.Member, rating: Literal['1/10', '2/10', '3/10', '4/10', '5/10', '6/10', '7/10', '8/10', '9/10', '10/10'], feedback: app_commands.Range[str, 1, 2000]):
       await ctx.defer(ephemeral=True)
       existing_feedback = await stafffeedback.find_one({'guild_id': ctx.guild.id, 'staff': staff.id, 'author': ctx.author.id})
       optionresult = await options.find_one({'guild_id': ctx.guild.id})
       if staff is None:
        await ctx.send(f"{no} **{ctx.author.display_name}**, please provide a staff member.", allowed_mentions=discord.AllowedMentions.none())
        return       
       if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the feedback module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return          
       if staff == ctx.author:
            await ctx.send(f"{no} **{ctx.author.display_name}**, you cannot rate yourself.", allowed_mentions=discord.AllowedMentions.none())
            return



       has_staff_role = await self.staffcheck(ctx, staff)

       if not has_staff_role:
        await ctx.send(f"{no} **{ctx.author.display_name}**, you can only rate staff members.", allowed_mentions=discord.AllowedMentions.none())
        return
       if optionresult:
        if optionresult.get('multiplefeedback', False) == False:
         
         if existing_feedback:
          await ctx.send(f"{no} **{ctx.author.display_name},** You have already rated this staff member.", allowed_mentions=discord.AllowedMentions.none())
          return
       else:
         if existing_feedback:
          await ctx.send(f"{no} **{ctx.author.display_name},** You have already rated this staff member.", allowed_mentions=discord.AllowedMentions.none())
          return            
       
       rating_value = rating.split("/")[0]
       feedbackid = await stafffeedback.count_documents({}) + 1
       feedbackdata = {
        'guild_id': ctx.guild.id,
        'rating': rating_value,
        'staff': staff.id,
        'author': ctx.author.id,
        'feedback': feedback,

        'date': datetime.now().timestamp(),
        'feedbackid': feedbackid
       }
       await stafffeedback.insert_one(feedbackdata)
       await ctx.send(f"{tick} You've rated **@{staff.display_name}** {rating}!", allowed_mentions=discord.AllowedMentions.none())
       data = await feedbackch.find_one({'guild_id': ctx.guild.id})
       if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
            embed = discord.Embed(title="Staff Feedback", description=f"* **Staff:** {staff.mention}\n* **Rating:** {rating}\n* **Feedback:** {feedback}", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=staff.display_avatar)
            embed.set_author(name=f"From {ctx.author.display_name}", icon_url=ctx.author.display_avatar) 
            embed.set_footer(text=f"Feedback ID: {feedbackid}")           
            try:
             await channel.send(f"{staff.mention}",embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False))
            except discord.Forbidden: 
               await ctx.send(f"{no} I don't have permission to view this channel.", allowed_mentions=discord.AllowedMentions.none())
               return

         else:   
            pass

    @feedback.command(description="View a staff members rating")
    @app_commands.describe(staff = 'The staff to view rating for', scope = "The scope of the rating to view")
    async def ratings(self, ctx: commands.Context, staff: discord.Member, scope: Literal["global", "server"]):
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the feedback module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return               
     
     if scope == "global":
        staff_ratings = stafffeedback.find({'staff': staff.id}).to_list(length=None)
        total_ratings = await stafffeedback.count_documents({'staff': staff.id})
     elif scope == "server":
        staff_ratings = stafffeedback.find({'guild_id': ctx.guild.id, 'staff': staff.id}).to_list(length=None)
        total_ratings = await stafffeedback.count_documents({'guild_id': ctx.guild.id, 'staff': staff.id})
     else:
        await ctx.send(f"{no} Invalid scope. Please use 'global' or 'server'.")
        return

     
     if total_ratings == 0:
        await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find any rating for this user.", allowed_mentions=discord.AllowedMentions.none())
        return
     staff_ratings = await staff_ratings
     sum_ratings = sum(int(rating['rating'].split('/')[0]) for rating in staff_ratings)
     average_rating = int(sum_ratings / total_ratings) 

     if total_ratings > 0:
        last_rating = staff_ratings[-1]['rating']
     else:
        last_rating = "N/A"

     rating_text = get_rating_text(average_rating)

     embed = discord.Embed(title=f"", description=f"* **Average Rating**: {average_rating}/10\n* **Last Rating**: {last_rating}/10\n* **Overall**: {rating_text}", color=discord.Color.dark_embed())
     embed.set_thumbnail(url=staff.display_avatar)
     embed.set_author(name=f"{(scope).capitalize()} Ratings", icon_url=staff.display_avatar)
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





    @discord.ui.button(label='View Ratings', style=discord.ButtonStyle.grey, emoji="<:Rate:1162135093129785364>")
    async def Ratings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        if self.scope == "global":
            staff_ratings = stafffeedback.find({'staff': self.staff.id}).to_list(length=None)
        elif self.scope == "server":
            staff_ratings = stafffeedback.find({'guild_id': interaction.guild.id, 'staff': self.staff.id}).to_list(length=None)
        embeds = []
        staff_ratings = await staff_ratings
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
    name=f"{star} {rating['rating']}/10",
    value=f"{arrow}**Date:** {date_str}\n{arrow}**Feedback ID:** {Id}\n{arrow}**Feedback:** {feedback}",
    inline=False
)

            if (idx + 1) % 9 == 0 or idx == len(staff_ratings) - 1:  
                embeds.append(embed)

        PreviousButton = discord.ui.Button(emoji="<:chevronleft:1220806425140531321>")
        NextButton = discord.ui.Button(emoji="<:chevronright:1220806430010118175>")
        FirstPageButton = discord.ui.Button(emoji="<:chevronsleft:1220806428726661130>")
        LastPageButton = discord.ui.Button(emoji="<:chevronsright:1220806426583371866>")
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