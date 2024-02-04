from typing import Optional
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from emojis import *
from Cogs.Configuration.Views.infractionsview import InfractionChannel

from Cogs.Configuration.Views.infractionsview import ToggleInfractionsDropdown
from Cogs.Configuration.Views.Utilityview import ToggleUtils

from Cogs.Configuration.Views.promotionsview import Promotionchannel
from Cogs.Configuration.Views.promotionsview import PromotionModuleToggle

from Cogs.Configuration.Views.loaview import LOAChannel
from Cogs.Configuration.Views.loaview import ToggleLOADropdown
from Cogs.Configuration.Views.loaview import LOARoled

from Cogs.Configuration.Views.tagsview import ToggleTags

from Cogs.Configuration.Views.quotaview import QuotaToggle
from Cogs.Configuration.Views.quotaview import QuotaAmount

from Cogs.Configuration.Views.feedbackview import FeedbackChannel
from Cogs.Configuration.Views.feedbackview import ToggleFeedback

from Cogs.Configuration.Views.suspensionsview import ToggleSuspensions

from Cogs.Configuration.Views.partnershipsview import PartnershipChannel
from Cogs.Configuration.Views.partnershipsview import TogglePartnerships

from Cogs.Configuration.Views.forumsview import ToggleForums

from Cogs.Configuration.Views.reportview import ReportChannel
from Cogs.Configuration.Views.reportview import ToggleReportsDropdown
from Cogs.Configuration.Views.reportview import ReportsModeratorRole

from Cogs.Configuration.Views.applicationsview import ApplicationChannel
from Cogs.Configuration.Views.applicationsview import ApplicationsRoles
from Cogs.Configuration.Views.applicationsview import ToggleApplications



from Cogs.Configuration.Views.suggestionview import SuggestionsChannel
from Cogs.Configuration.Views.suggestionview import ToggleSuggestions

from Cogs.Configuration.Views.connectionrolesview import ToggleConnectionRoles

from Cogs.Configuration.Views.Customationview import CustomEmbeds
from Cogs.Configuration.Views.Customationview import ResetEmbeds
from Cogs.Configuration.Views.infractionsview import InfractionTypes

from Cogs.Configuration.Views.CustomCommandsView  import CreateButtons
from Cogs.Configuration.Views.CustomCommandsView  import ToggleCommands
from Cogs.Configuration.Views.modmailview import ModmailCategory
from Cogs.Configuration.Views.modmailview import ModmailPing
from Cogs.Configuration.Views.modmailview import TranscriptChannel
from Cogs.Configuration.Views.modmailview import ModmailToggle
MONGO_URL = os.getenv('MONGO_URL')

mongo = MongoClient(MONGO_URL)
quota = MongoClient(MONGO_URL)
dbq = quota['quotab']
message_quota_collection = dbq["message_quota"]



db = mongo['astro']
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
partnershipch = db['Partnerships Channel']
modules = db['Modules']
nfractiontypes = db['infractiontypes']

ApplicationsChannel = db['Applications Channel']
ApplicationsRolesDB = db['Applications Roles']
ReportModeratorRole = db['Report Moderator Role']
mongo2 = MongoClient('mongodb://bugsbirt:deezbird2768@172.93.103.8:55199/?authMechanism=SCRAM-SHA-256&authSource=admin')
db2 = mongo2['quotab']
scollection2 = db2['staffrole']
message_quota_collection = db2["message_quota"]
arole2 = db2['adminrole']
srole = db2['staffrole']
suggestschannel = db["suggestion channel"]
customcommands = db['Custom Commands']
modmailcategory = db['modmailcategory']
transcriptchannel = db['transcriptschannel']
modmailping = db['modmailping']
class StaffRole(discord.ui.RoleSelect):
    def __init__(self, author):

        super().__init__(placeholder='Staff Roles', max_values=20)
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
        filter = {
            'guild_id': interaction.guild.id
        }        
        data = {
            'guild_id': interaction.guild.id, 
            'staffrole': selected_role_ids
        }
        try:
            existing_record = scollection.find_one(filter)
            if existing_record:
                scollection.update_one(filter, {'$set': data})
            else:
                scollection.insert_one(data)
            await refreshembed(interaction)    
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        print(f"Select Roles {selected_role_ids}")

