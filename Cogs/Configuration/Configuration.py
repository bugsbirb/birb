import discord
from discord.ext import commands
from pymongo import MongoClient
import os
from emojis import *
from Cogs.Configuration.Views.infractionsview import InfractionChannel, IMoreOptions

from Cogs.Configuration.Views.infractionsview import ToggleInfractionsDropdown
from Cogs.Configuration.Views.Utilityview import ToggleUtils

from Cogs.Configuration.Views.promotionsview import Promotionchannel, PMoreOptions
from Cogs.Configuration.Views.promotionsview import PromotionModuleToggle, Promotionrank
from Cogs.Configuration.Views.loaview import LOAChannel
from Cogs.Configuration.Views.loaview import ToggleLOADropdown
from Cogs.Configuration.Views.loaview import LOARoled

from Cogs.Configuration.Views.tagsview import ToggleTags
from Cogs.Configuration.Views.tagsview import TagsUsageChannel

from Cogs.Configuration.Views.quotaview import QuotaToggle
from Cogs.Configuration.Views.quotaview import QuotaAmount

from Cogs.Configuration.Views.feedbackview import FeedbackChannel, FMoreOptions
from Cogs.Configuration.Views.feedbackview import ToggleFeedback

from Cogs.Configuration.Views.suspensionsview import ToggleSuspensions

from Cogs.Configuration.Views.partnershipsview import PartnershipChannel
from Cogs.Configuration.Views.partnershipsview import TogglePartnerships

from Cogs.Configuration.Views.forumsview import ToggleForums

from Cogs.Configuration.Views.reportview import ReportChannel
from Cogs.Configuration.Views.reportview import ToggleReportsDropdown
from Cogs.Configuration.Views.reportview import ReportsModeratorRole

from Cogs.Configuration.Views.applicationsview import ApplicationChannel
from Cogs.Configuration.Views.applicationsview import ApplicationsRoles, ApplicationCreator, ApplicationSubmissions, AMoreOptions
from Cogs.Configuration.Views.applicationsview import ToggleApplications


from Cogs.Configuration.Views.suggestionview import SuggestionsChannel
from Cogs.Configuration.Views.suggestionview import ToggleSuggestions
from Cogs.Configuration.Views.suggestionview import SuggestionsChannelManagement

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

from Cogs.Configuration.Views.staffpanel import StaffData
from Cogs.Configuration.Views.staffpanel import StaffCustomise

from Cogs.Configuration.Views.CustomCommandsView import CmdUsageChannel

from Cogs.Configuration.Views.welcomeview import WelcomeChannel, Welcomemessage, ToggleWelcome

MONGO_URL = os.getenv('MONGO_URL')

mongo = MongoClient(MONGO_URL)

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
suggestschannel2 = db["Suggestion Management Channel"]

mongo2 = MongoClient(MONGO_URL)
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
tagslogging = db['Tags Logging']
commandslogging = db['Commands Logging']
welcome = db['welcome settings']
ApplicationsSubChannel = db['Applications Submissions']
options = db['module options']
class StaffRole(discord.ui.RoleSelect):
    def __init__(self, author, roles):

        super().__init__(placeholder='Staff Roles', max_values=20, default_values=roles)
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
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
  

            await interaction.response.edit_message(content=None)
            try:
             await refreshembed(interaction)  
            except:
                print('Error editing staff role config message')
                return 
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        print(f"Select Roles {selected_role_ids}")

class Adminrole(discord.ui.RoleSelect):
    def __init__(self, author, roles):
        super().__init__(placeholder='Admin Roles', max_values=20, default_values=roles)
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
  
        data = {
            'guild_id': interaction.guild.id,
            'staffrole': selected_role_ids
        }


        arole.update_one({'guild_id': interaction.guild.id}, {'$set': data}, upsert=True)

        await interaction.response.edit_message(content=None)
        try:
         await refreshembed(interaction)  
        except:
            print('Error editing admin role config message')

        print(f"Select Roles {selected_role_ids}")


