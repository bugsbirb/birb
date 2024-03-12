import discord
import os
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')
from motor.motor_asyncio import AsyncIOMotorClient
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

class Promotionchannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(placeholder='Promotion Channel',   channel_types=[discord.ChannelType.text])
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
            existing_record = promochannel.find_one(filter)

            if existing_record:
                await promochannel.update_one(filter, {'$set': data})
            else:
                await promochannel.insert_one(data)

            await refreshembed(interaction) 
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")        

class PromotionModuleToggle(discord.ui.Select):
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Promotions': True}}, upsert=True)  
            await refreshembed(interaction)

            
        if color == 'Disable':    
             
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Promotions': False}}, upsert=True) 
            await refreshembed(interaction)
            
                      

    
async def refreshembed(interaction):
            promochannelresult = await promochannel.find_one({'guild_id': interaction.guild.id})
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})
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
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    
            try:
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.")              