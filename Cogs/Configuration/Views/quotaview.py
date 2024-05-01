import discord
import os
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *
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





class QuotaToggle(discord.ui.Select):
    def __init__(self, author, options):
        self.author = author

        super().__init__(placeholder='Module Toggle', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        if color == 'Enabled':    
            await interaction.response.send_message(content=f"{tick} Enabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Quota': True}}, upsert=True)  
            await refreshembed(interaction)

        if color == 'Disabled':  
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Quota': False}}, upsert=True) 
            await refreshembed(interaction)


class IgnoredChannel(discord.ui.ChannelSelect):
    def __init__(self, author, channels):
        super().__init__(placeholder='Ignored Channels', channel_types=[discord.ChannelType.text, discord.ChannelType.news], default_values=channels, max_values=25)
        self.author = author
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
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
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
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