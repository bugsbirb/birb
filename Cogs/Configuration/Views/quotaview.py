import discord
import os
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *
from datetime import datetime, timedelta

import re
MONGO_URL = os.getenv('MONGO_URL')

mongo = AsyncIOMotorClient(MONGO_URL)
dbq = mongo['quotab']
message_quota_collection = dbq["message_quota"]

ignoredchannels = dbq['Ignored Quota Channels']

client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
modules = db['Modules']
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
autoactivity = db['auto activity']




class QuotaToggle(discord.ui.Select):
    def __init__(self, author, options):
        self.author = author

        super().__init__(placeholder='Module Toggle', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        if color == 'Enabled':    
            await interaction.response.send_message(content=f"{tick} Enabled", ephemeral=True)
            await  modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Quota': True}}, upsert=True)  
            await refreshembed(interaction)

        if color == 'Disabled':  
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Quota': False}}, upsert=True) 
            await refreshembed(interaction)


class IgnoredChannel(discord.ui.ChannelSelect):
    def __init__(self, author, channels):
        super().__init__(placeholder='Ignored Channels', channel_types=[discord.ChannelType.text, discord.ChannelType.news], default_values=channels, max_values=25)
        self.author = author
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer(ephemeral=True)
                  
        channelids = [channel.id for channel in self.values]

        filter = {
            'guild_id': interaction.guild.id
        }

        try:
            await ignoredchannels.update_one(filter, {'$set': {'channel_ids': channelids}}, upsert=True)
            await refreshembed(interaction)
            await interaction.edit_original_response(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel IDs: {channelids}")

class AutoActivity(discord.ui.Select):
    def __init__(self, author):
        self.author = author
    
        options = [
        discord.SelectOption(label="Toggle", emoji="<:Button:1223063359184830494>"),
        discord.SelectOption(label="Channel", emoji=f"{tagsemoji}"),
        discord.SelectOption(label="Post Date", emoji="<:time:1158064756104630294>"),
        ]
        super().__init__(placeholder='Auto Activity', min_values=1, max_values=1, options=options)    

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)  
        
        view = discord.ui.View()
        if selection == 'Toggle':
            
            view.add_item(ActivityToggle(interaction.user))
            await interaction.response.send_message(view=view, ephemeral=True)
        if selection == 'Channel':
            view.add_item(PostChannel(interaction.user))
            await interaction.response.send_message(view=view, ephemeral=True)
        if selection == 'Post Date':
            await interaction.response.send_modal(PostDate())



class PostDate(discord.ui.Modal, title='How often?'):
    
     postdate = discord.ui.TextInput(label='Post Day', placeholder="What day do you want it to post every week? (Monday, Tuesday etc)", style=discord.TextStyle.short)


     async def on_submit(self, interaction: discord.Interaction):
            days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'tuesday']
            specified_day = self.postdate.value.lower()
            
            if specified_day not in days:
                await interaction.response.send_message("Invalid day specified. Please enter a valid day of the week.", ephemeral=True)
                return
            current_day_index = datetime.utcnow().weekday()  
            specified_day_index = days.index(specified_day)
            
            days_until_next_occurrence = (specified_day_index - current_day_index) % 7
            
            if days_until_next_occurrence <= 0:
                days_until_next_occurrence += 7      
            next_occurrence_date = datetime.utcnow() + timedelta(days=days_until_next_occurrence - 1 )
            await autoactivity.update_one({'guild_id': interaction.guild.id}, {'$set': {'day': self.postdate.value, 'nextdate': next_occurrence_date}}, upsert=True)
            embed = discord.Embed(title="Succesfull!", color=discord.Color.brand_green(), description=f"**Next Post Date:** <t:{int(next_occurrence_date.timestamp())}>")
            
            await interaction.response.send_message(embed=embed,  ephemeral=True)


        


class PostChannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(placeholder='Post Channel', channel_types=[discord.ChannelType.text, discord.ChannelType.news])
        self.author = author
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer(ephemeral=True)
                  
        channelid = interaction.channel.id


        filter = {
            'guild_id': interaction.guild.id
        }

        try:
            await autoactivity.update_one(filter, {'$set': {'channel_id': channelid}}, upsert=True)
            await interaction.edit_original_response(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel IDs: {channelid}")
class ActivityToggle(discord.ui.Select):
    def __init__(self, author):
        self.author = author

        

        options = [
        discord.SelectOption(label="Enabled"),
        discord.SelectOption(label="Disabled"),
        ]
        super().__init__(placeholder='Activity Toggle', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        if color == 'Enabled':    
            await interaction.response.send_message(content=f"{tick} Enabled", ephemeral=True)
            await autoactivity.update_one({'guild_id': interaction.guild.id}, {'$set': {'enabled': True}}, upsert=True)  

        if color == 'Disabled':  
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await autoactivity.update_one({'guild_id': interaction.guild.id}, {'$set': {'enabled': False}}, upsert=True)       
        

class QuotaAmount(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="100"),
            discord.SelectOption(label="200"),
            discord.SelectOption(label="300"),
            discord.SelectOption(label="500"),        
            discord.SelectOption(label="Custom Amount"),                   
        ]
        super().__init__(placeholder='Quota Amount', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        if color == 'Custom Amount':        
            await interaction.response.send_modal(MessageQuota())
        else:    
         await message_quota_collection.update_one(
            {'guild_id': interaction.guild.id},
            {'$set': {'quota': color}},
            upsert=True  
        )            
         await interaction.response.edit_message(content=None)
         await refreshembed(interaction)


class MessageQuota(discord.ui.Modal, title='Quota Amount'):

    quota = discord.ui.TextInput(
        label='Message Quota',
        placeholder='Enter the guild\'s message quota here...',
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            quota_value = int(self.quota.value)
        except ValueError:
            await interaction.response.send_message('Invalid input. Please enter a valid number for the message quota.', ephemeral=True)
            return


        guild_id = interaction.guild.id

        await message_quota_collection.update_one(
            {'guild_id': guild_id},
            {'$set': {'quota': quota_value}},
            upsert=True  
        )
        await interaction.response.send_message(content=f"{tick} Succesfully updated message quota.", ephemeral=True)
        await refreshembed(interaction)
        

        


async def refreshembed(interaction):
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})            
            messagequotdata = await message_quota_collection.find_one({'guild_id': interaction.guild.id})
            messagecountmsg = "Not Configured"
            if messagequotdata:
                messagecountmsg = f"{messagequotdata['quota']}"
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Quota']}"            
            embed = discord.Embed(title="<:quota:1234994790056198175> Message Quota Module",  color=discord.Color.dark_embed())    
            embed.add_field(name="<:settings:1207368347931516928> Message Quota Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Quota:** {messagecountmsg}\n\n<:Tip:1223062864793702431> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)      
            try:     
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.")            