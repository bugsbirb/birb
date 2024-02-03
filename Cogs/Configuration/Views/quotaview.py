import discord
import os
from pymongo import MongoClient
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')

mongo = MongoClient(MONGO_URL)
dbq = mongo['quotab']
message_quota_collection = dbq["message_quota"]

client = MongoClient(MONGO_URL)
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
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Quota': True}}, upsert=True)  
            await refreshembed(interaction)

        if color == 'Disable':    
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Quota': False}}, upsert=True) 
            await refreshembed(interaction)


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
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        if color == 'Custom Amount':        
            await interaction.response.send_modal(MessageQuota())
        else:    
         message_quota_collection.update_one(
            {'guild_id': interaction.guild.id},
            {'$set': {'quota': color}},
            upsert=True  
        )            
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

        message_quota_collection.update_one(
            {'guild_id': guild_id},
            {'$set': {'quota': quota_value}},
            upsert=True  
        )
        await refreshembed(interaction)
        await interaction.followup.send(content=f"{tick} Succesfully updated message quota.", ephemeral=True)

        


async def refreshembed(interaction):
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
            await interaction.message.edit(embed=embed)
           