import discord
from discord.ext import commands
from discord.ext import commands
from emojis import *
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
infractions = db['infractions']
infractiontypes = db['infractiontypes']
suggestions_collection = db["suggestions"]
loa_collection = db['loa']
scollection = db['staffrole']
arole = db['adminrole']
LOARole = db['LOA Role']
infchannel = db['infraction channel']
repchannel = db['report channel']
loachannel = db['loa channel']
promochannel = db['promo channel']
feedbackch = db['Staff Feedback Channel']

appealable = db['Appeal Toggle']
appealschannel = db['Appeals Channel']
loachannel = db['LOA Channel']
tags = db['tags']
partnershipch = db['Partnerships Channel']
modules = db['Modules']
nfractiontypes = db['infractiontypes']
promotions = db['promotions']
ApplicationsChannel = db['Applications Channel']
ApplicationsRolesDB = db['Applications Roles']
ReportModeratorRole = db['Report Moderator Role']
reports = db['Reports']
db2 = client['quotab']
scollection2 = db2['staffrole']
message_quota_collection = db2["message_quota"]
arole2 = db2['adminrole']
srole = db2['staffrole']
mccollection = db2["messages"]
suggestschannel = db["suggestion channel"]
customcommands = db['Custom Commands']
modmailping = db['modmailping']
modmailcategory = db['modmailcategory']
transcriptchannel = db['transcriptschannel']
partnerships = db['Partnerships']
connectionroles = db['connectionroles']
suspensions = db['Suspensions']
forumsconfig = db['Forum Configuration']
stafffeedback = db['feedback']
staffdb = db['staff database']
welcome = db['welcome settings']
infractiontypeactions = db['infractiontypeactions']

