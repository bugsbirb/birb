import discord
from discord import ui
import time
import sys
import discord.ext
from discord.ext import commands
from urllib.parse import quote_plus
from discord import app_commands
import discord
import datetime
from discord.ext import commands, tasks
from jishaku import Jishaku
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from typing import Optional
import sqlite3
from emojis import *
from cogs.ConfigurationFolder.infractionsview import InfractionChannel

from cogs.ConfigurationFolder.infractionsview import ToggleInfractionsDropdown
from cogs.ConfigurationFolder.Utilityview import ToggleUtils

from cogs.ConfigurationFolder.promotionsview import Promotionchannel
from cogs.ConfigurationFolder.promotionsview import PromotionModuleToggle

from cogs.ConfigurationFolder.loaview import LOAChannel
from cogs.ConfigurationFolder.loaview import ToggleLOADropdown
from cogs.ConfigurationFolder.loaview import LOARoled

from cogs.ConfigurationFolder.tagsview import ToggleTags

from cogs.ConfigurationFolder.quotaview import QuotaToggle
from cogs.ConfigurationFolder.quotaview import QuotaAmount

from cogs.ConfigurationFolder.feedbackview import FeedbackChannel
from cogs.ConfigurationFolder.feedbackview import ToggleFeedback

from cogs.ConfigurationFolder.suspensionsview import ToggleSuspensions

from cogs.ConfigurationFolder.partnershipsview import PartnershipChannel
from cogs.ConfigurationFolder.partnershipsview import TogglePartnerships

from cogs.ConfigurationFolder.forumsview import ToggleForums

from cogs.ConfigurationFolder.reportview import ReportChannel
from cogs.ConfigurationFolder.reportview import ToggleReportsDropdown

quota = MongoClient('mongodb://bugsbirt:deezbird2768@172.93.103.8:55199/?authMechanism=SCRAM-SHA-256&authSource=admin')
dbq = quota['quotab']
message_quota_collection = dbq["message_quota"]


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
partnershipch = db['partnership channel']
appealable = db['Appeal Toggle']
appealschannel = db['Appeals Channel']
loachannel = db['LOA Channel']
partnershipsch = db['Partnerships Channel']
modules = db['Modules']

mongo2 = MongoClient('mongodb://bugsbirt:deezbird2768@172.93.103.8:55199/?authMechanism=SCRAM-SHA-256&authSource=admin')
db2 = mongo2['quotab']
scollection2 = db2['staffrole']
message_quota_collection = db2["message_quota"]
arole2 = db2['adminrole']
srole = db2['staffrole']

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
                arole.update_one(filter, {'$set': data})
            else:
                arole.insert_one(data)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        print(f"Select Roles {selected_role_ids}")

