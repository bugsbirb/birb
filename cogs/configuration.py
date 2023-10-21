import discord
from discord import ui
import time
import platform
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
from typing import Optional
import sqlite3
from emojis import *
from cogs.ModerationConfig.moderationdropdowns import *

mongo = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = mongo['astro']
scollection = db['staffrole']
arole = db['adminrole']
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
class StaffRole(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder='Staff Role')

    async def callback(self, interaction: discord.Interaction):
        selected_role_id = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'guild_id': interaction.guild.id, 
            'staffrole': selected_role_id.id  
        }

        try:
            existing_record = scollection.find_one(filter)

            if existing_record:
                scollection.update_one(filter, {'$set': data})
            else:
                scollection.insert_one(data)

            embed = discord.Embed(
                title="Success!",
                description=f"Great, now submit a admin role.",
                color=0x2b2d31
            )
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"selected_role_id: {selected_role_id.id}")

class Done(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(label='Done', style=discord.ButtonStyle.blurple)
    async def Done(self,  interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="", description="> Configuration updated", color=0x2b2d31)
        await interaction.response.edit_message(content=None, view=None, embed=embed)


  
class AppealTogglable(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(label='Enable', style=discord.ButtonStyle.green)
    async def enable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.enabled = True

        guild_id = str(interaction.guild.id)

        appealable.update_one({"guild_id": guild_id}, {"$set": {"enabled": True}}, upsert=True)

        embed = discord.Embed(
            title="Infraction Appeals",
            description="Nice you've enabled it! Now you have to select the appeals channel.",
            color=0x2b2d31
        )
        view = AppealChannel()
        await interaction.response.edit_message(content=None, embed=embed, view=view)

    @discord.ui.button(label='Disable', style=discord.ButtonStyle.red)
    async def disable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.enabled = False

        guild_id = str(interaction.guild.id)

        appealable.delete_one({"guild_id": guild_id})

        embed = discord.Embed(
            title="Infraction Appeals",
            description="You've disabled it! Infraction appeals are now turned off.",
            color=0x2b2d31
        )
        await interaction.response.edit_message(content=None, embed=embed, view=None)

class InfractionChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder='Infractions Channel')

    async def callback(self, interaction: discord.Interaction):
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = infchannel.find_one(filter)

            if existing_record:
                infchannel.update_one(filter, {'$set': data})
            else:
                infchannel.insert_one(data)

            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")        

class PromotionChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder='Promotion Channel')

    async def callback(self, interaction: discord.Interaction):
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = promochannel.find_one(filter)

            if existing_record:
                promochannel.update_one(filter, {'$set': data})
            else:
                promochannel.insert_one(data)

            await interaction.response.edit_message(content=None)

        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")     

class PartnershipChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder='Partnership Logging Channel')

    async def callback(self, interaction: discord.Interaction):
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = partnershipsch.find_one(filter)

            if existing_record:
                partnershipsch.update_one(filter, {'$set': data})
            else:
                partnershipsch.insert_one(data)

            await interaction.response.edit_message(content=None)

        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")     

class StaffFeedbackChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder='Staff Feedback Channel')

    async def callback(self, interaction: discord.Interaction):
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = feedbackch.find_one(filter)

            if existing_record:
                feedbackch.update_one(filter, {'$set': data})
            else:
                feedbackch.insert_one(data)

            await interaction.response.edit_message(content=None)

        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")   

class ReportsChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder='Reports Channel')

    async def callback(self, interaction: discord.Interaction):
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = repchannel.find_one(filter)

            if existing_record:
                repchannel.update_one(filter, {'$set': data})
            else:
                repchannel.insert_one(data)

            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")  

class AppealsChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder='Appeals Channel')

    async def callback(self, interaction: discord.Interaction):
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = appealschannel.find_one(filter)

            if existing_record:
                appealschannel.update_one(filter, {'$set': data})
            else:
                appealschannel.insert_one(data)

            embed = discord.Embed(
                title="Success!",
                description=f"> Configuration updated",
                color=0x2b2d31
            )
            view = Rerun()
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")  

class LOAChannel(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder='LOA Channel')

    async def callback(self, interaction: discord.Interaction):
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = loachannel.find_one(filter)

            if existing_record:
                loachannel.update_one(filter, {'$set': data})
            else:
                loachannel.insert_one(data)

            embed = discord.Embed(
                title="Success!",
                description=f"> Configuration updated",
                color=0x2b2d31
            )
            view = Rerun()
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")  

