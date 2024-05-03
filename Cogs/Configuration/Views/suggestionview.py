import discord
import os
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo['astro']
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
suggestschannel = db["suggestion channel"]
suggestschannel2 = db["Suggestion Management Channel"]
class SuggestionsChannel(discord.ui.ChannelSelect):
    def __init__(self, author, channel):
        super().__init__(placeholder='Suggestion Channel',   channel_types=[discord.ChannelType.text, discord.ChannelType.news], default_values=channel)
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                  
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = await suggestschannel.find_one(filter)

            if existing_record:
                await suggestschannel.update_one(filter, {'$set': data})
            else:
                await suggestschannel.insert_one(data)
            await refreshembed(interaction)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")        

class SuggestionsChannelManagement(discord.ui.ChannelSelect):
    def __init__(self, author, channels):
        super().__init__(placeholder='Suggestions Management Channel',   channel_types=[discord.ChannelType.text, discord.ChannelType.news], default_values=channels)
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                  
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'channel_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = await suggestschannel2.find_one(filter)

            if existing_record:
                await suggestschannel2.update_one(filter, {'$set': data})
            else:
                await suggestschannel2.insert_one(data)
            await refreshembed(interaction)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")    

class ToggleSuggestions(discord.ui.Select):
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Suggestions': True}}, upsert=True)  
            await refreshembed(interaction)
        if color == 'Disabled':  
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Suggestions': False}}, upsert=True)
            await refreshembed(interaction)


async def refreshembed(interaction):
            suschannelresult = await suggestschannel.find_one({'guild_id': interaction.guild.id})
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            suggestionchannelmsg = "Not Configured"
            smschannelresult = await suggestschannel2.find_one({'guild_id': interaction.guild.id})
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
            embed = discord.Embed(title="<:announcement:1192867080408682526> Suggestions Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Suggestions Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Suggestion Channel:** {suggestionchannelmsg}\n{replybottom}**Suggestions Management Channel:** {smschannelmsg}\n\n<:Tip:1223062864793702431> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    
            try:
             await interaction.message.edit(embed=embed)     
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.") 