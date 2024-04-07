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


class ToggleForums(discord.ui.Select):
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Forums': True}}, upsert=True)    
            await refreshembed(interaction)  
        if color == 'Disabled':  
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Forums': False}}, upsert=True)    
            await refreshembed(interaction)        

async def refreshembed(interaction):
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})            
            modulemsg = "True"
            if moduleddata:
                modulemsg = f"{moduleddata['Forums']}"            
            embed = discord.Embed(title="<:forum:1162134180218556497> Forum Utilites", description=f"**Enabled:** {modulemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())    
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            try:    
             await interaction.message.edit(embed=embed)  
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.")              