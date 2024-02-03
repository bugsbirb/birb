import discord
import os
from pymongo import MongoClient
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')

mongo = MongoClient(MONGO_URL)
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
appealable = db['Appeal Toggle']
appealschannel = db['Appeals Channel']
loachannel = db['LOA Channel']
partnershipsch = db['Partnerships Channel']
modules = db['Modules']
modmailcategory = db['modmailcategory']
modmailping = db['modmailping']
transcriptschannel = db['transcriptschannel']
class ModmailCategory(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(placeholder='Modmail Category', channel_types=[discord.ChannelType.category])
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                  
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id
        }        

        data = {
            'category_id': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:
            existing_record = modmailcategory.find_one(filter)

            if existing_record:
                modmailcategory.update_one(filter, {'$set': data})
            else:
                modmailcategory.insert_one(data)
            await interaction.response.edit_message(content=None)
            await refreshembed(interaction)        
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")        

class TranscriptChannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(placeholder='Transcripts Channel', channel_types=[discord.ChannelType.text])
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
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
            existing_record = transcriptschannel.find_one(filter)

            if existing_record:
                transcriptschannel.update_one(filter, {'$set': data})
            else:
                transcriptschannel.insert_one(data)
            await interaction.response.edit_message(content=None)
            await refreshembed(interaction)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")          

   

class ModmailPing(discord.ui.RoleSelect):
    def __init__(self, author):
        super().__init__(placeholder='Modmail Ping', max_values=25)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
  
        data = {
            'guild_id': interaction.guild.id,
            'modmailping': [selected_role_ids]
        }


        modmailping.update_one({'guild_id': interaction.guild.id}, {'$set': data}, upsert=True)
        await refreshembed(interaction)
    
async def refreshembed(interaction):
            transcriptschannelresult = transcriptschannel.find_one({'guild_id': interaction.guild.id})
            modmailcategoryresult = modmailcategory.find_one({'guild_id': interaction.guild.id})
            transcriptschannels = "Not Configured"
            modmailcategorys = "Not Configured"
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
            embed = discord.Embed(title="<:messagereceived:1201999712593383444> Modmail", description=f"**Modmail Category:** {modmailcategorys}\n**Modmail Pings:** {modmailroles}\n**Transcript Channel:** {transcriptschannels}", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)     
            await interaction.message.edit(embed=embed)
                 