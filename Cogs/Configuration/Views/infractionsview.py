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

nfractiontypes = db['infractiontypes']
class InfractionChannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(placeholder='Infractions Channel', channel_types=[discord.ChannelType.text])
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
            existing_record = await infchannel.find_one(filter)

            if existing_record:
                await infchannel.update_one(filter, {'$set': data})
            else:
                await infchannel.insert_one(data)
            await refreshembed(self, interaction)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")        

class ToggleInfractionsDropdown(discord.ui.Select):
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'infractions': True}}, upsert=True)  
            await refreshembed(self, interaction)
        if color == 'Disable':    
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'infractions': False}}, upsert=True)            
            await refreshembed(self, interaction)
class InfractionTypes(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Create"),
            discord.SelectOption(label="Delete"),
        ]
        super().__init__(placeholder='Infraction Types', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        type_action = self.values[0]

        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)   

        if type_action == 'Create':
            await interaction.response.send_modal(CreateInfractionModal(self.author))
        elif type_action == 'Delete':
            await interaction.response.send_modal(DeleteInfractionModal(self.author))




class CreateInfractionModal(discord.ui.Modal):
    def __init__(self, author):
        self.author = author
        super().__init__(title="Create Infraction Type")

        self.type_input = discord.ui.TextInput(
            label='Type',
            placeholder='What is the infraction type?',
            max_length=30,
        )

        self.add_item(self.type_input)

    async def on_submit(self, interaction: discord.Interaction):
        
        type_value = self.type_input.value   
        filterm = {
            'guild_id': interaction.guild.id,
            'types': {'$in': [type_value]}
        }

        types = await nfractiontypes.find_one(filterm)
        infractiontypesresult = await nfractiontypes.find_one({'guild_id': interaction.guild.id})

        infractiontypescount = len(infractiontypesresult['types'])
        if infractiontypescount >= 15:
            return await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, You have reached the maximum amount of infraction types (15)", ephemeral=True)
        if types:
            return await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, Infraction type already exists", ephemeral=True)



        await nfractiontypes.update_one(
    {'guild_id': interaction.guild.id},
    {'$addToSet': {'types': type_value}},
    upsert=True
)
        await refreshembed(self, interaction)
        await interaction.response.send_message(content=f"{tick} **{interaction.user.display_name}**, Infraction type created successfully", ephemeral=True)
        

class DeleteInfractionModal(discord.ui.Modal):
    def __init__(self, author):
        self.author = author
        super().__init__(title="Delete Infraction Type")

        self.type_input = discord.ui.TextInput(
            label='Type',
            placeholder='What is the infraction type?',
        )

        self.add_item(self.type_input)

    async def on_submit(self, interaction: discord.Interaction):
        type_value = self.type_input.value   
        filterm = {
            'guild_id': interaction.guild.id,
            'types': {'$in': [type_value]}
        }

        types = await nfractiontypes.find_one(filterm)
        if types is None:
            return await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, Infraction type not found.", ephemeral=True)

        await nfractiontypes.update_one(
    {'guild_id': interaction.guild.id},
    {'$pull': {'types': type_value}},
    upsert=True
)


        await interaction.response.send_message(content=f"{tick} **{interaction.user.display_name}**, Infraction type deleted successfully", ephemeral=True)
        await refreshembed(self, interaction)
async def refreshembed(self, interaction):
            infractionchannelresult = await infchannel.find_one({'guild_id': interaction.guild.id})
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            infchannelmsg = "Not Configured"
            infractiontypess = "Activity Notice, Verbal Warning, Warning, Strike, Demotion, Termination"
            infractiontyperesult = await nfractiontypes.find_one({'guild_id': interaction.guild.id})
            if infractiontyperesult:
                infractiontypess = infractiontyperesult['types']
                infractiontypess = ', '.join(infractiontypess)
                
            if moduleddata:
                modulemsg = f"{moduleddata['infractions']}"
            if infractionchannelresult:    
                channelid = infractionchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    infchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else:    
                 infchannelmsg = channel.mention          

            infractiontypescount = len(infractiontyperesult['types'])
            if infractiontypescount == None:
                infractiontypess = "0"
            embed = discord.Embed(title="<:Infraction:1162134605885870180> Infractions Module",  color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Infractions Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Infraction Channel:** {infchannelmsg}\n{replybottom}**Infraction Types [{infractiontypescount}/15]** {infractiontypess}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    
            try:
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.")              