class Adminrole(discord.ui.RoleSelect):
    def __init__(self, author):
        super().__init__(placeholder='Admin Roles', max_values=20)
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
  
        data = {
            'guild_id': interaction.guild.id,
            'staffrole': selected_role_ids
        }


        arole.update_one({'guild_id': interaction.guild.id}, {'$set': data}, upsert=True)
        await refreshembed(interaction)  
        await interaction.response.edit_message(content=None)
        print(f"Select Roles {selected_role_ids}")



                

class Config(discord.ui.Select):
    def __init__(self, author):
        self.author = author

        
        options = [
        discord.SelectOption(label="Settings", value="Settings", emoji="<:Setting:1154092651193323661>", description=self.permissionsconfig(author)),
        discord.SelectOption(label="Infractions", value="Infractions", emoji="<:Remove:1162134605885870180>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'infractions': True}) else "Disabled"),
        discord.SelectOption(label="Promotions", value="Promotions", emoji="<:Promote:1162134864594735315>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Promotions': True}) else "Disabled"),
        discord.SelectOption(label="Customisation", value="Customisation", emoji="<:Customisation:1195037906620911717>"),
        discord.SelectOption(label="Custom Commands", value="Custom Commands", emoji="<:command1:1199456319363633192>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'customcommands': True}) else "Disabled"),
        discord.SelectOption(label="Modmail", value="Modmail", emoji="<:messagereceived:1201999712593383444>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Modmail': True}) else "Disabled"),
        discord.SelectOption(label="Message Quota", value="Message Quota", emoji="<:Messages:1148610048151523339>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Quota': True}) else "Disabled"),
        discord.SelectOption(label="Suggestions", value="Suggestions", emoji="<:UpVote:1183063056834646066>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Suggestions': True}) else "Disabled"),
        discord.SelectOption(label="Forums Utils", value="Forum Utils", emoji="<:forum:1162134180218556497>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Forums': True}) else "Disabled"),
        discord.SelectOption(label="Tags", value="Tags", emoji="<:tag:1162134250414415922>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Tags': True}) else "Disabled"),
        discord.SelectOption(label="Connection Roles", value="Connection Roles", emoji="<:Role:1162074735803387944>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Connection': True}) else "Disabled"),
        discord.SelectOption(label="Suspensions", value="Suspensions", emoji="<:Suspensions:1167093139845165229>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Suspensions': True}) else "Disabled"),
        discord.SelectOption(label="Utility", value="Utility", emoji="<:Folder:1148813584957194250>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Utility': True}) else "Disabled"),
        discord.SelectOption(label="LOA", value="LOA", emoji="<:LOA:1164969910238203995>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'LOA': True}) else "Disabled"),
        discord.SelectOption(label="Staff Feedback", value="Staff Feedback", emoji="<:Rate:1162135093129785364>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Feedback': True}) else "Disabled"),
        discord.SelectOption(label="Partnerships", value="Partnerships", emoji="<:Partner:1162135285031772300>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Partnerships': True}) else "Disabled"),
        discord.SelectOption(label="Reports", value="Reports", emoji="<:Moderation:1163933000006893648>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Reports': True}) else "Disabled"),
        discord.SelectOption(label="Applications Results", value="Applications Results", emoji="<:ApplicationFeedback:1178754449125167254>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Applications': True}) else "Disabled")
]

        super().__init__(placeholder='Config Menu', min_values=1, max_values=1, options=options)

    def permissionsconfig(self, author):
     actionrequired = None
    
     if not scollection.find_one({'guild_id': author.guild.id}):
        actionrequired = "Action Required: Staff Role"
     if not arole.find_one({'guild_id': author.guild.id}):
        if actionrequired:
            actionrequired += " and Admin Role"
        else:
            actionrequired = "Action Required: Admin Role"       

     return actionrequired        


    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        if color == 'Settings':  # basic
            staffroleresult = scollection.find_one({'guild_id': interaction.guild.id})
            adminroleresult = arole.find_one({'guild_id': interaction.guild.id})
            staffrolemessage = "Not Configured"
            adminrolemessage = "Not Configured"

            if adminroleresult:
             admin_roles_ids = adminroleresult.get('staffrole', [])
             if not isinstance(admin_roles_ids, list):
                admin_roles_ids = [admin_roles_ids]
             admin_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention
                                    for role_id in admin_roles_ids if discord.utils.get(interaction.guild.roles, id=role_id) is not None]
             if not admin_roles_mentions:
                adminrolemessage = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
             else:
                adminrolemessage = ", ".join(admin_roles_mentions)

            if staffroleresult:
             staff_roles_ids = staffroleresult.get('staffrole', [])
             if not isinstance(staff_roles_ids, list):
                staff_roles_ids = [staff_roles_ids]
             staff_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention
                                    for role_id in staff_roles_ids if discord.utils.get(interaction.guild.roles, id=role_id) is not None]
             if not staff_roles_mentions:
                staffrolemessage = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
             else:
                staffrolemessage = ", ".join(staff_roles_mentions)
            embed = discord.Embed(title="<:Setting:1154092651193323661> Settings",
                                  description=f"**Staff Role:** {staffrolemessage}\n**Admin Role:** {adminrolemessage}",
                                  color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            view = ConfigViewMain(self.author)        


        elif color == 'Infractions':    #infractionss
            infractionchannelresult = infchannel.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            infchannelmsg = ""
            infractiontypess = "Activity Notice, Verbal Warning, Warning, Strike, Demotion, Termination"
            infractiontyperesult = nfractiontypes.find_one({'guild_id': interaction.guild.id})
            if infractiontyperesult:
                infractiontypess = infractiontyperesult['types']
                infractiontypess = ', '.join(infractiontypess)
                
            if moduleddata:
                modulemsg = f"{moduleddata['infractions']}"
            if infractionchannelresult:    
                channelid = infractionchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    infchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else:    
                 infchannelmsg = channel.mention          

            infractiontypescount = len(infractiontyperesult['types'])
            embed = discord.Embed(title="<:Infraction:1162134605885870180> Infractions Module", description=f"**Enabled:** {modulemsg}\n**Infraction Channel:** {infchannelmsg}\n**Infraction Types [{infractiontypescount}/15]** {infractiontypess}", color=discord.Color.dark_embed())
            view = InfractModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)                 



        elif color == 'Utility':         # Utility
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Utility']}"            
            embed = discord.Embed(title="<:Pen:1126527802255085628> Utilties Module", description=f"**Enabled:** {modulemsg}", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
            view = UtilsModule(self.author)

        elif color == 'Promotions': #Promos
            promochannelresult = promochannel.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            promochannelmsg = "Not Configured"
            if moduleddata:
                modulemsg = f"{moduleddata['Promotions']}"
            if promochannelresult:    
                channelid = promochannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                 promochannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else: 
                 promochannelmsg = channel.mention                          
            embed = discord.Embed(title="<:Promote:1162134864594735315> Promotions Module", description=f"**Enabled:** {modulemsg}\n**Promotion Channel:** {promochannelmsg}", color=discord.Color.dark_embed())
            view = PromotionModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)                   
        elif color == 'LOA':    #LOA
            loachannelresult = loachannel.find_one({'guild_id': interaction.guild.id})
            loaroleresult = LOARole.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            loarolemsg = "Not Configured"
            loachannelmsg = "Not Configured"
            if moduleddata:
                modulemsg = f"{moduleddata['LOA']}"
            if loaroleresult:    
                roleid = loaroleresult['staffrole']
                role = discord.utils.get(interaction.guild.roles, id=roleid)
                if role is None:
                 loarolemsg = "<:Error:1126526935716085810> Role wasn't found please reconfigure."
                else: 
                 loarolemsg = f"{role.mention}"

            if loachannelresult:     
                channelid = loachannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    loachannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else:    
                 loachannelmsg = channel.mention       
            embed = discord.Embed(title="<:LOA:1164969910238203995> LOA Module", description=f"**Enabled:** {modulemsg}\n**LOA Channel:** {loachannelmsg}\n**LOA Role:** {loarolemsg}", color=discord.Color.dark_embed())
            view = LOAModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    
        elif color == 'Tags':         # Tags
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Tags']}"            
            embed = discord.Embed(title="<:tag:1162134250414415922> Tags Module", description=f"**Enabled:** {modulemsg}", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
            view = TagsModule(self.author)

        elif color == 'Message Quota':         # Tags
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            messagequotdata = message_quota_collection.find_one({'guild_id': interaction.guild.id})
            messagecountmsg = "Not Configured"
            if messagequotdata:
                messagecountmsg = f"{messagequotdata['quota']}"
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Quota']}"            
            embed = discord.Embed(title="<:Messages:1148610048151523339> Message Quota Module", description=f"**Enabled:** {modulemsg}\n**Quota:** {messagecountmsg}", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
            view = QuotaModule(self.author)

        elif color == 'Staff Feedback':    #StaffFeed
            feedbackchannelresult = feedbackch.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            feedbackchannelmsg = "Not Configured"
            if moduleddata:
                modulemsg = f"{moduleddata['Feedback']}"
            if feedbackchannelresult:    
                channelid = feedbackchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    feedbackchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else:    
                 feedbackchannelmsg = channel.mention                
            embed = discord.Embed(title="<:Rate:1162135093129785364> Staff Feedback Module", description=f"**Enabled:** {modulemsg}\n**Feedback Channel:** {feedbackchannelmsg}", color=discord.Color.dark_embed())
            view = FeedbackModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   

        elif color == 'Suspensions':         # Tags
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Suspensions']}"            
            embed = discord.Embed(title="<:Suspensions:1167093139845165229> Suspension Module", description=f"**Enabled:** {modulemsg}\n**Channel:** Same as the infraction channel", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
            view = SuspensionsModule(self.author)




        elif color == 'Partnerships':    #Partnerships
            partnershipchannelresult = partnershipch.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            partnershipchannelmsg = "Not Configured"
            if moduleddata:
                modulemsg = f"{moduleddata['Partnerships']}"
            if partnershipchannelresult:    
                channelid = partnershipchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel:
                 partnershipchannelmsg = f"{channel.mention}"                     
                else:
                 partnershipchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
            embed = discord.Embed(title="<:Partner:1162135285031772300> Partnership Module", description=f"**Enabled:** {modulemsg}\n**Partnership Channel:** {partnershipchannelmsg}", color=discord.Color.dark_embed())
            view = PartnershipModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
        elif color == 'Forum Utils':         # Tags
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Forums']}"            
            embed = discord.Embed(title="<:forum:1162134180218556497> Forum Utilites", description=f"**Enabled:** {modulemsg}", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
            view = ForumUtilsModule(self.author)

        elif color == 'Reports':    #Reports
            partnershipchannelresult = repchannel.find_one({'guild_id': interaction.guild.id})
            reportsmoderatorresult = ReportModeratorRole.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            partnershipchannelmsg = "Not Configured"
            reprolemsg = "Not Configured"
            if moduleddata:
                modulemsg = f"{moduleddata['Reports']}"
            if partnershipchannelresult:    
                channelid = partnershipchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                 partnershipchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else: 
                 partnershipchannelmsg = channel.mention    

            if reportsmoderatorresult:    
                roleid = reportsmoderatorresult['staffrole']
                role = discord.utils.get(interaction.guild.roles, id=roleid)
                if role is None:
                 reprolemsg = "<:Error:1126526935716085810> Role wasn't found please reconfigure."
                else: 
                 reprolemsg = f"{role.mention}"
            embed = discord.Embed(title="<:Moderation:1163933000006893648> Reports Module", description=f"**Enabled:** {modulemsg}\n**Reports Channel:** {partnershipchannelmsg}\n**Reports Moderator Role:** {reprolemsg}", color=discord.Color.dark_embed())
            view = ReportsModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
        elif color == 'Applications Results':            


            applicationchannelresult = ApplicationsChannel.find_one({'guild_id': interaction.guild.id})
            staffroleresult = ApplicationsRolesDB.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})

            approlemsg = "Not Configured"
            appchannelmsg = "Not Configured"

            if moduleddata:
                modulemsg = moduleddata.get('Applications', 'False')
            else:
                modulemsg = 'False'

            if staffroleresult:
                staff_roles_ids = staffroleresult.get('applicationroles', [])
                if not isinstance(staff_roles_ids, list):
                    staff_roles_ids = [staff_roles_ids]
                staff_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention
                                        for role_id in staff_roles_ids if discord.utils.get(interaction.guild.roles, id=role_id) is not None]
                if not staff_roles_mentions:
                    approlemsg = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
                else:
                    approlemsg = ", ".join(staff_roles_mentions)


            if applicationchannelresult:
                channelid = applicationchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    appchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else:
                    appchannelmsg = channel.mention

            embed = discord.Embed(title="<:ApplicationFeedback:1178754449125167254> Applications Result Module",
                                   description=f"**Enabled:** {modulemsg}\n**Results Channel:** {appchannelmsg}\n**Application Roles:** {approlemsg}",
                                   color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            view = AppResultModule(self.author)

        elif color == 'Connection Roles':         # 
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            modulemsg = "True"
            if moduleddata:
                modulemsg = moduleddata.get('Connection', 'False')
            else:
                modulemsg = 'False'        
            embed = discord.Embed(title="<:Role:1162074735803387944> Connection Roles Module", description=f"**Enabled:** {modulemsg}", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
            view = ConnectionsModule(self.author)


        elif color == 'Suggestions':    # Suggestions
            suschannelresult = suggestschannel.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            suggestionchannelmsg = "Not Configured"
            if moduleddata:
                modulemsg = moduleddata.get('Suggestions', 'False')
            if suschannelresult:    
                channelid = suschannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                 suggestionchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else: 
                 suggestionchannelmsg = channel.mention                
            embed = discord.Embed(title="<:Moderation:1163933000006893648> Suggestions Module", description=f"**Enabled:** {modulemsg}\n**Suggestion Channel:** {suggestionchannelmsg}", color=discord.Color.dark_embed())
            view = SuggestionModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   

        elif color == 'Customisation':
            embed = discord.Embed(title="<:Customisation:1195037906620911717> Customisation", description="From here you can edit **promotions, infraction** embeds", color=discord.Color.dark_embed())
            view = CustomisatiomModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    

        elif color == 'Custom Commands':
            commands = customcommands.find({'guild_id': interaction.guild.id})
            
            amount = customcommands.count_documents({'guild_id': interaction.guild.id})
            embed = discord.Embed(title=f"<:command1:1199456319363633192> Custom Commands ({amount}/30)", description="", color=discord.Color.dark_embed())
            for result in commands:
                embed.add_field(name=f"<:command1:1199456319363633192> {result['name']}", value=f"<:arrow:1166529434493386823> **Created By:** <@{result['creator']}>", inline=False)
               
            view = CustomCommands(self.author)
            
        elif color =='Modmail':
            transcriptschannelresult = transcriptchannel.find_one({'guild_id': interaction.guild.id})
            modmailcategoryresult = modmailcategory.find_one({'guild_id': interaction.guild.id})
            transcriptschannels = "Not Configured"
            modmailcategorys = "Not Configured"
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            suggestionchannelmsg = "Not Configured"
            if moduleddata:
                modulemsg = moduleddata.get('Modmail', 'False')            
            modmailpingresult = modmailping.find_one({'guild_id': interaction.guild.id})
            modmailroles = "Not Configured"
            if modmailpingresult:
                modmailroles = [f'<@&{roleid}>' for sublist in modmailpingresult['modmailping'] for roleid in sublist if interaction.guild.get_role(roleid) is not None]
                if not modmailroles:
                    modmailroles = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
                modmailroles = ", ".join(filter(None, modmailroles))

            if transcriptschannelresult:
                transcriptschannels = f"<#{transcriptschannelresult['channel_id']}>"
            if modmailcategoryresult:
                modmailcategorys = f"<#{modmailcategoryresult['category_id']}>"    
            embed = discord.Embed(title="<:messagereceived:1201999712593383444> Modmail", description=f"**Enabled:** {modulemsg}\n**Modmail Category:** {modmailcategorys}\n**Modmail Pings:** {modmailroles}\n**Transcript Channel:** {transcriptschannels}", color=discord.Color.dark_embed())
            view = Modmail(interaction.user)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
        await interaction.edit_original_response(embed=embed, view=view)

     

class ConfigViewMain(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(StaffRole(author))
        self.add_item(Adminrole(author))
        self.add_item(Config(author))

class SuggestionModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(SuggestionsChannel(author))
        self.add_item(ToggleSuggestions(author))
        self.add_item(Config(author))

class CustomCommands(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(ToggleCommands(author))
        self.add_item(CreateButtons(author))
        self.add_item(Config(author))

class Modmail(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(ModmailToggle(author))
        self.add_item(ModmailCategory(author))
        self.add_item(ModmailPing(author))
        self.add_item(TranscriptChannel(author))
        self.add_item(Config(author))




class InfractModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.add_item(InfractionChannel(author))
        self.add_item(ToggleInfractionsDropdown(author))     
        self.add_item(InfractionTypes(author))   
        self.add_item(Config(author))        

class UtilsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.add_item(ToggleUtils(author))
        self.add_item(Config(author))        

class PromotionModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.add_item(Promotionchannel(author))
        self.add_item(PromotionModuleToggle(author))        
        self.add_item(Config(author))    

class LOAModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(LOARoled(author))
        self.add_item(LOAChannel(author))        
        self.add_item(ToggleLOADropdown(author))              
        self.add_item(Config(author))    

class TagsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(ToggleTags(author))         
        self.add_item(Config(author)) 

class QuotaModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(QuotaAmount(author))          
        self.add_item(QuotaToggle(author))         
        self.add_item(Config(author)) 

class FeedbackModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(FeedbackChannel(author))          
        self.add_item(ToggleFeedback(author))         
        self.add_item(Config(author)) 

class SuspensionsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(ToggleSuspensions(author))               
        self.add_item(Config(author)) 

class PartnershipModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(PartnershipChannel(author))            
        self.add_item(TogglePartnerships(author))               
        self.add_item(Config(author)) 

class ForumUtilsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(ToggleForums(author))                          
        self.add_item(Config(author)) 

class ReportsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()     
        self.add_item(ReportChannel(author))         
        self.add_item(ReportsModeratorRole(author))
        self.add_item(ToggleReportsDropdown(author))                          
        self.add_item(Config(author)) 

class AppResultModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(ApplicationChannel(author))         
        self.add_item(ApplicationsRoles(author))             
        self.add_item(ToggleApplications(author))                          
        self.add_item(Config(author)) 



class ConnectionsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(ToggleConnectionRoles(author))         
        self.add_item(Config(author)) 

class CustomisatiomModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(CustomEmbeds(author))     
        self.add_item(ResetEmbeds(author))       
        self.add_item(Config(author)) 


  

class ConfigCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(description="Configure the bot for your servers needs")
    @commands.has_guild_permissions(administrator=True)
    async def config(self, ctx):
        await ctx.defer()
        staffroleresult = scollection.find_one({'guild_id': ctx.guild.id})
        types = nfractiontypes.find_one({'guild_id': ctx.guild.id})
        if types is None:
            nfractiontypes.insert_one({"guild_id": ctx.guild.id, "types": ['Activity Notice', 'Verbal Warning', 'Warning', 'Strike', 'Demotion', 'Termination']})

        adminroleresult = arole.find_one({'guild_id': ctx.guild.id})
        modulesdata = modules.find_one({'guild_id': ctx.guild.id})
        if modulesdata is None:
            modulesdata = {'guild_id': ctx.guild.id, 'infractions': False, "Forums": False, "Suspensions": False, "Promotions": False, "Utility": True, "LOA": False, "Tags": False, "Partnerships": False, "Quota": False, "Feedback": False, 'Reports': False, 'Applications': False, 'StaffList': False, 'Suggestions': False, 'Connection': False  }
            modules.insert_one({'guild_id': ctx.guild.id, 'infractions': False, "Forums": False, "Suspensions": False, "Promotions": False, "Utility": True, "LOA": False, "Tags": False, "Partnerships": False, "Quota": False, "Feedback": False, 'Reports': False, 'Applications': False, 'StaffList': False, 'Suggestions': False, 'Connection': False  })
        staffrolemessage = "Not Configured"
        adminrolemessage = "Not Configured"
        if adminroleresult:
            admin_roles_ids = adminroleresult.get('staffrole', [])
            if not isinstance(admin_roles_ids, list):
                admin_roles_ids = [admin_roles_ids]
            admin_roles_mentions = [discord.utils.get(ctx.guild.roles, id=role_id).mention
                                    for role_id in admin_roles_ids if discord.utils.get(ctx.guild.roles, id=role_id) is not None]
            if not admin_roles_mentions:
                adminrolemessage = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
            else:
                adminrolemessage = ", ".join(admin_roles_mentions)
        
        if staffroleresult:
            staff_roles_ids = staffroleresult.get('staffrole', [])
            if not isinstance(staff_roles_ids, list):
                staff_roles_ids = [staff_roles_ids]
            staff_roles_mentions = [discord.utils.get(ctx.guild.roles, id=role_id).mention
                                    for role_id in staff_roles_ids if discord.utils.get(ctx.guild.roles, id=role_id) is not None]
            if not staff_roles_mentions:
                staffrolemessage = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
            else:
                staffrolemessage = ", ".join(staff_roles_mentions)
        
        embed = discord.Embed(title="<:Setting:1154092651193323661> Settings", description=f"**Staff Role:** {staffrolemessage}\n**Admin Role:** {adminrolemessage}", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        await ctx.send(embed=embed, view = ConfigViewMain(ctx.author))

    @config.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to configure this server.\n<:Arrow:1115743130461933599>**Required:** ``Administrator``")              

async def refreshembed(interaction):
            staffroleresult = scollection.find_one({'guild_id': interaction.guild.id})
            adminroleresult = arole.find_one({'guild_id': interaction.guild.id})
            staffrolemessage = "Not Configured"
            adminrolemessage = "Not Configured"

            if adminroleresult:
             admin_roles_ids = adminroleresult.get('staffrole', [])
             if not isinstance(admin_roles_ids, list):
                admin_roles_ids = [admin_roles_ids]
             admin_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention
                                    for role_id in admin_roles_ids if discord.utils.get(interaction.guild.roles, id=role_id) is not None]
             if not admin_roles_mentions:
                adminrolemessage = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
             else:
                adminrolemessage = ", ".join(admin_roles_mentions)

            if staffroleresult:
             staff_roles_ids = staffroleresult.get('staffrole', [])
             if not isinstance(staff_roles_ids, list):
                staff_roles_ids = [staff_roles_ids]
             staff_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention
                                    for role_id in staff_roles_ids if discord.utils.get(interaction.guild.roles, id=role_id) is not None]
             if not staff_roles_mentions:
                staffrolemessage = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
             else:
                staffrolemessage = ", ".join(staff_roles_mentions)
            embed = discord.Embed(title="<:Setting:1154092651193323661> Settings",
                                  description=f"**Staff Role:** {staffrolemessage}\n**Admin Role:** {adminrolemessage}",
                                  color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            await interaction.message.edit(embed=embed)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(ConfigCog(client))     
        
        
