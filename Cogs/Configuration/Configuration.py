import discord
from discord.ext import commands
from discord.ext import commands
from pymongo import MongoClient
import os
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
from Cogs.Configuration.Views.tagsview import TagsUsageChannel

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
commandslogging = db['Commands Logging'
                     ]
welcome = db['welcome settings']
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
        discord.SelectOption(label="Customisation", value="Customisation", emoji="<:Customisation:1195037906620911717>"),
        discord.SelectOption(label="Custom Commands", value="Custom Commands", emoji="<:command1:1199456319363633192>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'customcommands': True}) else "Disabled"),
        discord.SelectOption(label="Welcome", value="Welcome", emoji="<:welcome:1218531757691764738>",description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'welcome': True}) else "Disabled"),         
        discord.SelectOption(label="Staff Database & Panel", value="Staff Database & Panel", emoji="<:staffdb:1206253848298127370>",description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Staff Database': True}) else "Disabled"), 
        discord.SelectOption(label="Modmail", value="Modmail", emoji="<:messagereceived:1201999712593383444>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Modmail': True}) else "Disabled"),
        discord.SelectOption(label="Message Quota", value="Message Quota", emoji="<:Messages:1148610048151523339>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Quota': True}) else "Disabled"),
        discord.SelectOption(label="Suggestions", value="Suggestions", emoji="<:UpVote:1183063056834646066>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Suggestions': True}) else "Disabled"),
        discord.SelectOption(label="Forums Utils", value="Forum Utils", emoji="<:forum:1162134180218556497>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Forums': True}) else "Disabled"),
        discord.SelectOption(label="Tags", value="Tags", emoji="<:tag:1162134250414415922>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Tags': True}) else "Disabled"),
        discord.SelectOption(label="Connection Roles", value="Connection Roles", emoji="<:Role:1162074735803387944>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Connection': True}) else "Disabled"),
        discord.SelectOption(label="Suspensions", value="Suspensions", emoji="<:Suspensions:1167093139845165229>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Suspensions': True}) else "Disabled"),
        discord.SelectOption(label="Utility", value="Utility", emoji="<:Folder:1148813584957194250>", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'Utility': True}) else "Disabled"),
        discord.SelectOption(label="LOA", value="LOA", emoji=f"{loa}", description="Enabled" if modules.find_one({'guild_id': author.guild.id, 'LOA': True}) else "Disabled"),
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
            embed = discord.Embed(
            title="<:Setting:1154092651193323661> Settings",
            description=f"",
            color=discord.Color.dark_embed(),
        )
            embed.add_field(name="<:Permissions:1207365901956026368> Permissions", value=f"{replytop}**Staff Role:** {staffrolemessage}\n{replybottom}**Admin Role:** {adminrolemessage}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            view = ConfigViewMain(self.author)        

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
                    wchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                 else:    
                  wchannelmsg = channel.mention          

            embed = discord.Embed(title="<:welcome:1218531757691764738> Welcome Module",  color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Welcome Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Welcome Channel:** {wchannelmsg}\n\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            view = WelcomeModule(self.author)
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
                    infchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else:    
                 infchannelmsg = channel.mention          

            infractiontypescount = len(infractiontyperesult['types'])
            if infractiontypescount == None:
                infractiontypess = "0"
            embed = discord.Embed(title="<:Infraction:1162134605885870180> Infractions Module",  color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Infractions Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Infraction Channel:** {infchannelmsg}\n{replybottom}**Infraction Types [{infractiontypescount}/15]** {infractiontypess}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            view = InfractModule(self.author)
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
            embed = discord.Embed(title="<:Promote:1162134864594735315> Promotions Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Promotions Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Promotion Channel:** {promochannelmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
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
            embed = discord.Embed(title=f"{loa} LOA Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> LOA Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**LOA Channel:** {loachannelmsg}\n{replybottom}**LOA Role:** {loarolemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            view = LOAModule(self.author)
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
            embed = discord.Embed(title="<:Messages:1148610048151523339> Message Quota Module",  color=discord.Color.dark_embed())    
            embed.add_field(name="<:settings:1207368347931516928> Message Quota Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Quota:** {messagecountmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
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
            embed = discord.Embed(title="<:Rate:1162135093129785364> Staff Feedback Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Staff Feedback Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Feedback Channel:** {feedbackchannelmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            view = FeedbackModule(self.author)
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
            embed = discord.Embed(title="<:Partner:1162135285031772300> Partnership Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Partnership Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Partnership Channel:** {partnershipchannelmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            view = PartnershipModule(self.author)
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
            embed = discord.Embed(title="<:Moderation:1163933000006893648> Reports Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Reports Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Reports Channel:** {partnershipchannelmsg}\n{replybottom}**Reports Moderator Role:** {reprolemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
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
                                   description=f"",
                                   color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Applications Configuration",
                            value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Results Channel:** {appchannelmsg}\n{replybottom}**Application Roles:** {approlemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
                            inline=False)
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
            embed = discord.Embed(title="<:Role:1162074735803387944> Connection Roles Module", description=f"**Enabled:** {modulemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
            view = ConnectionsModule(self.author)


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
                 suggestionchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else: 
                 suggestionchannelmsg = channel.mention       
            if smschannelresult:    
                channelid = smschannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                 smschannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else: 
                 smschannelmsg = channel.mention                            
            embed = discord.Embed(title="<:suggestion:1207370004379607090> Suggestions Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Suggestions Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Suggestion Channel:** {suggestionchannelmsg}\n{replybottom}**Suggestions Management Channel:** {smschannelmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
            view = SuggestionModule(self.author)
            try:
             await interaction.message.edit(embed=embed)     
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.") 

        elif color == 'Customisation':
            embed = discord.Embed(title="<:Customisation:1195037906620911717> Customisation", description="From here you can edit **promotions, infraction** embeds\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())
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
            embed = discord.Embed(title="<:messagereceived:1201999712593383444> Modmail",  color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Modmail Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Modmail Category:** {modmailcategorys}\n{replymiddle}**Modmail Pings:** {modmailroles}\n{replybottom}**Transcript Channel:** {transcriptschannels}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)")
            view = Modmail(interaction.user)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
        elif color == 'Staff Database & Panel':
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            if moduleddata:
                modulemsg = moduleddata.get('Staff Database', 'False')     
            embed = discord.Embed(title="<:staffdb:1206253848298127370> Staff Database & Panel", description=f"**Enabled:** {modulemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())

            view = StaffDB(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    
        view.message = await interaction.edit_original_response(embed=embed, view=view)


class StaffDB(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(StaffData(author))
        self.add_item(StaffCustomise(author))
        self.add_item(Config(author))

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class ConfigViewMain(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360) 
        self.add_item(StaffRole(author))
        self.add_item(Adminrole(author))
        self.add_item(Config(author))

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class SuggestionModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(ToggleSuggestions(author))        
        self.add_item(SuggestionsChannel(author))
        self.add_item(SuggestionsChannelManagement(author))
        self.add_item(Config(author))


 

class CustomCommands(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.add_item(ToggleCommands(author))
        self.add_item(CreateButtons(author))
        self.add_item(CmdUsageChannel(author))
        self.add_item(Config(author))

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class Modmail(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(ModmailToggle(author))
        self.add_item(ModmailCategory(author))
        self.add_item(ModmailPing(author))
        self.add_item(TranscriptChannel(author))
        self.add_item(Config(author))

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class InfractModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.author = author
        self.add_item(ToggleInfractionsDropdown(author))         
        self.add_item(InfractionChannel(author))
        self.add_item(InfractionTypes(author))   
        self.add_item(Config(author))        

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class UtilsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.author = author
        self.add_item(ToggleUtils(author))
        self.add_item(Config(author))        

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class PromotionModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.author = author
        self.add_item(PromotionModuleToggle(author))        
        self.add_item(Promotionchannel(author))
        self.add_item(Config(author))    

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class LOAModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(ToggleLOADropdown(author))  
        self.add_item(LOARoled(author))
        self.add_item(LOAChannel(author))                  
        self.add_item(Config(author))    

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class TagsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(ToggleTags(author))      
        self.add_item(TagsUsageChannel(author))   
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class QuotaModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(QuotaToggle(author))            
        self.add_item(QuotaAmount(author))          
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class FeedbackModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(ToggleFeedback(author))         
        self.add_item(FeedbackChannel(author))          
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class SuspensionsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(ToggleSuspensions(author))               
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted') 

class WelcomeModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(ToggleWelcome(author))   
        self.add_item(Welcomemessage(author))  
        self.add_item(WelcomeChannel(author))            
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted') 

class PartnershipModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(TogglePartnerships(author))          
        self.add_item(PartnershipChannel(author))                    
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')
class ForumUtilsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(ToggleForums(author))                          
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class ReportsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)   
        self.add_item(ToggleReportsDropdown(author))           
        self.add_item(ReportChannel(author))         
        self.add_item(ReportsModeratorRole(author))          
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class AppResultModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(ToggleApplications(author))          
        self.add_item(ApplicationChannel(author))         
        self.add_item(ApplicationsRoles(author))             
                        
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted') 

class ConnectionsModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=360)
        self.add_item(ToggleConnectionRoles(author))         
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

class CustomisatiomModule(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.add_item(CustomEmbeds(author))     
        self.add_item(ResetEmbeds(author))       
        self.add_item(Config(author)) 

    async def on_timeout(self) -> None:
        try:
         await self.message.edit(view=None, embed=None, content=f"{no} **Timed out**")
        except discord.errors.NotFound:
            return print('[⚠️] I can\'t time out this view because it was already deleted')

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

        embed = discord.Embed(
            title="<:Setting:1154092651193323661> Settings",
            description=f"",
            color=discord.Color.dark_embed(),
        )
        embed.add_field(name="<:Permissions:1207365901956026368> Permissions", value=f"{replytop}**Staff Role:** {staffrolemessage}\n{replybottom}**Admin Role:** {adminrolemessage}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)")
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        view = ConfigViewMain(ctx.author)
        view.message = await ctx.send(embed=embed, view=view)

    @config.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to configure this server.\n<:Arrow:1115743130461933599>**Required:** ``Administrator``", allowed_mentions=discord.AllowedMentions.none())            

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
            embed = discord.Embed(
            title="<:Setting:1154092651193323661> Settings",
            description=f"",
            color=discord.Color.dark_embed(),
        )
            embed.add_field(name="<:Permissions:1207365901956026368> Permissions", value=f"{replytop}**Staff Role:** {staffrolemessage}\n{replybottom}**Admin Role:** {adminrolemessage}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)")
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            await interaction.message.edit(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ConfigCog(client))     