promotionroles = db['promotion roles']
class DataView(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.add_item(DataSelector(author))
            

class DataSelector(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
        discord.SelectOption(label="Infractions", value="Infractions", emoji="<:Remove:1162134605885870180>"), #
        discord.SelectOption(label="Promotions", value="Promotions", emoji="<:Promote:1162134864594735315>"), #
        discord.SelectOption(label="Custom Commands", value="Custom Commands", emoji="<:command1:1223062616872583289>"), #
        discord.SelectOption(label="Welcome", value="Welcome", emoji="<:welcome:1234994848856150057>"), #
        discord.SelectOption(label="Modmail", value="Modmail", emoji="<:messagereceived:1201999712593383444>"), #  
        discord.SelectOption(label="Quota", value="Quota", emoji="<:quota:1234994790056198175>"), #
        discord.SelectOption(label="Suggestions", value="Suggestions", emoji="<:announcement:1192867080408682526>"),  #
        discord.SelectOption(label="Staff Database & Panel", value="Staff Database & Panel", emoji="<:staffdb:1206253848298127370>"),
        discord.SelectOption(label="Forums Autopost + Utils", value="Forums Autopost + Utils", emoji="<:forum:1223062562782838815>"), #
        discord.SelectOption(label="Tags", value="Tags", emoji="<:tags:1234994806829355169>"),  #
        discord.SelectOption(label="Connection Roles", value="Connection Roles", emoji="<:link:1206670134064717904>"), #
        discord.SelectOption(label="Suspensions", value="Suspensions", emoji="<:suspensions:1234998406938755122>"), #
        discord.SelectOption(label="LOA", value="LOA", emoji=f"{loa}"), #
        discord.SelectOption(label="Staff Feedback", value="Staff Feedback", emoji="<:stafffeedback:1235000485208002610>"), 
        discord.SelectOption(label="Partnerships", value="Partnerships", emoji="<:partnerships:1224724406144733224>"), #
        discord.SelectOption(label="Reports", value="Reports", emoji="<:reports:1224723845726998651>"), #
        discord.SelectOption(label="Applications Results", value="Applications Results", emoji="<:Application:1224722901328986183>") #
        ]
        super().__init__(placeholder='Data Select', min_values=1, max_values=1, options=options,)

    async def callback(self, interaction: discord.Interaction):
        data_type = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if data_type == 'Infractions':
            view = Infractions(interaction.user)
            view.add_item(DataSelector(interaction.user))

            embed = discord.Embed(title="Infraction Data", description="**Erase Infractions:** This will erase all infractions. This will not remove already posted infraction messages.\n**Erase Infraction Types:** Reset the infraction types back to default.\n**Erase Infraction Config:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'LOA':
                view = LOAs(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="LOA Data", description="**Erase Partnerships:** This will erase all LOA data. The LOA role will not be removed from people who are actively on LOA.\n**Erase LOA Config:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Welcome':
                view = Welcome(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="LOA Data", description="**Erase Welcome Config:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)                
        elif data_type == 'Partnerships':
                view = Partnerships(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Partnerships Data", description="**Erase Partnerships:** This will erase all partnership data. Every partnership message will be deleted. Logged partnership message posts won't be deleted, only the data.\n**Erase Partnership Config:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Custom Commands':
                view = CustomCommands(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Commands Data", description="**Erase Commands:** This will erase all custom commands.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Modmail':
                view = Modmail(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Modmail Data", description="**Erase Modmail Configuration:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Quota':
                view = Quota(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Quota Data", description="**Erase Message Count:** This will erase the server's leaderboard.\n**Erase Quota Configuration:** This will reset the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Suggestions':
                view = Suggestions(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Suggestions Data", description="**Erase Suggestions:** This will erase all suggestions. This will make all suggestions stop working in your server.\n**Erase Suggestions Config:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Forums Autopost + Utils':
                view = Forums(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Forums Data", description="**Erase Forums Autopost:** This will erase all forums autoposts.\n**Erase Forums Configuration:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Tags':
                view = Tags(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Tags Data", description="**Erase Tags:** This will erase all created tags.\n**Erase Tags Configuration:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Connection Roles':
                view = ConnectionRoles(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Connection Roles Data", description="**Erase Connection Roles:** This will erase all connection roles.\n**Erase Connection Roles Configuration:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Suspensions':
                view = Suspensions(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Suspensions Data", description="**Erase Suspensions:** This will erase all suspensions. This will not give back their roles and will not remove suspension posts.\n**Erase Suspensions Configuration:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Staff Feedback':
                view = StaffFeedback(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Staff Feedback Data", description="**Erase Staff Feedback:** This will erase all staff feedback. This will not remove already posted feedback messages.\n**Erase Staff Feedback Configuration:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Reports':
                view = Reports(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Reports Data", description="**Erase Reports:** This will erase all reports. This will make all reports in your server uninteractive.\n**Erase Reports Configuration:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Applications Results':
                view = Applications(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Applications Results Data", description="**Erase Applications Results Configuration:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Promotions':
                view = Promotions(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Promotions Data", description="**Erase Promotions Configuration:** This will erase the configuration for this module.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)
        elif data_type == 'Staff Database & Panel':
                view = StaffPanel(interaction.user)
                view.add_item(DataSelector(interaction.user))
                embed = discord.Embed(title="Staff Database & Panel Data", description="**Erase Staff Database:** This will erase the configuration for this module.\n**Erase Staff Database:** This will delete all staff members data.", color=discord.Color.dark_embed())
                embed.set_thumbnail(url=interaction.guild.icon)
                embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
                await interaction.response.edit_message(embed=embed, view=view)



class datamanage(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_group(name="data", description="Data Management Commands")
    async def data(self, ctx: commands.Context):
        pass

    @data.command(name="manage", description="Manage your servers data.")
    @commands.has_permissions(administrator=True)
    async def manage(self, ctx: commands.Context):

        embed = discord.Embed(title="Data Portal", description="The Data Portal is a place where you can manage your server data. You can erase data and reset configurations for modules.", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        embed.set_footer(text=f"ID: {ctx.guild.id} | Data Portal", icon_url=self.client.user.display_avatar)
        view = DataView(ctx.author)
        await ctx.send(embed=embed, view=view)

    @manage.error
    async def permissionerror(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to manage data in this server.\n<:Arrow:1115743130461933599>**Required:** ``Administrator``")         
            return       

class Infractions(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Erase Infractions", style=discord.ButtonStyle.red, row=0)
    async def eraseinfractions(self, interaction: discord.Interaction,  button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await infractions.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Infractions have been erased.", ephemeral=True)


    @discord.ui.button(label="Reset Infraction Types", style=discord.ButtonStyle.red, row=1)
    async def erasetypes(self, interaction: discord.Interaction,  button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await infractiontypes.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'types': ['Activity Notice', 'Verbal Warning', 'Warning', 'Strike', 'Demotion', 'Termination']}}, upsert=True)
        await infractiontypeactions.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Infractions types have been erased.", ephemeral=True)

    @discord.ui.button(label="Erase Infraction Configuration", style=discord.ButtonStyle.red, row=2)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)     
        await interaction.response.defer()   
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'infractions': False}})
        except:
            pass
        await infchannel.delete_many({'guild_id': int(interaction.guild.id)})
        await infractiontypes.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'types': ['Activity Notice, Verbal Warning, Warning, Strike, Demotion, Termination']}}, upsert=True)
        await infractiontypeactions.delete_many({'guild_id': int(interaction.guild.id)})   
        await interaction.followup.send("<:whitecheck:1223062421212631211> Infractions configuration have been erased.", ephemeral=True)




class Partnerships(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Erase Partnerships", style=discord.ButtonStyle.red, row=0)
    async def erasepartnerships(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)             
        await interaction.response.defer()
        await partnerships.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Infractions configuration have been erased.", ephemeral=True)


        

    @discord.ui.button(label="Erase Partnership Configuration", style=discord.ButtonStyle.red, row=1)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)             
        await interaction.response.defer()        
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Partnerships': False}})
        except:
            pass
        await partnershipch.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Partnership configuration have been erased.", ephemeral=True)
class Welcome(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author


    @discord.ui.button(label="Erase Welcome Configuration", style=discord.ButtonStyle.red, row=0)
    async def eraseconfig(self,interaction: discord.Interaction,  button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'welcome': False}})
        except:
            pass
        await welcome.delete_one({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Welcome configuration have been erased.", ephemeral=True)

class LOAs(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Erase LOAs ", style=discord.ButtonStyle.red, row=0)
    async def eraseloa(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.response.defer()
        await loa_collection.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> LOAs have been erased.", ephemeral=True)

    @discord.ui.button(label="Erase LOA Configuration", style=discord.ButtonStyle.red, row=1)
    async def eraseconfig(self,interaction: discord.Interaction,  button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'LOA': False}})
        except:
            pass
        await loachannel.delete_many({'guild_id': int(interaction.guild.id)})
        await LOARole.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> LOA configuration have been erased.", ephemeral=True)
class CustomCommands(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        
    @discord.ui.button(label="Erase Commands", style=discord.ButtonStyle.red, row=0)
    async def erasecommands(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.response.defer()
        await customcommands.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Custom commands have been erased.", ephemeral=True)

class Modmail(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        
    @discord.ui.button(label="Erase Modmail Configuration", style=discord.ButtonStyle.red, row=0)
    async def erasemodmail(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Modmail': False}})
        except:
            pass
        await transcriptchannel.delete_many({'guild_id': int(interaction.guild.id)})
        await modmailcategory.delete_many({'guild_id': int(interaction.guild.id)})
        await modmailping.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Modmail Configuration Reset", ephemeral=True)

class Quota(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        
    @discord.ui.button(label="Erase Message Count", style=discord.ButtonStyle.red, row=0)
    async def erasequota(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await mccollection.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Message Quota has been erased.", ephemeral=True)

    @discord.ui.button(label="Erase Quota Configuration", style=discord.ButtonStyle.red, row=1)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Quota': False}})
        except:
            pass
        await message_quota_collection.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Quota Configuration Reset", ephemeral=True)    

class Suggestions(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
    
    @discord.ui.button(label="Erase Suggestions", style=discord.ButtonStyle.red, row=0)
    async def erasesuggestions(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await suggestions_collection.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Suggestions have been erased.", ephemeral=True)
        
    @discord.ui.button(label="Erase Suggestions Configuration", style=discord.ButtonStyle.red, row=1)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Suggestions': False}})
        except:
            pass
        await suggestschannel.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Suggestions Configuration Reset", ephemeral=True)    

class Forums(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Erase Forums Autopost", style=discord.ButtonStyle.red, row=0)
    async def eraseforums(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await forumsconfig.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Forums Autoposts have been erased.", ephemeral=True)

    @discord.ui.button(label="Erase Forums Configuration", style=discord.ButtonStyle.red, row=1)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Forums': False}})
        except:
            pass

        await interaction.followup.send("<:whitecheck:1223062421212631211> Forums Configuration Reset", ephemeral=True)
    
class Tags(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author


    @discord.ui.button(label="Erase Tags", style=discord.ButtonStyle.red, row=0)
    async def erasetags(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await tags.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Tags have been erased.", ephemeral=True)    

    @discord.ui.button(label="Erase Tags Configuration", style=discord.ButtonStyle.red, row=1)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Tags': False}})
        except:
            pass
        await interaction.followup.send("<:whitecheck:1223062421212631211> Tags Configuration Reset", ephemeral=True)    

class ConnectionRoles(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Erase Connection Roles", style=discord.ButtonStyle.red, row=0)    
    async def eraseconnectionroles(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await connectionroles.delete_many({'guild': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Connection Roles have been erased.", ephemeral=True)

    @discord.ui.button(label="Erase Connection Roles Configuration", style=discord.ButtonStyle.red, row=1)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Connection': False}})
        except:
            pass
        await interaction.followup.send("<:whitecheck:1223062421212631211> Connection Roles Configuration Reset", ephemeral=True)    
     
class Suspensions(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Erase Suspensions", style=discord.ButtonStyle.red, row=0)
    async def erasesuspensions(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await suspensions.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Suspensions have been erased.", ephemeral=True)

    @discord.ui.button(label="Erase Suspensions Configuration", style=discord.ButtonStyle.red, row=1)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Suspensions': False}})
        except:
            pass
        await interaction.followup.send("<:whitecheck:1223062421212631211> Suspensions Configuration Reset", ephemeral=True)    

class StaffFeedback(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Erase Staff Feedback", style=discord.ButtonStyle.red, row=0)
    async def erasestafffeedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await stafffeedback.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Staff Feedback have been erased.", ephemeral=True)

    @discord.ui.button(label="Erase Staff Feedback Configuration", style=discord.ButtonStyle.red, row=1)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Feedback': False}})
        except:
            pass
        await interaction.followup.send("<:whitecheck:1223062421212631211> Staff Feedback Configuration Reset", ephemeral=True)        

class Reports(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Erase Reports", style=discord.ButtonStyle.red, row=0)
    async def erasereports(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await reports.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Reports have been erased.", ephemeral=True)    

    @discord.ui.button(label="Erase Reports Configuration", style=discord.ButtonStyle.red, row=1)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Reports': False}})
        except:
            pass
        await repchannel.delete_many({'guild_id': int(interaction.guild.id)})
        await ReportModeratorRole.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Reports Configuration Reset", ephemeral=True)    

class Applications(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author


    @discord.ui.button(label="Erase Applications Configuration", style=discord.ButtonStyle.red, row=0)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Applications': False}})
        except:
            pass
        await ApplicationsChannel.delete_many({'guild_id': int(interaction.guild.id)})
        await ApplicationsRolesDB.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Applications Configuration Reset", ephemeral=True)

class Promotions(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Erase Promotions", style=discord.ButtonStyle.red, row=0)
    async def eraseinfractions(self, interaction: discord.Interaction,  button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await promotionroles.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Promotions have been erased.", ephemeral=True)
    
    @discord.ui.button(label="Erase Promotions Ranks", style=discord.ButtonStyle.red, row=0)
    async def erasepromotionroles(self, interaction: discord.Interaction,  button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await promotions.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Promotions roles have been erased.", ephemeral=True)

    @discord.ui.button(label="Erase Promotions Configuration", style=discord.ButtonStyle.red, row=0)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Promotions': False}})
        except:
            pass
        await promochannel.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Promotions Configuration Reset", ephemeral=True)    

class StaffPanel(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Erase Staff Database Configuration", style=discord.ButtonStyle.red, row=0)
    async def eraseconfig(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        try:
         await modules.update_one({'guild_id': int(interaction.guild.id)}, {'$set': {'Staff Database': False}})
        except Exception as e:
            print(f"Failed to reset Staff Database Configuration: {e}")

        await interaction.followup.send("<:whitecheck:1223062421212631211> Staff Database Configuration Reset", ephemeral=True)

    @discord.ui.button(label="Erase Staff Database", style=discord.ButtonStyle.red, row=1)
    async def erasestaff(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view.",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        await interaction.response.defer()
        await staffdb.delete_many({'guild_id': int(interaction.guild.id)})
        await interaction.followup.send("<:whitecheck:1223062421212631211> Staff Database have been erased.", ephemeral=True)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(datamanage(client))     
