import discord
from discord import app_commands
from discord.ext import commands
import pymongo
import Paginator
from emojis import *
import os
from discord.ext import tasks
from datetime import datetime, timedelta
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
staffdb = db['staff database']
Customisation = db['Customisation']
StaffPanelLabel = db['StaffPanel Label']
autoactivity = db['auto activity']
infchannel = db['infraction channel']
consent = db['consent']

modules = db['Modules']
Customisation = db['Customisation']
infractiontypes = db['infractiontypes']
infractiontypeactions = db['infractiontypeactions']
collection = db['infractions']
options = db['module options']

environment = os.getenv("ENVIRONMENT")
guildid = os.getenv("CUSTOM_GUILD")

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


class AddMessage(discord.ui.Modal, title='Add Messages'):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id



    message_count = discord.ui.TextInput(
        label='Added Message Count',
        placeholder='Will add onto their current message count',
    )

    async def on_submit(self, interaction: discord.Interaction):
        result = await mccollection.find_one({'guild_id': interaction.guild.id, 'user_id': self.user_id})
        message_count_value = int(self.message_count.value)
        guild_id = interaction.guild.id
        if result:
            message_count = int(result['message_count']) + message_count_value
            filter = {'guild_id': guild_id, 'user_id': self.user_id}
            await mccollection.update_one(filter, {'$set': {'message_count': message_count}})
            await interaction.response.edit_message(content=f'{tick} **{interaction.user.display_name}**, I have added `{message_count_value}` messages to the users message count.', embed=None, view=None)
        else:
            message_count = message_count_value
            await mccollection.insert_one({'guild_id': guild_id, 'user_id': self.user_id, 'message_count': message_count})


class RemovedMessage(discord.ui.Modal, title='Remove Messages'):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id



    message_count = discord.ui.TextInput(
        label='Removed Message Count',
        placeholder='Will remove from their current message count',
    )

    async def on_submit(self, interaction: discord.Interaction):
        result = await mccollection.find_one({'guild_id': interaction.guild.id, 'user_id': self.user_id})
        message_count_value = int(self.message_count.value)
        guild_id = interaction.guild.id
        if result:
            message_count = int(result['message_count']) - message_count_value
            filter = {'guild_id': guild_id, 'user_id': self.user_id}
            await mccollection.update_one(filter, {'$set': {'message_count': message_count}})
            await interaction.response.edit_message(content=f'{tick} **{interaction.user.display_name}**, I have added `{message_count_value}` messages to the users message count.', embed=None, view=None)
        else:
            message_count = message_count_value
            await mccollection.insert_one({'guild_id': guild_id, 'user_id': self.user_id, 'message_count': 0})





class StaffManage(discord.ui.View):
    def __init__(self, staff_id, author):
        super().__init__(timeout=None)
        self.value = None
        self.staff_id = staff_id        
        self.author = author



    @discord.ui.button(label="Add Messages", style=discord.ButtonStyle.green,emoji="<:Add:1163095623600447558>", row=1)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
       if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True) 
       await interaction.response.send_modal(AddMessage(self.staff_id))      
    @discord.ui.button(label="Subtract Messages", style=discord.ButtonStyle.red, emoji="<:Subtract:1229040262161109003>", row=1)
    async def subtract(self, interaction: discord.Interaction, button: discord.ui.Button):
       if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True) 
       await interaction.response.send_modal(RemovedMessage(self.staff_id))     

    @discord.ui.button(label='Set Messages', style=discord.ButtonStyle.blurple, row=2, emoji="<:Pen:1235001839036923996>")
    async def set(self, interaction: discord.Interaction, button: discord.ui.Button):
       if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
       await interaction.response.send_modal(SetMessages(self.staff_id))      



    @discord.ui.button(label='Reset Messages', style=discord.ButtonStyle.red, row=2, emoji="<:bin:1235001855721865347>")
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
       staff_id = self.staff_id
       if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                 
       filter = {'guild_id': interaction.guild.id, 'user_id': staff_id}
       update = {'$set': {'message_count': 0}}
       await mccollection.update_one(filter, update)

       await interaction.response.edit_message(content=f'**{tick} {interaction.user.display_name}**, I have resetted the staffs message count.', embed=None, view=None)
    