class AdminRole(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder='Admin Role')

    async def callback(self, interaction: discord.Interaction):
        selected_role_id = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'guild_id': interaction.guild.id, 
            'adminrole': selected_role_id.id  
        }

        try:
            existing_record = arole.find_one(filter)

            if existing_record:
                arole.update_one(filter, {'$set': data})
            else:
                arole.insert_one(data)

            embed = discord.Embed(
                title="Success!",
                description=f"> Configuration updated",
                color=0x2b2d31
            )
            view = Rerun()
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"selected_role_id: {selected_role_id.id}")

class Rerun(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Rerun', style=discord.ButtonStyle.blurple)
    async def Rerun(self, interaction: discord.Interaction, button: discord.ui.Button):
          embed = discord.Embed(
        title=f"{interaction.guild.name}'s Config Panel",
        description="""**Configuration Setup**
Welcome to the configuration setup for our server! You can use this panel to customize various aspects of our bot's behavior. Follow the steps below to set up the bot according to your preferences:

1. **Permissions**:
   - Configure the staff role and admin role for your server.

2. **Channels**:
   - Configure channels such as the infraction channel, reports channel, promotion channel.

3. **Infraction Appeals**:
   - Enable or disable the Infraction Appeals module, allowing users to appeal their infractions.

4. **Moderation Module**:
   - This moderation module is *different* it uses a *standalone* point system its different as instead of other bots that use a point system that you have to have another moderation bot for to use it this one is built into the moderation system.

Please select an option from the dropdown menu below to get started. If you have any questions or need assistance, [**join the support server**](https://discord.gg/M7eGhqEFZG)""",
        color=discord.Color.dark_embed()
    )    
          
          embed.set_thumbnail(url=interaction.guild.icon)  
          embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
          embed.set_footer(text=f"Guild ID: {interaction.guild.id}")
          view = ConfigView()
          await interaction.response.edit_message(content=None, view=view, embed=embed)  







class Channels(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(InfractionChannel())
        self.add_item(ReportsChannel())
        self.add_item(PromotionChannel())
        self.add_item(LOAChannel())
        self.add_item(PartnershipChannel())
        self.add_item(StaffFeedbackChannel())

class Channels2(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(PartnershipChannel())

class Perms(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(StaffRole())
        self.add_item(AdminRole())

class AppealChannel(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(AppealsChannel())

class ChannelSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Channels', value='channels'),
            discord.SelectOption(label='Channels 2', value='channels2')
        ]
        super().__init__(placeholder="Select a channel configuration", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]

        if selected_option == 'channels':
            embed = discord.Embed(
                title="Server Channels Configuration",
                description="""
                Configure various channels for your server to enhance its functionality. Each channel serves a specific purpose and plays a crucial role in managing your server's activities.

                **Infractions Channel**:
                - This channel is dedicated to recording and managing user infractions, keeping your server organized and transparent.

                **Reports Channel**:
                - Use this channel for reporting issues or rule violations, providing an efficient way to address problems.

                **Promotion Channel**:
                - Utilize the Promotion Channel to acknowledge and celebrate staff achievements within your server. Keep your staff members motivated and informed about organizational advancements.

                **LOA Channel**:
                - Utilize the LOA Channel for leave of absence requests if a staff needs a break it'll be sent here.

                **Staff Feedback Channel**:
                - Utilize the Staff feedback channel for staff feedback; if a staff receives a review, it'll be sent here.

                Optimize your server's structure with these channels for a seamless experience!
                """,
                color=0x2b2d31
            )
            view = Channels()
        elif selected_option == 'channels2':
            embed = discord.Embed(
                title="Server Channels Configuration",
                description="""
                Configure various channels for your server to enhance its functionality. Each channel serves a specific purpose and plays a crucial role in managing your server's activities.

                **Partnerships Channel**:
                - This channel is dedicated to logging and managing partnerships.

                Optimize your server's structure with these channels for a seamless experience!
                """,
                color=0x2b2d31
            )
            view = Channels2()

        await interaction.response.edit_message(embed=embed, view=view)


class ChannelDropdowns(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ChannelSelect())

class Config(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Permissions', emoji='<:Config:1148610134147338381>'),
            discord.SelectOption(label='Channels', emoji=f'{folder}'),
            discord.SelectOption(label="Infraction Appeals", emoji=f'<:pending:1140623442962546699>'),
            discord.SelectOption(label="Moderation", emoji='<:Infraction:1162134605885870180>')

        
            
        ]
        super().__init__(placeholder='Config Menu', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]

        if color == 'Permissions':
            embed = discord.Embed(
        title="Configure Staff and Admin Roles",
        description="""
        **Staff Role**:
         Select a role that represents your server's staff members.
          Staff members with this role can request LOAs, send tags, answer modmail, and manage forums.

        **Admin Role**:
          Choose a role for your server's administrators.
          Admins with this role can access infractions, LOAs, Partnerships, and tags.

        **How to Configure**:
        1. Click the buttons below to select roles for each category.
    2. Once configured, you can proceed to set up other aspects of the bot.

        Remember to assign the appropriate roles for a smooth server experience!
        """,
        color=0x2b2d31
    )

            view = Perms()
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon) 
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_footer(text="Configuration is saved upon clicking.", icon_url="https://media.discordapp.net/ephemeral-attachments/1140411707953520681/1165221940722675722/1035353776460152892.png?ex=6546107f&is=65339b7f&hm=8d73392705483a84a47d09a7cd4838cd2e1235caa1022f10777ea1fec4a91f13&=")

        if color == 'Channels':
            embed = discord.Embed(
        title="Server Channels Configuration",
        description="* **Channels 1**\n> LOA Channel, Staff Feedback Channel, Promotions Channel, Infractions Channel, Reports Channel\n\n* **Channels 2**\n> Partnership Channel.",
        color=0x2b2d31
    ) 
            view = ChannelDropdowns()
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon) 
            embed.set_footer(text="Due to hitting the max dropdowns there is Channels 1 & 2", icon_url="https://media.discordapp.net/ephemeral-attachments/1140411707953520681/1165221940722675722/1035353776460152892.png?ex=6546107f&is=65339b7f&hm=8d73392705483a84a47d09a7cd4838cd2e1235caa1022f10777ea1fec4a91f13&=")
            

        if color == 'Infraction Appeals':
          embed = discord.Embed(title="Appeal Module", description="Please Select **Enable** or **Disable** to enable or disable the Appeal Module", color=0x2b2d31)
          view = AppealTogglable()
        if color == 'Moderation':
          view = ModerationConfigdrop()
          embed = discord.Embed(title="Moderation Module", description="* **Moderation Punishments**\n> Choose what roles can do certain role actions make sure this is a staff role and not a role normal members have.\n\n* **Logging**\n> This is the modlogs channel all moderation actions are logged here.\n> **Suggestion:** Make sure moderators can't delete stuff in this channel.\n\n* **Point Configuration**\n> Config different point values you can enable autoban aswell.", color=discord.Color.dark_embed())
          embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
          embed.set_thumbnail(url=interaction.guild.icon)
          
        await interaction.response.edit_message(embed=embed, view=view)

class ConfigView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Config())

class configuration(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(description="Configure the bot for your servers needs")
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
       embed = discord.Embed(
        title=f"{ctx.guild.name}'s Config Panel",
        description="""**Configuration Setup**
Welcome to the configuration setup for our server! You can use this panel to customize various aspects of our bot's behavior. Follow the steps below to set up the bot according to your preferences:

1. **Permissions**:
   - Configure the staff role and admin role for your server.

2. **Channels**:
   - Configure channels such as the infraction channel, reports channel, promotion channel.

3. **Infraction Appeals**:
   - Enable or disable the Infraction Appeals module, allowing users to appeal their infractions.

4. **Moderation Module**:
   - This moderation module is *different* it uses a *standalone* point system its different as instead of other bots that use a point system that you have to have another moderation bot for to use it this one is built into the moderation system.

Please select an option from the dropdown menu below to get started. If you have any questions or need assistance, [**join the support server**](https://discord.gg/M7eGhqEFZG)""",
        color=discord.Color.dark_embed()
    )    

       embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
       embed.set_thumbnail(url=ctx.guild.icon)        
       view = ConfigView()
       await ctx.send(embed=embed, view=view, ephemeral=True)


    @config.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to configure this server.\n<:Arrow:1115743130461933599>**Required:** ``Administrator``")              


async def setup(client: commands.Bot) -> None:
    await client.add_cog(configuration(client))     
        
        

        

        
