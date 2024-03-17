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
            await modmailcategory.update_one(filter, {'$set': data}, upsert=True)
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
            existing_record = await transcriptschannel.find_one(filter)

            if existing_record:
                await transcriptschannel.update_one(filter, {'$set': data})
            else:
                await transcriptschannel.insert_one(data)
            await interaction.response.edit_message(content=None)
            await refreshembed(interaction)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")          

class ModmailToggle(discord.ui.Select):
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Modmail': True}}, upsert=True)  
            await refreshembed(interaction)
        if color == 'Disable':    
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Modmail': False}}, upsert=True) 
            await refreshembed(interaction)   

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


        await modmailping.update_one({'guild_id': interaction.guild.id}, {'$set': data}, upsert=True)
        await interaction.response.edit_message(content=None)
        await refreshembed(interaction)
    
async def refreshembed(interaction):
            transcriptschannelresult = await transcriptschannel.find_one({'guild_id': interaction.guild.id})
            modmailcategoryresult = await modmailcategory.find_one({'guild_id': interaction.guild.id})
            transcriptschannels = "Not Configured"
            modmailcategorys = "Not Configured"
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            if moduleddata:
                modulemsg = moduleddata.get('Modmail', 'False')            
            modmailpingresult = await  modmailping.find_one({'guild_id': interaction.guild.id})
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
            embed.add_field(name="<:settings:1207368347931516928> Modmail Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Modmail Category:** {modmailcategorys}\n{replymiddle}**Modmail Pings:** {modmailroles}\n{replybottom}**Transcript Channel** {transcriptschannels}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)")
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)  
            try:    
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.")              
                 