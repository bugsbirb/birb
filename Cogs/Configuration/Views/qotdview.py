import discord
import os
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *
import datetime
MONGO_URL = os.getenv('MONGO_URL')

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo['astro']
modules = db['Modules']
qotds = db['qotd']

class ToggleQOTD(discord.ui.Select):
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

            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'QOTD': True}}, upsert=True)    
            await refreshembed(interaction)
            await qotds.update_one({'guild_id': interaction.guild.id}, {'$set': {'nextdate': datetime.datetime.now() + datetime.timedelta(days=1)}}, upsert=True)
            nextdate = datetime.datetime.now() + datetime.timedelta(days=1)
            timestamp = f"<t:{int(nextdate.timestamp())}>"
            embed = discord.Embed(title=f"{greencheck} Succesfully Enabled Daily messages", description=f"**Next Post Date:** {timestamp}", color=discord.Color.brand_green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        if color == 'Disabled':  
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Utility': False}}, upsert=True)    
            await refreshembed(interaction)        

class QOTDChannel(discord.ui.ChannelSelect):
    def __init__(self, author, channels):
        super().__init__(placeholder='Channel',  channel_types=[discord.ChannelType.text, discord.ChannelType.news], default_values=channels)
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
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
            await qotds.update_one(filter, {'$set': data}, upsert=True)
            await refreshembed(interaction)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")  

class PingRole(discord.ui.RoleSelect):
    def __init__(self, author, roles):
        super().__init__(placeholder='Message Ping', default_values=roles)
        self.author = author
        
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_id = self.values[0]

        filter = {
            'guild_id': interaction.guild.id
        }        
        data = {
            'guild_id': interaction.guild.id, 
            'pingrole': selected_role_id.id  
        }
        try:

            await qotds.update_one(filter, {'$set': data}, upsert=True)
            await interaction.response.edit_message(content=None)
            await refreshembed(interaction)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"selected_role_id: {selected_role_id.id}")

async def refreshembed(interaction):
            qotd = await qotds.find_one({'guild_id': interaction.guild.id})
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})
            pingmsg = "Not Configured"
            channelmsg = "Not Configured"

            if (
                qotd
                and qotd.get('channel_id')
            ):
             channelmsg = f"<#{qotd.get('channel_id')}>"
            if (
                qotd
                and qotd.get('pingrole')
            ):
                pingmsg = f"<@&{qotd.get('pingrole')}>"


            if moduleddata:
                modulemsg = moduleddata.get('QOTD', 'False')     
            embed = discord.Embed(title="<:qotd:1231270156647403630> Daily Questions", description=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Channel:** {channelmsg}\n{replybottom}**Ping:** {pingmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)                       
            try:
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.")             