class Config(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Basic Settings", value="Basic Settings", emoji="<:Setting:1154092651193323661>"),                   
            discord.SelectOption(label="Infractions", value="Infractions", emoji="<:Remove:1162134605885870180>"),            
            discord.SelectOption(label="Promotions", value="Promotions", emoji="<:Promote:1162134864594735315>"),            
            discord.SelectOption(label="Message Quota", value="Message Quota", emoji="<:Messages:1148610048151523339>"),
            discord.SelectOption(label="Forums Utils", value="Forum Utils", emoji="<:forum:1162134180218556497>"),
            discord.SelectOption(label="Tags", value="Tags", emoji="<:tag:1162134250414415922>"),
            discord.SelectOption(label="Suspensions", value="Suspensions", emoji="<:Suspensions:1167093139845165229>"),
            discord.SelectOption(label="Utility", value="Utility", emoji="<:Folder:1148813584957194250>"),
            discord.SelectOption(label="LOA", value="LOA", emoji="<:LOA:1164969910238203995>"),
            discord.SelectOption(label="Staff Feedback", value="Staff Feedback", emoji="<:Rate:1162135093129785364>"),            
            discord.SelectOption(label="Partnerships", value="Partnerships", emoji="<:Partner:1162135285031772300>"),                
            discord.SelectOption(label="Reports", value="Reports", emoji="<:Moderation:1163933000006893648>")                

        
            
        ]
        super().__init__(placeholder='Config Menu', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        if color == 'Infractions':    #infractionss
            infractionchannelresult = infchannel.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            infchannelmsg = ""
            if moduleddata:
                modulemsg = f"{moduleddata['infractions']}"
            if infractionchannelresult:    
                channelid = infractionchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    infchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else:    
                 infchannelmsg = channel.mention                
            embed = discord.Embed(title="<:Infraction:1162134605885870180> Infractions Module", description=f"**Enabled:** {modulemsg}\n**Infraction Channel:** {infchannelmsg}", color=discord.Color.dark_embed())
            view = InfractModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)                 

        elif color == 'Basic Settings':    #basic
         staffroleresult = scollection.find_one({'guild_id': interaction.guild.id})
         adminroleresult = arole.find_one({'guild_id': interaction.guild.id})
         staffrolemessage = "Not Configured"
         adminrolemessage = "Not Configured"
    
         if adminroleresult:
          staff_roles_ids = adminroleresult.get('staffrole', [])
         if not isinstance(staff_roles_ids, list):
            staff_roles_ids = [staff_roles_ids]              
         staff_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention for role_id in staff_roles_ids]
         adminrolemessage = ", ".join(staff_roles_mentions)             

        if staffroleresult:
         staff_roles_ids = staffroleresult.get('staffrole', [])
         if not isinstance(staff_roles_ids, list):
            staff_roles_ids = [staff_roles_ids]          
         staff_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention for role_id in staff_roles_ids]
         staffrolemessage = ", ".join(staff_roles_mentions)

         embed = discord.Embed(title="<:Setting:1154092651193323661> Settings", description=f"**Staff Role:** {staffrolemessage}\n**Admin Role:** {adminrolemessage}", color=discord.Color.dark_embed())
         embed.set_thumbnail(url=interaction.guild.icon)
         embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)            
         view = ConfigViewMain(self.author)

         
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
            feedbackchannelmsg = ""
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
            partnershipchannelresult = partnershipsch.find_one({'guild_id': interaction.guild.id})
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            partnershipchannelmsg = ""
            if moduleddata:
                modulemsg = f"{moduleddata['Feedback']}"
            if partnershipchannelresult:    
                channelid = partnershipchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                 partnershipchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else:
                 partnershipchannelmsg = channel.mention                
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
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            partnershipchannelmsg = ""
            if moduleddata:
                modulemsg = f"{moduleddata['Reports']}"
            if partnershipchannelresult:    
                channelid = partnershipchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                 partnershipchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else: 
                 partnershipchannelmsg = channel.mention                
            embed = discord.Embed(title="<:Moderation:1163933000006893648> Reports Module", description=f"**Enabled:** {modulemsg}\n**Partnership Channel:** {partnershipchannelmsg}", color=discord.Color.dark_embed())
            view = ReportsModule(self.author)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   
        await interaction.response.edit_message(embed=embed, view=view)
            

class ConfigViewMain(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.add_item(StaffRole(author))
        self.add_item(Adminrole(author))
        self.add_item(Config(author))

class InfractModule(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.add_item(InfractionChannel(author))
        self.add_item(ToggleInfractionsDropdown(author))        
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
        self.add_item(ToggleReportsDropdown(author))                          
        self.add_item(Config(author)) 

class ConfigCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(description="Configure the bot for your servers needs")
    @commands.has_guild_permissions(administrator=True)
    async def config(self, ctx):
        staffroleresult = scollection.find_one({'guild_id': ctx.guild.id})
        adminroleresult = arole.find_one({'guild_id': ctx.guild.id})
        modulesdata = modules.find_one({'guild_id': ctx.guild.id})
        if modulesdata is None:
            modulesdata = {'guild_id': ctx.guild.id, 'infractions': False, "Forums": False, "Suspensions": False, "Promotions": False, "Utility": True, "LOA": False, "Tags": False, "Partnerships": False, "Quota": False, "Feedback": False, 'Reports': False}
            modules.insert_one({'guild_id': ctx.guild.id, 'infractions': False, "Forums": False, "Suspensions": False, "Promotions": False, "Utility": True, "LOA": False, "Tags": False, "Partnerships": False, "Quota": False, "Feedback": False, 'Reports': False})
        staffrolemessage = "Not Configured"
        adminrolemessage = "Not Configured"
        if adminroleresult:
        
         staff_roles_ids = adminroleresult.get('staffrole', [])
         if not isinstance(staff_roles_ids, list):
          staff_roles_ids = [staff_roles_ids]            
         staff_roles_mentions = [discord.utils.get(ctx.guild.roles, id=role_id).mention for role_id in staff_roles_ids]
         adminrolemessage = ", ".join(staff_roles_mentions)             
        if staffroleresult:
         staff_roles_ids = staffroleresult.get('staffrole', [])
         if not isinstance(staff_roles_ids, list):
          staff_roles_ids = [staff_roles_ids]               
         staff_roles_mentions = [discord.utils.get(ctx.guild.roles, id=role_id).mention for role_id in staff_roles_ids]
         staffrolemessage = ", ".join(staff_roles_mentions)
        
        embed = discord.Embed(title="<:Setting:1154092651193323661> Settings", description=f"**Staff Role:** {staffrolemessage}\n**Admin Role:** {adminrolemessage}", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        await ctx.send(embed=embed, view = ConfigViewMain(ctx.author))



async def setup(client: commands.Bot) -> None:
    await client.add_cog(ConfigCog(client))     
        
        