dbq = mongo['quotab']
mccollection = dbq["messages"]
message_quota_collection = dbq["message_quota"]



class quota(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.quota_activity.start()







    async def modulecheck(self, ctx: commands.Context): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata.get('Quota', False) == True:   
        return True

    async def modulecheck2(self, ctx: commands.Context): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata.get('Staff Database', False) == True: 
        return True
     else:   
        return False

    async def check_admin_and_staff(self, ctx: commands.Context, user: discord.User):
        filter = {'guild_id': ctx.guild.id}
        staff_data = await scollection.find_one(filter)
        if staff_data and 'staffrole' in staff_data:
            staff_role_ids = staff_data['staffrole']
            staff_role_ids = staff_role_ids if isinstance(staff_role_ids, list) else [staff_role_ids]
            admin_data = await arole.find_one(filter)
            if not admin_data:
             return False
            else:
                if 'staffrole' in admin_data:
                    admin_role_ids = admin_data['staffrole']
                    admin_role_ids = admin_role_ids if isinstance(admin_role_ids, list) else [admin_role_ids]

                    if any(role.id in staff_role_ids + admin_role_ids for role in user.roles):
                        return True
                    else:
                        return False
            if any(role.id in staff_role_ids for role in user.roles):
                return True
            else:
                return False
        else:
            return False


    async def check_admin_and_staff_2(self, guild: discord.Guild, user: discord.Member):
        filter = {'guild_id': guild.id}
        staff_data = await scollection.find_one(filter)
        if staff_data and 'staffrole' in staff_data:
            staff_role_ids = staff_data['staffrole']
            staff_role_ids = staff_role_ids if isinstance(staff_role_ids, list) else [staff_role_ids]
            admin_data = await arole.find_one(filter)
            if not user:
                return False
            if not admin_data:
             return False
            else:
                if 'staffrole' in admin_data:
                    admin_role_ids = admin_data['staffrole']
                    admin_role_ids = admin_role_ids if isinstance(admin_role_ids, list) else [admin_role_ids]

                    if any(role.id in staff_role_ids + admin_role_ids for role in user.roles):
                        return True
                    else:
                        return False
            if any(role.id in staff_role_ids for role in user.roles):
                return True
            else:
                return False
        else:
            return False
    

    @tasks.loop(minutes=5, reconnect=True)
    async def quota_activity(self):
       print('[INFO] Checking for quota activity')
       if environment == "custom":
           autoactivityresult = await autoactivity.find({'guild_id': int(guildid)}).to_list(length=None)
       else:
        autoactivityresult = await autoactivity.find({}).to_list(length=None)
       if autoactivityresult:

        for data in autoactivityresult:
            if data.get('enabled', False) == False:
                continue
            try: 
             channel = self.client.get_channel(data.get('channel_id', None))
            except (discord.HTTPException, discord.NotFound):
                 print(f"[ERROR] Channel {data.get('channel_id', None)} not found.") 
                 pass
            days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'tuesday']
            
            nextdate = data.get('nextdate', None)
            day = data.get('day', None)
            
            
            if day is None:
                continue
            if nextdate is None:
                continue     
            day = str(day).lower()       
            current_day_index = datetime.utcnow().weekday()  
            specified_day_index = days.index(day)
            
            days_until_next_occurrence = (specified_day_index - current_day_index) % 7
            

            next_occurrence_date = datetime.utcnow() + timedelta(days=days_until_next_occurrence - 1 )
            if next_occurrence_date < datetime.now():
                next_occurrence_date += timedelta(days=7)                    

            if nextdate < datetime.now():
                
                try:
                 guild = await self.client.fetch_guild(data.get('guild_id', None))
                except (discord.HTTPException, discord.NotFound):
                    continue 
                if not guild:
                    continue                   
                await autoactivity.update_one(
                {'guild_id': guild.id},
                {'$set': {'nextdate': next_occurrence_date, 'lastposted': datetime.utcnow()}}
)  
                         
                print(f'[⏰] Sending Activity @{guild.name} next post is {next_occurrence_date}!')
                if guild:
                    result = await mccollection.find({'guild_id': guild.id}).to_list(length=None)
                    loa_role_data = await lcollection.find_one({'guild_id': guild.id})
                    passed = []
                    failed = []    
                    on_loa = []      
                    failedids = []      
                    if result:
                        for data in result:
                            has_loa_role = False

                            try:
                             user = await guild.fetch_member(data.get('user_id', None))
                            except (discord.HTTPException, discord.NotFound):
                                continue                         
                            if not user:
                                continue
                            if user:
                                if not await self.check_admin_and_staff_2(guild, user):
                                    continue
                                result = await mccollection.find_one({'guild_id': guild.id, 'user_id': user.id})
                                quotaresult = await message_quota_collection.find_one({'guild_id': guild.id})
                                if loa_role_data:
                                    loa_role_id = loa_role_data.get('staffrole')
                                    has_loa_role = any(role.id == loa_role_id for role in user.roles)
                                                    
                                if quotaresult and result:
                                    message_quota = quotaresult.get('quota', 100)
                                    message_count = result.get('message_count', 0)
                                    if has_loa_role:
                                        on_loa.append(f"> **{user.name}** • `{message_count}` messages")
                                        continue



                                    if int(message_count) >= int(message_quota):
                                        passed.append(f"> **{user.name}** • `{message_count}` messages")
                                    else:    
                                        failed.append(f"> **{user.name}** • `{message_count}` messages")
                                        failedids.append(user.id)




                                    
                    
                    else:
                        continue
                    passed.sort(key=lambda x: int(x.split('•')[-1].strip().split(' ')[0].strip('`')), reverse=True)
                    failed.sort(key=lambda x: int(x.split('•')[-1].strip().split(' ')[0].strip('`')), reverse=True)
                    on_loa.sort(key=lambda x: int(x.split('•')[-1].strip().split(' ')[0].strip('`')), reverse=True)
                    passedembed = discord.Embed(title="Passed", color=discord.Color.brand_green())   
                    passedembed.set_image(url="https://astrobirb.dev/assets/invisible.png")
                    if passed:
                     passedembed.description = "\n".join(passed)
                    else:
                        passedembed.description = "> No users passed the quota."
                    
                    loaembed = discord.Embed(title="On LOA", color=discord.Color.purple())
                    loaembed.set_image(url="https://astrobirb.dev/assets/invisible.png")
                    if on_loa:
                     loaembed.description = "\n".join(on_loa)
                    else:
                        loaembed.description = "> No users on LOA."



                    failedembed = discord.Embed(title="Failed", color=discord.Color.brand_red())   
                    failedembed.set_image(url="https://astrobirb.dev/assets/invisible.png")
                    if failed:
                     failedembed.description = "\n".join(failed)
                    else:
                        failedembed.description = "> No users failed the quota."
                    if channel:
                        
                         view = ResetLeaderboard()

                         try:
                          await channel.send(embeds=[passedembed, loaembed, failedembed], view=view)
                         except discord.Forbidden:
                            print('[ERROR] Channel not found') 
                            return                        
                    else:
                        print('[NOTFOUND] Channel not found')
                        continue    


                                   


    @commands.hybrid_group(name="staff")
    async def staff(self, ctx: commands.Context):
        return

            
    @staff.group(name="manage")
    async def manage(self, ctx: commands.Context):
        pass

    @manage.command(name="messages", description="Manage a staffs messages count.")
    async def messages(self, ctx: commands.Context, staff: discord.Member):
     await ctx.defer()

     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the quota module isn't enabled.")
         return   
     if not await has_admin_role(ctx):
            return                      
     mccollection = dbq["messages"]
     message_data = await mccollection.find_one({'guild_id': ctx.guild.id, 'user_id': staff.id})
     loa_role_data = await lcollection.find_one({'guild_id': ctx.guild.id})
     if message_data:
        message_count = message_data.get('message_count', 0)
     else:
        message_count = 0
     message_quota_result = await message_quota_collection.find_one({'guild_id': ctx.guild.id})

     if loa_role_data:
                    loa_role_id = loa_role_data.get('staffrole')
                    has_loa_role = any(role.id == loa_role_id for role in staff.roles)
     else:
                    has_loa_role = False

     if message_quota_result:
                    message_quota = message_quota_result.get('quota', 100)
                    message_quota = int(message_quota)

     else:
                    message_quota = 100

     view = StaffManage(staff.id, ctx.author)
     if message_count >= message_quota:
                    emoji = "`LOA`" if has_loa_role else "<:Confirmed:1122636234255253545>"
     else:
                    emoji = "`LOA`" if has_loa_role else "<:Cancelled:1122637466353008810>"     

     embed = discord.Embed(
        title=f"<:messagereceived:1201999712593383444> {staff.display_name}'s Activity Stats",
        description=f"{replytop} **Messages:** {message_count}\n{replybottom} **Passed:** {emoji}",
        color=discord.Color.dark_embed()
    )
     embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
     embed.set_thumbnail(url=staff.display_avatar)
    
     await ctx.send(embed=embed, view=view)



    @staff.command(name="messages", description="Display the amount the message count of a staff member.")
    async def messages(self, ctx: commands.Context, staff: discord.Member):

     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the quota module isn't enabled.")
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
        await ctx.send(f"<:Messages:1148610048151523339> **{staff.display_name}** has sent {message_count} messages.")        
     else:  
          if staff is ctx.author:
           await ctx.send(f"{no} **{ctx.author.display_name}**, couldn't find any messages from you or your not staff.")
          else: 
            await ctx.send(f"{no} **{ctx.author.display_name}**, couldn't find any messages from this user or they aren't staff.")


    @staff.command(description="View the staff message leaderboard to see if anyone has passed their quota")
    async def leaderboard(self, ctx: commands.Context):
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the quota module isn't enabled.")
            return

        await ctx.defer()
        
        if not await has_staff_role(ctx):
            return
        filter = {'guild_id': ctx.guild.id}
        cursor = mccollection.find(filter).sort("message_count", pymongo.DESCENDING).limit(750)

        user_data_list = await cursor.to_list(length=750)

        pages = []
        rank = 1
        leaderboard_description = ""
        for user_data in user_data_list:
            user_id = user_data['user_id']
            message_count = user_data['message_count']
            member = ctx.guild.get_member(user_id)
                
            loa_role_data = await lcollection.find_one({'guild_id': ctx.guild.id})
            if not member:
                
                try:
                 member = await ctx.guild.fetch_member(user_id)
                except (discord.HTTPException, discord.NotFound):
                    
                    continue 
                if not member:
                    continue
                print(f"[ERROR] Cache ERROR (member not found) Using FETCH Instead.")

            if member:
                if not await self.check_admin_and_staff(ctx, member):
                    continue


                message_quota_result = await message_quota_collection.find_one({'guild_id': ctx.guild.id})

                if message_quota_result:
                    message_quota = message_quota_result.get('quota', 100)
                    message_quota = int(message_quota)

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
                    emoji = "`LOA`" if has_loa_role else f"{redxbox}"

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

        PreviousButton = discord.ui.Button(emoji="<:chevronleft:1220806425140531321>")
        NextButton = discord.ui.Button(emoji="<:chevronright:1220806430010118175>")
        FirstPageButton = discord.ui.Button(emoji="<:chevronsleft:1220806428726661130>")
        LastPageButton = discord.ui.Button(emoji="<:chevronsright:1220806426583371866>")
        InitialPage = 0
        timeout = 42069
        if len(pages) <= 1:
            PreviousButton.disabled = True
            NextButton.disabled = True
            FirstPageButton.disabled = True
            LastPageButton.disabled = True           
        paginator = Paginator.Simple(
            PreviousButton=PreviousButton,
            NextButton=NextButton,
            FirstEmbedButton=FirstPageButton,
            LastEmbedButton=LastPageButton,
            InitialPage=InitialPage,
            timeout=timeout
        )

        await paginator.start(ctx, pages=pages)
    
    

    @staff.command(name="leaderboard-reset", description="Reset the message quota leaderboard")
    async def reset_staff_message_counts(self, ctx: commands.Context):
        await ctx.defer()
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the quota module isn't enabled.")
         return                    
        if not await has_admin_role(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`")
            return  
            
        mccollection = dbq["messages"]
        await mccollection.update_many({'guild_id': ctx.guild.id}, {'$set': {'message_count': 0}})
        await ctx.send(f"{tick} **{ctx.author.display_name}**, I've reset the entire staff team's message count.")                    
        try:
                owner = ctx.guild.owner
                await owner.send(f"{tick} **{ctx.guild.owner.display_name}**, `{ctx.author.display_name}` has reset the staff leaderboard.")
        except Exception as e:
                 print('Yeah I couldn\'t dm the owner but oh well.')
                 return



# Staff Panel ------
        

        
    @staff.command(description="Add a staff member to the staff database.")
    @app_commands.describe(
        staff="The staff member to add.",
        rank="The staff member's rank.",
        timezone="The staff member's timezone."
    )
    async def add(self, ctx: commands.Context, staff: discord.User, rank: str, timezone: str = None):
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the staff database module isn't enabled.")
            return        
        if not await has_admin_role(ctx):
            return
       
        if await staffdb.find_one({'guild_id': ctx.guild.id, 'staff_id': staff.id}):
            return await ctx.send(f"{no} **{ctx.author.display_name}**, this user is already a staff member.")
        try:
            await staffdb.insert_one({
                'guild_id': ctx.guild.id,
                'staff_id': staff.id,
                'name': staff.display_name,
                'rank': rank,
                'timezone': timezone,
                'joinestaff': datetime.utcnow(),
                'rolename': rank
            })
        except Exception as e:
            print(e)

        await ctx.send(f'{tick} **{ctx.author.display_name},** staff member added successfully.')

    @staff.command(description="Remove a staff member from the staff database.")
    @app_commands.describe(
        staff="The staff member to remove."
    )
    async def remove(self, ctx: commands.Context, staff: discord.User):
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module isn't enabled.")
            return        
        if not await has_admin_role(ctx):
            return
        if not await staffdb.find_one({'guild_id': ctx.guild.id, 'staff_id': staff.id}):
            return await ctx.send(f"{no} **{ctx.author.display_name}**, this user has not been added to the staff team.")
        try:
            await staffdb.delete_one({'guild_id': ctx.guild.id, 'staff_id': staff.id})
        except Exception as e:
            print(e)
        await ctx.send(f'{tick} **{ctx.author.display_name},** staff member removed successfully.')

    @staff.command(description="Edit a staff member's rank. (Staff Database)")
    @app_commands.describe(
        staff="The staff member to edit.", 
        rank="The staff member's new rank.", 
        timezone="The staff member's new timezone.", 
        introduction="The staff member's new introduction."
    )
    async def edit(self, ctx: commands.Context, staff: discord.User, rank: str, timezone: str = None, *, introduction = None):
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the staff database module isn't enabled.")
            return        
        if not await has_admin_role(ctx):
            return
        
        if not await staffdb.find_one({'guild_id': ctx.guild.id, 'staff_id': staff.id}):
            return await ctx.send(f"{no} **{ctx.author.display_name}**, this user has not been added to the staff team.")
        try:
            await staffdb.update_one({'guild_id': ctx.guild.id, 'staff_id': staff.id}, {'$set': {'rolename': rank, 'timezone': timezone or None, 'introduction': introduction or None}})
        except Exception as e:
            print(e)
        await ctx.send(f'{tick} **{ctx.author.display_name},** staff member edited successfully.')
    
    @staff.command(description="View a staff member's information. (Staff Database)")
    @app_commands.describe(staff="The staff member to view.")
    async def view(self, ctx: commands.Context, staff: discord.User):
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module isn't enabled.")
            return        
        if not await has_staff_role(ctx):
            return
        result = await staffdb.find_one({'guild_id': ctx.guild.id, 'staff_id': staff.id})
        if result is None:
            await ctx.send(f"{no} **{ctx.author.display_name}**, this user is not in the staff database.")
            return
        timezone = ""
        introduction = ""
        if result.get('introduction', None):
            introduction = f"\n\n**Introduction:**\n```{result['introduction']}```"
        else:
            introduction = ""
        if result.get('timezone', None):
            timezone = f"\n{arrow} **Timezone:** {result['timezone']}" 
        else:
            timezone = ""

        if result:
            embed = discord.Embed(
                title=staff.display_name,
                description=f"{arrow} **Staff:** <@{staff.id}>\n{arrow} **Rank:** {result['rolename']}{timezone}\n{arrow} **Joined Staff:** <t:{int(result['joinestaff'].timestamp())}:F>{introduction}",
                color=discord.Color.dark_embed()
            )
            embed.set_thumbnail(url=staff.display_avatar)
            embed.set_author(name=staff.name, icon_url=staff.display_avatar)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{ctx.author.display_name}, I couldn't find **@{staff.display_name}**.")
    @staff.command(description="Give yourself an introduction (Staff Database)")
    @app_commands.describe(introduction = "The introduction you want to add to your staff profile.")
    async def introduction(self, ctx: commands.Context, *, introduction):
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the staff database module isn't enabled.")
            return      
        result = await staffdb.find_one({'guild_id': ctx.guild.id, 'staff_id': ctx.author.id})
        if not result:
                return await ctx.send(f"{no} **{ctx.author.display_name}**, you are not in the staff database.")
           
        await staffdb.update_one({'guild_id': ctx.guild.id, 'staff_id': ctx.author.id}, {'$set': {'introduction': introduction}})
        await ctx.send(f"{tick} **{ctx.author.display_name}**, your introduction has been updated.")


           


    @staff.command(description="Send a panel that shows all staff members. (Staff Database)")
    async def panel(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        if not await has_admin_role(ctx):
            return
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the staff database module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return
        custom = await Customisation.find_one({'guild_id': ctx.guild.id, 'name': 'Staff Panel'})
        if custom:
            if custom.get('embed') == True:
             embed_title = custom.get('title', None)
             embed_description = custom.get('description', None)
             embed_author = custom.get('author', None)

             if embed_title in ["None", None]:
                embed_title = ""
             if embed_description in ["None", None]:
                embed_description = ""
             color_value = custom.get('color', None)
             colors = discord.Colour(int(color_value, 16)) if color_value else discord.Colour.dark_embed()

             embed = discord.Embed(
                title=embed_title,
                description=embed_description, color=colors)

             if embed_author in ["None", None]:
                embed_author = ""
             if 'image' in custom:
                embed.set_image(url=custom['image'])
             if 'thumbnail' in custom:
                embed.set_thumbnail(url=custom['thumbnail'])
             if 'author' in custom and 'author_icon' in custom:
                embed.set_author(name=embed_author, icon_url=custom['author_icon']) 
             view = Staffview()          
             content = custom.get('content', None)
             if content in ["None", None]:
                content = ""     
             try:
              await ctx.channel.send(content, embed=embed, view=view)
              await ctx.send(f"{tick} **{ctx.author.display_name},** staff panel sent successfully.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
             except (discord.errors.HTTPException, discord.errors.Forbidden):
                await ctx.send(f"{no} **{ctx.author.display_name}**, I don't have permission to send messages in that channel.", allowed_mentions=discord.AllowedMentions.none()) 
                return              
             return   
            
            else:
             embed = discord.Embed(title="Staff Panel", description="Select a staff member to view their information.", color=discord.Color.dark_embed())
             embed.set_thumbnail(url=ctx.guild.icon)
             embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
             view = Staffview()
             
             try:
              await ctx.channel.send(embed=embed, view=view)
              await ctx.send(f"{tick} **{ctx.author.display_name},** staff panel sent successfully.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
             except (discord.errors.HTTPException, discord.errors.Forbidden):
                await ctx.send(f"{no} **{ctx.author.display_name}**, I don't have permission to send messages in that channel.", allowed_mentions=discord.AllowedMentions.none()) 
                return
             return   

        else:
            embed = discord.Embed(title="Staff Panel", description="Select a staff member to view their information.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=ctx.guild.icon)
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            view = Staffview()
            try:
             await ctx.send(f"{tick} **{ctx.author.display_name},** staff panel sent successfully.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
             await ctx.channel.send(embed=embed, view=view)
            except (discord.errors.HTTPException, discord.errors.Forbidden):
                await ctx.send(f"{no} **{ctx.author.display_name}**, I don't have permission to send messages in that channel.", allowed_mentions=discord.AllowedMentions.none()) 
                return             
            return   



        


class Staffview(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StaffPanel())

class StaffPanel(discord.ui.Select):
    def __init__(self):
        from pymongo import MongoClient
        mongo = MongoClient(MONGO_URL)
        db = mongo['astro']
        self.collection = db['staff database']

        options = [discord.SelectOption(label='Load', description='Load the staff panel', emoji='<:staticload:1206248311280111616>')]
        super().__init__(placeholder='Staff', min_values=1, max_values=1, options=options, custom_id='persistent:staffpanel')

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            value = self.values[0]
            if value in ('Reload', 'Load'):
                await self.update_options(interaction)

                return

            result = self.collection.find_one({'name': value, 'guild_id': interaction.guild.id})
            if value == 'Load More':
                results = self.collection.find({'guild_id': interaction.guild.id})
                staff_names = [result['name'] for result in results]
                 
                 
                names_str = '\n'.join([f"{arrow} **{name}**" for name in staff_names])
                embed = discord.Embed(title='All Staff', description=names_str, color=discord.Color.dark_embed())    
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                embed.set_thumbnail(url=interaction.guild.icon)
                view = StaffButton()
                await interaction.followup.send(embed=embed, view=view, ephemeral=True  )
                return
       
            if result:
                    staff_id = result['staff_id']
                    staff = interaction.guild.get_member(staff_id)
                    if staff is None:
                        staff = await interaction.guild.fetch_member(staff_id)
                        if staff is None:
                            await interaction.followup.send(f"{no} {interaction.user.display_name}, I couldn't find **@{value}**.", ephemeral=True)
                            return
                    if staff:
                        timezone = ""
                        introduction = ""
                        if result.get('introduction') is not None:
                            introduction = f"\n\n**Introduction:**\n```{result['introduction']}```"
                        if result.get('timezone') is not None:
                            timezone = f"\n{arrow} **Timezone:** {result['timezone']}" 

                        embed = discord.Embed(
                            title=staff.display_name,
                            description=f"{arrow} **Staff:** <@{staff.id}>\n{arrow} **Rank:** {result['rolename']}{timezone}\n{arrow} **Joined Staff:** <t:{int(result['joinestaff'].timestamp())}:F>{introduction}",
                            color=discord.Color.dark_embed()
                        )
                        embed.set_thumbnail(url=staff.display_avatar)
                        embed.set_author(name=staff.display_name, icon_url=staff.display_avatar)
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        print('3')
                    else:
                        await interaction.followup.send(f"{no} {interaction.user.display_name}, I couldn't find **@{value}**.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

                        
        except Exception as e:
            print(e)
            

    async def update_options(self, interaction: discord.Interaction):
     try: 
        results = self.collection.find({'guild_id': interaction.guild.id}).limit(23)
        options = [discord.SelectOption(label='Reload', description='Reload the staff panel', emoji='<:staticload:1206248311280111616>')]
        if self.collection.count_documents({'guild_id': interaction.guild.id}) > 1:
            options.append(discord.SelectOption(label='Load More', description='Load more staff members', emoji='<:select:1206247978050916423>'))
        for result in results:
            staff_id = result['staff_id']
            staff = await interaction.guild.fetch_member(staff_id)
            if staff:
                if result.get('rolename', None) is not None:
                    description = result['rolename']
                else:
                    description = ''    
                options.append(discord.SelectOption(label=result['name'], emoji='<:staff:1206248655359840326>', description=description))
     except Exception as e:
        print(e)
     self.options = options
     label_change = await StaffPanelLabel.find_one({'guild_id': interaction.guild.id})
     labelchange = 'Staff'
     if label_change:
        labelchange = label_change['label']

     self.placeholder = labelchange
      
     await interaction.edit_original_response(view=self.view)
        

class StaffButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label='Search Staff', style=discord.ButtonStyle.secondary, custom_id='load_more_button')
    async def load_more_button(self, interaction: discord.Interaction, button: discord.ui.Button):
     
     await interaction.response.send_modal(StaffModal())

                
class StaffModal(discord.ui.Modal, title='Search Staff'):

    rolename = discord.ui.TextInput(
        label='Staff Name',
        placeholder='Search for a staff member from the list.',
        style=discord.TextStyle.short,
        required=True
    )


    async def on_submit(self, interaction: discord.Interaction):
        staff_name = self.rolename.value
        result = await staffdb.find_one({'name': staff_name})
        if result:
                    staff_id = result['staff_id']
                    staff = interaction.guild.get_member(staff_id)

                    if staff:
                        timezone = ""
                        introduction = ""
                        if result.get('introduction') is not None:
                            introduction = f"\n\n**Introduction:**\n```{result['introduction']}```"
                        if result.get('timezone') is not None:
                            timezone = f"\n{arrow} **Timezone:** {result['timezone']}" 

                        embed = discord.Embed(
                            title=staff.display_name,
                            description=f"{arrow} **Staff:** <@{staff.id}>\n{arrow} **Rank:** {result['rolename']}{timezone}\n{arrow} **Joined Staff:** <t:{int(result['joinestaff'].timestamp())}:F>{introduction}",
                            color=discord.Color.dark_embed()
                        )
                        embed.set_thumbnail(url=staff.avatar.url)
                        embed.set_author(name=staff.display_name, icon_url=staff.avatar.url)
                        await interaction.response.send_message(embed=embed, ephemeral=True)

                    else:
                     return await interaction.response.send_message(f"{no} {interaction.user.display_name}, I couldn't find **@{staff_name}**.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        else:
                     return await interaction.response.send_message(f"{no} {interaction.user.display_name}, I couldn't find **@{staff_name}**.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

class ResetLeaderboard(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @staticmethod
    async def has_admin_role(interaction):
        filter = {
            'guild_id': interaction.guild.id
        }
        staff_data = await arole.find_one(filter)

        if staff_data and 'staffrole' in staff_data:
            staff_role_ids = staff_data['staffrole']
            staff_role = discord.utils.get(interaction.guild.roles, id=staff_role_ids)
            if not isinstance(staff_role_ids, list):
                staff_role_ids = [staff_role_ids]
            if any(role.id in staff_role_ids for role in interaction.user.roles):
                return True

        return False

    @discord.ui.button(label='Reset Leaderboard', style=discord.ButtonStyle.danger, custom_id='persistent:resetleaderboard', emoji="<:staticload:1206248311280111616>")
    async def reset_button(self,  interaction: discord.Interaction, button: discord.ui.Button):   
       if not await self.has_admin_role(interaction):
           await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, You don't have permission to use this button", ephemeral=True)
           return    
       button.label =f'Reset By @{interaction.user.display_name}'
       button.disabled = True
       await mccollection.update_many({'guild_id': interaction.guild.id}, {'$set': {'message_count': 0}})
       await interaction.response.edit_message(view=self)       




async def setup(client: commands.Bot) -> None:
    await client.add_cog(quota(client))     
       
    