import discord
from discord.ext import commands
import pymongo
import Paginator
from emojis import *
import os
from datetime import datetime
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

    async def modulecheck2(self, ctx): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata.get('Staff Database', False) == True: 
        return True
     else:   
        return False

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


# Staff Panel ------
        

        
    @staff.command(description="Add a staff member to the staff database.")
    async def add(self, ctx, staff: discord.User, rank: str, timezone: str = None):
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is not enabled.")
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
    async def remove(self, ctx, staff: discord.User):
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is not enabled.")
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
    async def edit(self, ctx, staff: discord.User, rank: str, timezone: str = None, *, introduction = None):
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is not enabled.")
            return        
        if not await has_admin_role(ctx):
            return
        
        if not await staffdb.find_one({'guild_id': ctx.guild.id, 'staff_id': staff.id}):
            return await ctx.send(f"{no} **{ctx.author.display_name}**, this user has not been added to the staff team.")
        try:
            await staffdb.update_one({'guild_id': ctx.guild.id, 'staff_id': staff.id}, {'$set': {'rank': rank, 'timezone': timezone or None, 'introduction': introduction or None}})
        except Exception as e:
            print(e)
        await ctx.send(f'{tick} **{ctx.author.display_name},** staff member edited successfully.')
    
    @staff.command(description="View a staff member's information. (Staff Database)")
    async def view(self, ctx, staff: discord.User):
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is not enabled.")
            return        
        if not await has_staff_role(ctx):
            return
        result = await staffdb.find_one({'guild_id': ctx.guild.id, 'staff_id': staff.id})
        timezone = ""
        introduction = ""
        if result.get('introduction', None):
            introduction = f"\n\n**Introduction:**\n```{result['introduction']}```"
        else:
            introduction = ""
        if result.get('timezone', None):
            timezone = f"\n<:arrow:1166529434493386823> **Timezone:** {result['timezone']}" 
        else:
            timezone = ""

        if result:
            embed = discord.Embed(
                title=staff.display_name,
                description=f"<:arrow:1166529434493386823> **Staff:** <@{staff.id}>\n<:arrow:1166529434493386823> **Rank:** {result['rank']}{timezone}\n<:arrow:1166529434493386823> **Joined Staff:** <t:{int(result['joinestaff'].timestamp())}:F>{introduction}",
                color=discord.Color.dark_embed()
            )
            embed.set_thumbnail(url=staff.display_avatar)
            embed.set_author(name=staff.name, icon_url=staff.display_avatar)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{ctx.author.display_name}, I couldn't find **@{staff.display_name}**.")
    @staff.command(description="Give yourself an introduction (Staff Database)")
    async def introduction(self, ctx, *, introduction):
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is not enabled.")
            return      
        result = await staffdb.find_one({'guild_id': ctx.guild.id, 'staff_id': ctx.author.id})
        if not result:
                return await ctx.send(f"{no} **{ctx.author.display_name}**, you are not in the staff database.")
           
        await staffdb.update_one({'guild_id': ctx.guild.id, 'staff_id': ctx.author.id}, {'$set': {'introduction': introduction}})
        await ctx.send(f"{tick} **{ctx.author.display_name}**, your introduction has been updated.")


           


    @staff.command(description="Send a panel that shows all staff members. (Staff Database)")
    async def panel(self, ctx):
        if not await has_admin_role(ctx):
            return
        if not await self.modulecheck2(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is not enabled.")
            return
        custom = await Customisation.find_one({'guild_id': ctx.guild.id, 'name': 'Staff Panel'})
        if custom:
            if custom['embed'] == True:
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
             await ctx.channel.send(content, embed=embed, view=view)
             await ctx.send(f"**{ctx.author.display_name},** staff panel sent successfully.", ephemeral=True)
             return   
        else:
            embed = discord.Embed(title="Staff Panel", description="Select a staff member to view their information.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=ctx.guild.icon)
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            view = Staffview()
            await ctx.send(f"**{ctx.author.display_name},** staff panel sent successfully.", ephemeral=True)
            await ctx.channel.send(embed=embed, view=view)
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
        try:
            value = self.values[0]
            if value in ('Reload', 'Load'):
                await self.update_options(interaction)
                return

            result = self.collection.find_one({'name': value, 'guild_id': interaction.guild.id})
            print(f"{result} + Guild = {interaction.guild.name}")
            if value == 'Load More':
                results = self.collection.find({'guild_id': interaction.guild.id})
                staff_names = [result['name'] for result in results]
                 
                 
                names_str = '\n'.join([f"<:arrow:1166529434493386823> **{name}**" for name in staff_names])
                embed = discord.Embed(title='All Staff', description=names_str, color=discord.Color.dark_embed())    
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                embed.set_thumbnail(url=interaction.guild.icon)
                view = StaffButton()
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True  )
                return
       
            if result:
                    staff_id = result['staff_id']
                    staff = interaction.guild.get_member(staff_id)
                    if staff is None:
                        staff = await interaction.guild.fetch_member(staff_id)
                        if staff is None:
                            await interaction.response.send_message(f"{no} {interaction.user.display_name}, I couldn't find **@{value}**.", ephemeral=True)
                            return
                    if staff:
                        timezone = ""
                        introduction = ""
                        if result.get('introduction') is not None:
                            introduction = f"\n\n**Introduction:**\n```{result['introduction']}```"
                        if result.get('timezone') is not None:
                            timezone = f"\n<:arrow:1166529434493386823> **Timezone:** {result['timezone']}" 

                        embed = discord.Embed(
                            title=staff.display_name,
                            description=f"<:arrow:1166529434493386823> **Staff:** <@{staff.id}>\n<:arrow:1166529434493386823> **Rank:** {result['rank']}{timezone}\n<:arrow:1166529434493386823> **Joined Staff:** <t:{int(result['joinestaff'].timestamp())}:F>{introduction}",
                            color=discord.Color.dark_embed()
                        )
                        embed.set_thumbnail(url=staff.display_avatar)
                        embed.set_author(name=staff.display_name, icon_url=staff.display_avatar)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        print('3')
                    else:
                        await interaction.response.send_message(f"{no} {interaction.user.display_name}, I couldn't find **@{value}**.", ephemeral=True)

                        
        except Exception as e:
            print(e)
            

    async def update_options(self, interaction: discord.Interaction):
        try: 
         results = self.collection.find({'guild_id': interaction.guild.id}).limit(24)
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
        await interaction.response.edit_message(view=self.view)
        

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
                            timezone = f"\n<:arrow:1166529434493386823> **Timezone:** {result['timezone']}" 

                        embed = discord.Embed(
                            title=staff.display_name,
                            description=f"<:arrow:1166529434493386823> **Staff:** <@{staff.id}>\n<:arrow:1166529434493386823> **Rank:** {result['rank']}{timezone}\n<:arrow:1166529434493386823> **Joined Staff:** <t:{int(result['joinestaff'].timestamp())}:F>{introduction}",
                            color=discord.Color.dark_embed()
                        )
                        embed.set_thumbnail(url=staff.avatar.url)
                        embed.set_author(name=staff.display_name, icon_url=staff.avatar.url)
                        await interaction.response.send_message(embed=embed, ephemeral=True)

                    else:
                     return await interaction.response.send_message(f"{no} {interaction.user.display_name}, I couldn't find **@{staff_name}**.", ephemeral=True)
        else:
                     return await interaction.response.send_message(f"{no} {interaction.user.display_name}, I couldn't find **@{staff_name}**.", ephemeral=True)

                     


async def setup(client: commands.Bot) -> None:
    await client.add_cog(quota(client))        
    