class Config(discord.ui.Select):
    def __init__(self, author):
        self.author = author

        
        options = [
        discord.SelectOption(label="Settings", value="Settings", emoji="<:Setting:1154092651193323661>", description=self.permissionsconfig(author)),
        discord.SelectOption(label="Infractions", value="Infractions", emoji="<:Remove:1162134605885870180>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'infractions': True}) else "Disabled"),
        discord.SelectOption(label="Promotions", value="Promotions", emoji="<:Promote:1162134864594735315>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Promotions': True}) else "Disabled"),
        discord.SelectOption(label="Customisation", value="Customisation", emoji="<:Customisation:1223063306131210322>"),
        discord.SelectOption(label="Custom Commands", value="Custom Commands", emoji="<:command1:1199456319363633192>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'customcommands': True}) else "Disabled"),
        discord.SelectOption(label="Welcome", value="Welcome", emoji="<:welcome:1218531757691764738>",description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'welcome': True}) else "Disabled"),         
        discord.SelectOption(label="Staff Database & Panel", value="Staff Database & Panel", emoji="<:staffdb:1206253848298127370>",description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Staff Database': True}) else "Disabled"), 
        discord.SelectOption(label="Modmail", value="Modmail", emoji="<:messagereceived:1201999712593383444>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Modmail': True}) else "Disabled"),
        discord.SelectOption(label="Message Quota", value="Message Quota", emoji="<:messageup:1224722310687359106>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Quota': True}) else "Disabled"),
        discord.SelectOption(label="Suggestions", value="Suggestions", emoji="<:UpVote:1183063056834646066>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Suggestions': True}) else "Disabled"),
        discord.SelectOption(label="Forums Utils", value="Forum Utils", emoji="<:forum:1162134180218556497>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Forums': True}) else "Disabled"),
        discord.SelectOption(label="Tags", value="Tags", emoji="<:tag:1162134250414415922>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Tags': True}) else "Disabled"),
        discord.SelectOption(label="Connection Roles", value="Connection Roles", emoji="<:Role:1162074735803387944>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Connection': True}) else "Disabled"),
        discord.SelectOption(label="Suspensions", value="Suspensions", emoji="<:Suspensions:1167093139845165229>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Suspensions': True}) else "Disabled"),
        discord.SelectOption(label="Utility", value="Utility", emoji="<:Folder:1148813584957194250>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Utility': True}) else "Disabled"),
        discord.SelectOption(label="LOA", value="LOA", emoji=f"{loa}", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'LOA': True}) else "Disabled"),
        discord.SelectOption(label="Staff Feedback", value="Staff Feedback", emoji="<:Rate:1162135093129785364>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Feedback': True}) else "Disabled"),
        discord.SelectOption(label="Partnerships", value="Partnerships", emoji="<:partnerships:1224724406144733224>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Partnerships': True}) else "Disabled"),
        discord.SelectOption(label="Reports", value="Reports", emoji="<:reports:1224723845726998651>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Reports': True}) else "Disabled"),
        discord.SelectOption(label="Applications", value="Applications", emoji="<:Application:1224722901328986183>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Applications': True}) else "Disabled")
]

        super().__init__(placeholder='Config Menu', min_values=1, max_values=1, options=options)

    @staticmethod
    def permissionsconfig(author):
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
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.followup.send(embed=embed, ephemeral=True)    
        if color == 'Settings':  # basic
            staffroleresult = scollection.find_one({'guild_id': interaction.guild.id})

            adminroleresult = arole.find_one({'guild_id': interaction.guild.id})
       
            staffrolemessage = "Not Configured"
            adminrolemessage = "Not Configured"
            adminroles = []
            if adminroleresult:
                admin_roles = adminroleresult.get('staffrole', [])
                if not isinstance(admin_roles, list):
                    admin_roles = [admin_roles]

                for admin_role_ids in admin_roles:
                    if not isinstance(admin_role_ids, list):
                        admin_role_ids = [admin_role_ids]

                    for role_id in admin_role_ids:
                        role = interaction.guild.get_role(role_id)

                        if role:
                            adminroles.append(role)
                        else:
                            print(f"Role with ID {role_id} not found.")
            
                admin_roles_ids = adminroleresult.get('staffrole', [])
                if not isinstance(admin_roles_ids, list):
                    admin_roles_ids = [admin_roles_ids]
                admin_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention
                                        for role_id in admin_roles_ids if discord.utils.get(interaction.guild.roles, id=role_id) is not None]
                if not admin_roles_mentions:
                    adminrolemessage = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
                else:
                    adminrolemessage = ", ".join(admin_roles_mentions)


            staffroles = []
            if staffroleresult:
                staff_roles = staffroleresult.get('staffrole', [])
                if not isinstance(staff_roles, list):
                    staff_roles = [staff_roles]

                for staff_role_ids in staff_roles:
                    if not isinstance(staff_role_ids, list):
                        staff_role_ids = [staff_role_ids]

                    for role_id in staff_role_ids:
                        role = interaction.guild.get_role(role_id)

                        if role:
                            staffroles.append(role)
                        else:
                            print(f"Role with ID {role_id} not found.")
                staff_roles_ids = staffroleresult.get('staffrole', [])
                if not isinstance(staff_roles_ids, list):
                    staff_roles_ids = [staff_roles_ids]
                staff_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention
                                        for role_id in staff_roles_ids if discord.utils.get(interaction.guild.roles, id=role_id) is not None]
                if not staff_roles_mentions:
                    staffrolemessage = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
                else:
                    staffrolemessage = ", ".join(staff_roles_mentions)

            embed = discord.Embed(
            title="<:Setting:1154092651193323661> Settings",
            description=f"",
            color=discord.Color.dark_embed(),
        )   
            value = f"{replytop}**Staff Role:** {staffrolemessage}\n{replybottom}**Admin Role:** {adminrolemessage}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)"
            if len(value) > 1024:
             value = value[:1021] + "..."
            embed.add_field(name="<:Permissions:1207365901956026368> Permissions", value=value, inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            view = ConfigViewMain(self.author, staffroles, adminroles)        

        elif color == 'Welcome':
            welcomechannelresult = welcome.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            wchannelmsg = "Not Configured"

                
            if moduleddata:
                modulemsg = moduleddata.get('welcome', False)
            if welcomechannelresult:    
                channelid = welcomechannelresult.get('welcome_channel', None)
                if channelid is None:
                   wchannelmsg = "Not Configured"
                else:   
                   
                 channel = interaction.guild.get_channel(channelid)
                 if channel is None:
                    wchannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                 else:    
                  wchannelmsg = channel.mention          

            embed = discord.Embed(title="<:welcome:1218531757691764738> Welcome Module",  color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Welcome Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Welcome Channel:** {wchannelmsg}\n\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]
            channels = []
            if (
                welcomechannelresult
                and welcomechannelresult.get('welcome_channel')
            ):
             channels = interaction.guild.get_channel(welcomechannelresult.get('welcome_channel'))  
             if channels is None:
                 channels = []          
             else:
                channels = [channels]  
                     
            view = WelcomeModule(self.author, options, channels)
            
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)              
        elif color == 'Infractions':    #infractionss
            infractionchannelresult = infchannel.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            infchannelmsg = "Not Configured"
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
                    infchannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else:    
                 infchannelmsg = channel.mention          
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]
            infractiontypescount = len(infractiontyperesult['types'])
            if infractiontypescount == None:
                infractiontypess = "0"
            channels = []
            if (
                infractionchannelresult
                and infractionchannelresult.get('channel_id')
            ):
             channels = interaction.guild.get_channel(infractionchannelresult.get('channel_id'))  
             if channels is None:
                 channels = []          
             else:
                channels = [channels]    
            embed = discord.Embed(title="<:Infraction:1223063128275943544> Infractions Module",  color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Infractions Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Infraction Channel:** {infchannelmsg}\n{replybottom}**Infraction Types [{infractiontypescount}/15]** {infractiontypess}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            view = InfractModule(self.author, options, channels)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)                 



        elif color == 'Utility':         # Utility
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Utility']}"            
            embed = discord.Embed(title="<:Pen:1126527802255085628> Utilties Module", description=f"**Enabled:** {modulemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon) 
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]              
            view = UtilsModule(self.author, options)

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
                 promochannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else: 
                 promochannelmsg = channel.mention                          
            embed = discord.Embed(title="<:Promote:1162134864594735315> Promotions Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Promotions Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Promotion Channel:** {promochannelmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)\n\n<:Information:1115338749728002089> **What are Promotion Ranks?:** Promotion ranks enable you to choose a primary role and automatically include any additional selected roles. When you use the command /promote and select a rank, it will assign the chosen primary role along with any additional roles you've selected.", inline=False)
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]  
            channels = []
            if (
                promochannelresult
                and promochannelresult.get('channel_id')
            ):
             channels = interaction.guild.get_channel(promochannelresult.get('channel_id'))  
             if channels is None:
                 channels = []          
             else:
                channels = [channels]                           
            view = PromotionModule(self.author, options, channels)
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
                 loarolemsg = "<:Error:1223063223910010920> Role wasn't found please reconfigure."
                else: 
                 loarolemsg = f"{role.mention}"

            if loachannelresult:     
                channelid = loachannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    loachannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else:    
                 loachannelmsg = channel.mention       
            embed = discord.Embed(title=f"{loa} LOA Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> LOA Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**LOA Channel:** {loachannelmsg}\n{replybottom}**LOA Role:** {loarolemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]
            channels = []
            if loachannelresult and loachannelresult.get('channel_id'):
             channels = interaction.guild.get_channel(loachannelresult.get('channel_id'))  
             if channels is None:
                 channels = []          
             else:
                channels = [channels]       

            roles = []
            if loaroleresult and loaroleresult.get('staffrole'):
               result = loaroleresult.get('staffrole', []) 
               if not isinstance(result, list):
                   result = [result]
               for role_ids in result:
                       if not isinstance(role_ids, list):
                           role_ids = [role_ids]
                       for role_id in role_ids:
                        role = interaction.guild.get_role(role_id)
                                             
                        if role:
                           roles.append(role)
                        else:
                           print(f"Role with ID {role_id} not found.")                                
            view = LOAModule(self.author, options, channels, roles)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    
        elif color == 'Tags':         # Tags
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})        
            usagechanneldata = tagslogging.find_one({'guild_id': interaction.guild.id})
            usagechannelmsg = "Not Configured"    
            if usagechanneldata:
                usagechannelmsg = f"<#{usagechanneldata['channel_id']}>"
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Tags']}"            
            embed = discord.Embed(title="<:tag:1162134250414415922> Tags Module", color=discord.Color.dark_embed())    
            embed.add_field(name="<:settings:1207368347931516928> Tags Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Tags Logging:** {usagechannelmsg}\n\n <:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)")
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)      
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]       
            view = TagsModule(self.author, options)

        elif color == 'Message Quota':         # Tags
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            messagequotdata = message_quota_collection.find_one({'guild_id': interaction.guild.id})
            messagecountmsg = "Not Configured"
            if messagequotdata:
                messagecountmsg = f"{messagequotdata['quota']}"
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Quota']}"            
            embed = discord.Embed(title="<:messageup:1224722310687359106> Message Quota Module",  color=discord.Color.dark_embed())    
            embed.add_field(name="<:settings:1207368347931516928> Message Quota Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Quota:** {messagecountmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]                    
            view = QuotaModule(self.author, options)

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
                    feedbackchannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else:    
                 feedbackchannelmsg = channel.mention                
            embed = discord.Embed(title="<:Rate:1162135093129785364> Staff Feedback Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Staff Feedback Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Feedback Channel:** {feedbackchannelmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]   
            channels = []                     
            if (
                feedbackchannelresult
                and feedbackchannelresult.get('channel_id')
            ):
             channels = interaction.guild.get_channel(feedbackchannelresult.get('channel_id'))  
             if channels is None:
                 channels = []          
             else:
                channels = [channels]       
            view = FeedbackModule(self.author, options, channels)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   

        elif color == 'Suspensions':         # Tags
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Suspensions']}"            
            embed = discord.Embed(title="<:Suspensions:1167093139845165229> Suspension Module", color=discord.Color.dark_embed())   
            embed.add_field(name="<:settings:1207368347931516928> Suspension Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Suspension Channel:** Infraction Channel\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False) 
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]                    
            view = SuspensionsModule(self.author, options)




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
                 partnershipchannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
            embed = discord.Embed(title="<:partnerships:1224724406144733224> Partnership Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Partnership Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Partnership Channel:** {partnershipchannelmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]  
            channels = []
            if (
                partnershipchannelresult
                and partnershipchannelresult.get('channel_id')
            ):
             channels = interaction.guild.get_channel(partnershipchannelresult.get('channel_id'))  
             if channels is None:
                 channels = []          
             else:
                channels = [channels]       
                                                      
            view = PartnershipModule(self.author, options, channels)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
        elif color == 'Forum Utils':         # Tags
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Forums']}"            
            embed = discord.Embed(title="<:forum:1162134180218556497> Forum Utilites", description=f"**Enabled:** {modulemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]
            view = ForumUtilsModule(self.author, options)

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
                 partnershipchannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else: 
                 partnershipchannelmsg = channel.mention    

            if reportsmoderatorresult:    
                roleid = reportsmoderatorresult['staffrole']
                role = discord.utils.get(interaction.guild.roles, id=roleid)
                if role is None:
                 reprolemsg = "<:Error:1223063223910010920> Role wasn't found please reconfigure."
                else: 
                 reprolemsg = f"{role.mention}"
            embed = discord.Embed(title="<:reports:1224723845726998651> Reports Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Reports Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Reports Channel:** {partnershipchannelmsg}\n{replybottom}**Reports Moderator Role:** {reprolemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]  
            channels = []
            if (
                partnershipchannelresult
                and partnershipchannelresult.get('channel_id')
            ):
             channels = interaction.guild.get_channel(partnershipchannelresult.get('channel_id'))  
             if channels is None:
                 channels = []          
             else:
                channels = [channels]       
            roles = []    
            if (
                reportsmoderatorresult
                and reportsmoderatorresult.get('staffrole')
            ):
               result = reportsmoderatorresult.get('staffrole', []) 
               if not isinstance(result, list):
                   result = [result]
               for role_ids in result:
                       if not isinstance(role_ids, list):
                           role_ids = [role_ids]
                       for role_id in role_ids:
                        role = interaction.guild.get_role(role_id)
                                             
                        if role:
                           roles.append(role)
                        else:
                           print(f"Role with ID {role_id} not found.")            
            view = ReportsModule(self.author, options, channels ,roles)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
        elif color == 'Applications':            


            applicationchannelresult = ApplicationsChannel.find_one({'guild_id': interaction.guild.id})
            submissionchannelresult = ApplicationsSubChannel.find_one({'guild_id': interaction.guild.id})

            staffroleresult = ApplicationsRolesDB.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})

            approlemsg = "Not Configured"
            subchannelmsg = "Not Configured"
            appchannelmsg = "Not Configured"
            modulemsg = ""


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
                    approlemsg = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
                else:
                    approlemsg = ", ".join(staff_roles_mentions)

            if submissionchannelresult:
                channelid = submissionchannelresult['channel_id']
                subchannelmsg = f"<#{channelid}>"

            if applicationchannelresult:
                channelid = applicationchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    appchannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else:
                    appchannelmsg = channel.mention

            embed = discord.Embed(title="<:Application:1224722901328986183> Applications Module",
                                   description=f"",
                                   color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Applications Configuration",
                            value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Submission Channel:** {subchannelmsg}\n{replymiddle}**Results Channel:** {appchannelmsg}\n{replybottom}**Application Roles:** {approlemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
                            inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            channels = []
            if (
                applicationchannelresult
                and applicationchannelresult.get('channel_id')
            ):
             channels = interaction.guild.get_channel(applicationchannelresult.get('channel_id'))  
             if channels is None:
                 channels = []          
             else:
                channels = [channels]       
                                                               
            view = AppResultModule(self.author, channels)

        elif color == 'Connection Roles':         # 
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})            
            modulemsg = "True"
            if moduleddata:
                modulemsg = moduleddata.get('Connection', 'False')
            else:
                modulemsg = 'False'     
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]                
            embed = discord.Embed(title="<:Role:1162074735803387944> Connection Roles Module", description=f"**Enabled:** {modulemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
            view = ConnectionsModule(self.author, options)


        elif color == 'Suggestions':    # Suggestions
            suschannelresult = suggestschannel.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            suggestionchannelmsg = "Not Configured"
            smschannelresult = suggestschannel2.find_one({'guild_id': interaction.guild.id})
            smschannelmsg = "Not Configured"
    
            if moduleddata:
                modulemsg = moduleddata.get('Suggestions', 'False')
            if suschannelresult:    
                channelid = suschannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                 suggestionchannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else: 
                 suggestionchannelmsg = channel.mention       
            if smschannelresult:    
                channelid = smschannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                 smschannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else: 
                 smschannelmsg = channel.mention                         

            if moduleddata:
                modulemsg = moduleddata.get('Connection', 'False')
            else:
                modulemsg = 'False'     
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]


            embed = discord.Embed(title="<:suggestion:1207370004379607090> Suggestions Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Suggestions Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Suggestion Channel:** {suggestionchannelmsg}\n{replybottom}**Suggestions Management Channel:** {smschannelmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
            if suschannelresult and suschannelresult.get('channel_id'):
             suggestchannel = interaction.guild.get_channel(suschannelresult.get('channel_id'))  
             if suggestchannel is None:
                 suggestchannel = []          
             else:
                suggestchannel = [suggestchannel]       
            managementchannel = []    
            suggestchannel = []
            if smschannelresult and smschannelresult.get('channel_id'):
             managementchannel = interaction.guild.get_channel(suschannelresult.get('channel_id'))  
             if managementchannel is None:
                 managementchannel = []          
             else:
                managementchannel = [managementchannel]                   
            view = SuggestionModule(self.author, options, suggestchannel, managementchannel)
            try:
             await interaction.message.edit(embed=embed)     
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.") 

        elif color == 'Customisation':
            embed = discord.Embed(title="<:Customisation:1223063306131210322> Customisation", description="From here you can edit **promotions, infraction** embeds\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())
            view = CustomisatiomModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    

        elif color == 'Custom Commands':
            commands = customcommands.find({'guild_id': interaction.guild.id})
            moduledata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = 'False'
            if moduledata:
                modulemsg = moduledata.get('customcommands', 'False')
                
        

            logging = commandslogging.find_one({'guild_id': interaction.guild.id})
            loggingmsg = "Not Configured"
            if logging:
                loggingid = logging['channel_id']
                loggingmsg = f"<#{loggingid}>"





            amount = customcommands.count_documents({'guild_id': interaction.guild.id})
            embed = discord.Embed(title=f"<:command1:1199456319363633192> Custom Commands ({amount}/25)", description="", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            embed.add_field(name=f"<:settings:1207368347931516928> Custom Commands Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Logging Channel:** {loggingmsg}")
            for result in commands:
                permissions = result.get('permissionroles', 'None')
                if permissions == 'None':
                    permissions = "None"
                else:
                    permissions = ", ".join([f"<@&{roleid}>" for roleid in permissions])
                embed.add_field(name=f"<:command1:1199456319363633192> {result['name']}", value=f"{arrow} **Created By:** <@{result['creator']}>\n{arrow} **Required Permissions:** {permissions}", inline=False)
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]   
            channels = []
            if logging and logging.get('channel_id'):
             channels = interaction.guild.get_channel(logging.get('channel_id'))  
             if channels is None:
                 channels = []          
             else:
                channels = [channels]       
            view = CustomCommands(self.author, options, channels)
            
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
                    modmailroles = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
                modmailroles = ", ".join(filter(None, modmailroles))

            if transcriptschannelresult:
                transcriptschannels = f"<#{transcriptschannelresult['channel_id']}>"
            if modmailcategoryresult:
                modmailcategorys = f"<#{modmailcategoryresult['category_id']}>"    
            embed = discord.Embed(title="<:messagereceived:1201999712593383444> Modmail",  color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Modmail Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Modmail Category:** {modmailcategorys}\n{replymiddle}**Modmail Pings:** {modmailroles}\n{replybottom}**Transcript Channel:** {transcriptschannels}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)")
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]
            category = []
            if (
                modmailcategoryresult
                and modmailcategoryresult.get('category_id')
            ):
               category = discord.utils.get(interaction.guild.categories, id=modmailcategoryresult.get('category_id'))
               if category is None:
                   category = []
               else:
                   category = [category]    
            roles = []
            if (
                modmailpingresult
                and modmailpingresult.get('modmailping')
            ):
               result = modmailpingresult.get('modmailping', []) 
               if not isinstance(result, list):
                   result = [result]
               for role_ids in result:
                       if not isinstance(role_ids, list):
                           role_ids = [role_ids]
                       for role_id in role_ids:
                        role = interaction.guild.get_role(role_id)
                                             
                        if role:
                           roles.append(role)
                        else:
                           print(f"Role with ID {role_id} not found.")
            channels = []
            
            if (
                transcriptschannelresult
                and transcriptschannelresult.get('channel_id')
            ):
             channels = interaction.guild.get_channel(transcriptschannelresult.get('channel_id'))
             if channels is None:
                 channels = []
             else:
                 channels = [channels]
            view = Modmail(interaction.user, options, channels, category, roles)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   



        elif color == 'Staff Database & Panel':
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            if moduleddata:
                modulemsg = moduleddata.get('Staff Database', 'False')     
            embed = discord.Embed(title="<:staffdb:1206253848298127370> Staff Database & Panel", description=f"**Enabled:** {modulemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())
            options = [
              discord.SelectOption(label="Enabled"),
              discord.SelectOption(label="Disabled")]
            view = StaffDB(self.author, options)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    
        view.message = await interaction.edit_original_response(embed=embed, view=view)


class StaffDB(discord.ui.View):
    def __init__(self, author, options):
        super().__init__(timeout=None)
        self.add_item(StaffData(author, options))
        self.add_item(StaffCustomise(author))
        self.add_item(Config(author))



class ConfigViewMain(discord.ui.View):
    def __init__(self, author, staffroles, adminroles):
        super().__init__(timeout=None) 
        self.add_item(StaffRole(author, staffroles))
        self.add_item(Adminrole(author, adminroles))
        self.add_item(Config(author))



class SuggestionModule(discord.ui.View):
    def __init__(self, author,options, suggestchannel, managementchannel):
        super().__init__(timeout=None)
        self.add_item(ToggleSuggestions(author, options))        
        self.add_item(SuggestionsChannel(author, suggestchannel))
        self.add_item(SuggestionsChannelManagement(author, managementchannel))
        self.add_item(Config(author))


 

class CustomCommands(discord.ui.View):
    def __init__(self, author, options, channels):
        super().__init__(timeout=None)
        self.add_item(ToggleCommands(author, options))
        self.add_item(CreateButtons(author))
        self.add_item(CmdUsageChannel(author, channels))
        self.add_item(Config(author))



class Modmail(discord.ui.View):
    def __init__(self, author, options, channels, category, roles):
        super().__init__(timeout=None)
        self.add_item(ModmailToggle(author, options))
        self.add_item(ModmailCategory(author, category))
        self.add_item(ModmailPing(author, roles))
        self.add_item(TranscriptChannel(author, channels))
        self.add_item(Config(author))



class InfractModule(discord.ui.View):
    def __init__(self, author, options, channels):
        super().__init__(timeout=None)
        self.author = author
        self.add_item(ToggleInfractionsDropdown(author, options))         
        self.add_item(InfractionChannel(author, channels))
        self.add_item(InfractionTypes(author))   
        self.add_item(IMoreOptions(author))
        self.add_item(Config(author))        



class UtilsModule(discord.ui.View):
    def __init__(self, author, options):
        super().__init__(timeout=None)
        self.author = author
        self.add_item(ToggleUtils(author, options))
        self.add_item(Config(author))        



class PromotionModule(discord.ui.View):
    def __init__(self, author, options, channels):
        super().__init__(timeout=None)
        self.author = author
        self.add_item(PromotionModuleToggle(author, options))        
        self.add_item(Promotionchannel(author, channels))
        self.add_item(Promotionrank(author))
        self.add_item(PMoreOptions(author))
        
        self.add_item(Config(author))    



class LOAModule(discord.ui.View):
    def __init__(self, author, options, channels, roles):
        super().__init__(timeout=None)
        self.add_item(ToggleLOADropdown(author, options))  
        self.add_item(LOARoled(author, roles))
        self.add_item(LOAChannel(author, channels))                  
        self.add_item(Config(author))    



class TagsModule(discord.ui.View):
    def __init__(self, author, options):
        super().__init__(timeout=None)
        self.add_item(ToggleTags(author, options))      
        self.add_item(TagsUsageChannel(author))   
        self.add_item(Config(author)) 



class QuotaModule(discord.ui.View):
    def __init__(self, author, options):
        super().__init__(timeout=None)
        self.add_item(QuotaToggle(author, options))            
        self.add_item(QuotaAmount(author))          
        self.add_item(Config(author)) 



class FeedbackModule(discord.ui.View):
    def __init__(self, author, options, channels):
        super().__init__(timeout=None)
        self.add_item(ToggleFeedback(author, options))         
        self.add_item(FeedbackChannel(author, channels))    
        self.add_item(FMoreOptions(author))      
        self.add_item(Config(author)) 



class SuspensionsModule(discord.ui.View):
    def __init__(self, author, options):
        super().__init__(timeout=None)
        self.add_item(ToggleSuspensions(author, options))               
        self.add_item(Config(author)) 

 

class WelcomeModule(discord.ui.View):
    def __init__(self, author, options, channels):
        super().__init__(timeout=None)
        self.add_item(ToggleWelcome(author, options))   
        self.add_item(Welcomemessage(author))  
        self.add_item(WelcomeChannel(author, channels))            
        self.add_item(Config(author)) 

 

class PartnershipModule(discord.ui.View):
    def __init__(self, author, options, channels):
        super().__init__(timeout=None)
        self.add_item(TogglePartnerships(author, options))          
        self.add_item(PartnershipChannel(author, channels))                    
        self.add_item(Config(author)) 


class ForumUtilsModule(discord.ui.View):
    def __init__(self, author, options):
        super().__init__(timeout=None)
        self.add_item(ToggleForums(author, options))                          
        self.add_item(Config(author)) 



class ReportsModule(discord.ui.View):
    def __init__(self, author, options, channels, roles):
        super().__init__(timeout=None)   
        self.add_item(ToggleReportsDropdown(author, options))           
        self.add_item(ReportChannel(author, channels))         
        self.add_item(ReportsModeratorRole(author, roles))          
        self.add_item(Config(author)) 



class AppResultModule(discord.ui.View):
    def __init__(self, author, channels):
        super().__init__(timeout=None)     
        self.add_item(ToggleApplications(author))         
        self.add_item(ApplicationCreator(author))   
        self.add_item(ApplicationSubmissions(author, channels))
        self.add_item(AMoreOptions(author))                   
        self.add_item(Config(author)) 
class ConnectionsModule(discord.ui.View):
    def __init__(self, author, options):
        super().__init__(timeout=None)
        self.add_item(ToggleConnectionRoles(author, options))         
        self.add_item(Config(author)) 



class CustomisatiomModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.add_item(CustomEmbeds(author))     
        self.add_item(ResetEmbeds(author))       
        self.add_item(Config(author)) 



class ConfigCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(description="Configure the bot for your servers needs")
    @commands.has_guild_permissions(manage_guild=True)
    async def config(self, ctx: commands.Context):
        await ctx.defer()
        option_result = options.find_one({'guild_id': ctx.guild.id})
        if option_result is None:
            options.insert_one({'guild_id': ctx.guild.id})        
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
        adminroles = []
        staffroles = []
        if adminroleresult:
            result = adminroleresult.get('staffrole', []) 
            if not isinstance(result, list):
                result = [result]
            for role_ids in result:         
                if not isinstance(role_ids, list):
                    role_ids = [role_ids]                            
                for role_id in role_ids:
                    role = ctx.guild.get_role(role_id)
                    if role:
                        adminroles.append(role)
                    else:
                        print(f"Role with ID {role_id} not found.")                  
            admin_roles_ids = adminroleresult.get('staffrole', [])
            if not isinstance(admin_roles_ids, list):
                admin_roles_ids = [admin_roles_ids]
            admin_roles_mentions = [discord.utils.get(ctx.guild.roles, id=role_id).mention
                                    for role_id in admin_roles_ids if discord.utils.get(ctx.guild.roles, id=role_id) is not None]
            if not admin_roles_mentions:
                adminrolemessage = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
            else:
                adminrolemessage = ", ".join(admin_roles_mentions)
        
        if staffroleresult:
            result = staffroleresult.get('staffrole', []) 
            if not isinstance(result, list):
                result = [result]
            for role_ids in result:
                if not isinstance(role_ids, list):
                    role_ids = [role_ids]
                for role_id in role_ids:
                    role = ctx.guild.get_role(role_id)
                    if role:
                        staffroles.append(role)
                    else:
                        print(f"Role with ID {role_id} not found.")
            staff_roles_ids = staffroleresult.get('staffrole', [])
            if not isinstance(staff_roles_ids, list):
                staff_roles_ids = [staff_roles_ids]
            staff_roles_mentions = [discord.utils.get(ctx.guild.roles, id=role_id).mention
                                    for role_id in staff_roles_ids if discord.utils.get(ctx.guild.roles, id=role_id) is not None]
            if not staff_roles_mentions:
                staffrolemessage = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
            else:
                staffrolemessage = ", ".join(staff_roles_mentions)
         
        embed = discord.Embed(
            title="<:Setting:1154092651193323661> Settings",
            description=f"",
            color=discord.Color.dark_embed(),
        )
        value = f"{replytop}**Staff Role:** {staffrolemessage}\n{replybottom}**Admin Role:** {adminrolemessage}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)"
        if len(value) > 1024:
             value = value[:1021] + "..."         
        embed.add_field(name="<:Permissions:1207365901956026368> Permissions", value=value)
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        view = ConfigViewMain(ctx.author, staffroles, adminroles)
        await ctx.send(embed=embed, view=view)

    @config.error
    async def permissionerror(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to configure this server.\n<:Arrow:1115743130461933599>**Required:** ``Manage Guild``", allowed_mentions=discord.AllowedMentions.none())            

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
                adminrolemessage = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
             else:
                adminrolemessage = ", ".join(admin_roles_mentions)

            if staffroleresult:
             staff_roles_ids = staffroleresult.get('staffrole', [])
             if not isinstance(staff_roles_ids, list):
                staff_roles_ids = [staff_roles_ids]
             staff_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention
                                    for role_id in staff_roles_ids if discord.utils.get(interaction.guild.roles, id=role_id) is not None]
             if not staff_roles_mentions:
                staffrolemessage = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
             else:
                staffrolemessage = ", ".join(staff_roles_mentions)
            embed = discord.Embed(
            title="<:Setting:1154092651193323661> Settings",
            description=f"",
            color=discord.Color.dark_embed(),
        )
            value = f"{replytop}**Staff Role:** {staffrolemessage}\n{replybottom}**Admin Role:** {adminrolemessage}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)"
            if len(value) > 1024:
             value = value[:1021] + "..."            
            embed.add_field(name="<:Permissions:1207365901956026368> Permissions", value=value)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            await interaction.message.edit(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ConfigCog(client))     
