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
ApplicationsChannel = db['Applications Channel']
ApplicationsRolesDB = db['Applications Roles']
class ToggleApplications(discord.ui.Select):
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Applications': True}}, upsert=True) 
            await refreshembed(interaction)   

        if color == 'Disable':    
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Applications': False}}, upsert=True)    
            await refreshembed(interaction)        

class ApplicationChannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(placeholder='Application Channel',  channel_types=[discord.ChannelType.text])
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
            existing_record = await ApplicationsChannel.find_one(filter)

            if existing_record:
                await ApplicationsChannel.update_one(filter, {'$set': data})
            else:
                await ApplicationsChannel.insert_one(data)

            await interaction.response.edit_message(content=None)
            await refreshembed(interaction)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")            


class ApplicationsRoles(discord.ui.RoleSelect):
    def __init__(self, author):
        super().__init__(placeholder='Passed Application Roles', max_values=20)
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
  
        data = {
            'guild_id': interaction.guild.id,
            'applicationroles': selected_role_ids
        }


        await ApplicationsRolesDB.update_one({'guild_id': interaction.guild.id}, {'$set': data}, upsert=True)
        await interaction.response.edit_message(content=None)
        await refreshembed(interaction)
        print(f"Select Application Roles: {selected_role_ids}")


async def refreshembed(interaction):
            applicationchannelresult = await ApplicationsChannel.find_one({'guild_id': interaction.guild.id})
            staffroleresult = await ApplicationsRolesDB.find_one({'guild_id': interaction.guild.id})
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})

            approlemsg = "Not Configured"
            appchannelmsg = "Not Configured"

            if moduleddata:
                modulemsg = moduleddata.get('Applications', 'False')
            else:
                modulemsg = 'False'

            if staffroleresult:
                staff_roles_ids = staffroleresult.get('applicationroles', [])
                if not isinstance(staff_roles_ids, list):
                    staff_roles_ids = [staff_roles_ids]
                staff_roles_mentions = [discord.utils.get(interaction.guild.roles, id=role_id).mention
                                        for role_id in staff_roles_ids if discord.utils.get(interaction.guild.roles, id=role_id) is not None]
                if not staff_roles_mentions:
                    approlemsg = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
                else:
                    approlemsg = ", ".join(staff_roles_mentions)


            if applicationchannelresult:
                channelid = applicationchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    appchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else:
                    appchannelmsg = channel.mention

            embed = discord.Embed(title="<:ApplicationFeedback:1178754449125167254> Applications Result Module",
                                   description=f"",
                                   color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Applications Configuration",
                            value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Results Channel:** {appchannelmsg}\n{replybottom}**Application Roles:** {approlemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
                            inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            try:
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.") 