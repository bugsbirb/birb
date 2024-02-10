import discord
from discord.ext import commands
import pymongo
import Paginator
from emojis import *
import os
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
mongo = AsyncIOMotorClient(MONGO_URL)

from permissions import has_admin_role, has_staff_role

client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
lcollection = db['LOA Role']
arole = db['adminrole']
modules = db['Modules']


class SetMessages(discord.ui.Modal, title='Set Message Count'):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    message_count = discord.ui.TextInput(
        label='Message Count',
        placeholder='Set the message count for this user',
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            message_count_value = int(self.message_count.value)
        except ValueError:
            await interaction.response.send_message(f'{no} Invalid input. Please enter a valid number for the message count.', ephemeral=True)
            return

        guild_id = interaction.guild.id

        filter = {'guild_id': guild_id, 'user_id': self.user_id}
        update_data = {'$set': {'message_count': message_count_value}}
        await mccollection.update_one(filter, update_data, upsert=True)
        await interaction.response.edit_message(content=f'{tick} **{interaction.user.display_name}**, I have set the users message count as `{message_count_value}`.', embed=None, view=None)

class StaffManage(discord.ui.View):
    def __init__(self, staff_id, author):
        super().__init__(timeout=None)
        self.value = None
        self.staff_id = staff_id        
        self.author = author

    @discord.ui.button(label='Reset Messages', style=discord.ButtonStyle.grey)
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
       staff_id = self.staff_id
       if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                 
       filter = {'guild_id': interaction.guild.id, 'user_id': staff_id}
       update = {'$set': {'message_count': 0}}
       await mccollection.update_one(filter, update)

       await interaction.response.edit_message(content=f'**{tick} {interaction.user.display_name}**, I have resetted the staffs message count.', embed=None, view=None)


    @discord.ui.button(label='Set Messages', style=discord.ButtonStyle.grey)
    async def set(self, interaction: discord.Interaction, button: discord.ui.Button):
       if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
       await interaction.response.send_modal(SetMessages(self.staff_id))      



dbq = mongo['quotab']
mccollection = dbq["messages"]
message_quota_collection = dbq["message_quota"]



class quota(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client







    async def modulecheck(self, ctx): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Quota'] == True:   
        return True



    @commands.hybrid_group(name="staff")
    async def staff(self, ctx):
        return

    @commands.command()
    async def staffcommand(self, ctx):
        if await has_staff_role(ctx):
            await ctx.send("Worked")
        else:
            await ctx.send("You don't have the staff role.")



    @commands.command()
    async def checkadmin(self, ctx):
        if await has_admin_role(ctx):
            await ctx.send("You have an admin role!")
        else:
            await ctx.send("You don't have an admin role.")


            


    @staff.command(name="manage", description="Manage your staffs messages.")    
    async def manage(self, ctx, staff: discord.Member):

     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return   
     if not await has_admin_role(ctx):
            return                      
     mccollection = dbq["messages"]
     message_data = await mccollection.find_one({'guild_id': ctx.guild.id, 'user_id': staff.id})
    
     if message_data:
        message_count = message_data.get('message_count', 0)
     else:
        message_count = 0

     view = StaffManage(staff.id, ctx.author)

     embed = discord.Embed(
        title=f"{staff.display_name}",
        description=f"* **Messages:** {message_count}",
        color=discord.Color.dark_embed()
    )
     embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
     embed.set_thumbnail(url=staff.display_avatar)
    
     await ctx.send(embed=embed, view=view)


    @commands.hybrid_group(name="leaderboard")
    async def leader(self, ctx):
        return

    @leader.command(name="reset", description="Reset the message quota leaderboard")
    async def reset_staff_message_counts(self, ctx):


        await ctx.defer()
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return                    
        if not await has_admin_role(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`")
            return  
            
        mccollection = dbq["messages"]
        await mccollection.delete_many({'guild_id': ctx.guild.id})
        await ctx.send(f"{tick} **{ctx.author.display_name}**, I've reset the entire staff team's message count.")                    
        try:
                owner = ctx.guild.owner
                await owner.send(f"{tick} **{ctx.guild.owner.display_name}**, `{ctx.author.display_name}` has reset the staff leaderboard.")
        except Exception as e:
                 await ctx.send(f"{tick} **{ctx.guild.owner.display_name}**, `{ctx.author.display_name}` has reset the staff leaderboard.")


    @staff.command(name="messages", description="Display the amount the message count of a staff member.")
    async def messages(self, ctx, staff: discord.Member):

     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return                    
     if not await has_staff_role(ctx):
        return        
     message_data = await mccollection.find_one({'guild_id': ctx.guild.id, 'user_id': staff.id})
     if staff.id:

      if message_data:
        message_count = message_data.get('message_count', 0)
      else:
        message_count = 0        

     if message_data:
        message_count = message_data.get('message_count', 0)
        await ctx.send(f"<:Messages:1148610048151523339> **{staff.display_name}**, has sent {message_count} messages.")        
     else:  
          if staff is ctx.author:
           await ctx.send(f"{no} **{ctx.author.display_name}**, couldn't find any messages from you or your not staff.")
          else: 
            await ctx.send(f"{no} **{ctx.author.display_name}**, couldn't find any messages from this user or they aren't staff.")


    @staff.command(description="View the staff message leaderboard to see if anyone has passed their quota")
    async def leaderboard(self, ctx):
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
            return

        await ctx.defer()
        if not await has_staff_role(ctx):
            return

        filter = {'guild_id': ctx.guild.id}
        cursor = mccollection.find(filter).sort("message_count", pymongo.DESCENDING).limit(400)

        user_data_list = await cursor.to_list(length=400)

        pages = []
        rank = 1
        leaderboard_description = ""

        for user_data in user_data_list:
            user_id = user_data['user_id']
            message_count = user_data['message_count']
            member = ctx.guild.get_member(user_id)
            loa_role_data = await lcollection.find_one({'guild_id': ctx.guild.id})

            if member:
                message_quota_result = await message_quota_collection.find_one({'guild_id': ctx.guild.id})

                if message_quota_result:
                    message_quota = message_quota_result.get('message_quota', 100)
                else:
                    message_quota = 100

                if loa_role_data:
                    loa_role_id = loa_role_data.get('staffrole')
                    has_loa_role = any(role.id == loa_role_id for role in member.roles)
                else:
                    has_loa_role = False

                if message_count >= message_quota:
                    emoji = "`LOA`" if has_loa_role else "<:Confirmed:1122636234255253545>"
                else:
                    emoji = "`LOA`" if has_loa_role else "<:Cancelled:1122637466353008810>"

                leaderboard_description += f"* `{rank}` • {member.display_name} • {message_count} messages\n> **Passed:** {emoji}\n\n"
                rank += 1

                if rank % 10 == 0:
                    embed = discord.Embed(
                        title=f"Staff Leaderboard",
                        description=leaderboard_description,
                        color=discord.Color.dark_embed()
                    )
                    embed.set_thumbnail(url=ctx.guild.icon)
                    embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
                    pages.append(embed)
                    leaderboard_description = ""

        if rank == 1:
            leaderboard_description += "No message data."

        if leaderboard_description:
            embed = discord.Embed(
                title=f"Staff Leaderboard",
                description=leaderboard_description,
                color=discord.Color.dark_embed()
            )
            embed.set_thumbnail(url=ctx.guild.icon)
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            pages.append(embed)

        if not pages:
            pages.append(discord.Embed(title="Staff Leaderboard", description="No message data.", color=discord.Color.dark_embed()))

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

        await paginator.start(ctx, pages=pages)




async def setup(client: commands.Bot) -> None:
    await client.add_cog(quota(client))        
