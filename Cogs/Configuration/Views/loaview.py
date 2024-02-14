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
partnershipch = db['partnership channel']
appealable = db['Appeal Toggle']
appealschannel = db['Appeals Channel']
loachannel = db['LOA Channel']
partnershipsch = db['Partnerships Channel']
modules = db['Modules']



class LOAChannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(placeholder='LOA Channel', channel_types=[discord.ChannelType.text])
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
            existing_record = loachannel.find_one(filter)

            if existing_record:
                loachannel.update_one(filter, {'$set': data})
            else:
                loachannel.insert_one(data)
            await interaction.response.edit_message(content=None)
            await refreshembed(interaction)

        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")  

class LOARoled(discord.ui.RoleSelect):
    def __init__(self, author):
        super().__init__(placeholder='LOA Role')
        self.author = author
        
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_id = self.values[0]

        filter = {
            'guild_id': interaction.guild.id
        }        
        data = {
            'guild_id': interaction.guild.id, 
            'staffrole': selected_role_id.id  
        }
        try:
            existing_record = LOARole.find_one(filter)

            if existing_record:
                LOARole.update_one(filter, {'$set': data})
            else:
                LOARole.insert_one(data)
            await interaction.response.edit_message(content=None)
            await refreshembed(interaction)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"selected_role_id: {selected_role_id.id}")

class ToggleLOADropdown(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Enable"),
            discord.SelectOption(label="Disable"),
            

        
            
        ]
        super().__init__(placeholder='Module Toggle', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        if color == 'Enable':    
            await interaction.response.send_message(content=f"{tick} Enabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'LOA': True}}, upsert=True)  
            await refreshembed(interaction)
        if color == 'Disable':    
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'LOA': False}}, upsert=True) 
            await refreshembed(interaction)


async def refreshembed(interaction):
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
            embed = discord.Embed(title="<:LOA:1164969910238203995> LOA Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> LOA Configuration", value=f"<:replytop:1207366581735129118>**Enabled:** {modulemsg}\n<:replymiddle:1207366662916014100>**LOA Channel:** {loachannelmsg}\n<:replybottom:1207366623913316363>**LOA Role:** {loarolemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
            await interaction.message.edit(embed=embed)   
     