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
options = db['module options']
class FeedbackChannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(placeholder='Feedback Channel', channel_types=[discord.ChannelType.text])
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
            existing_record = await feedbackch.find_one(filter)

            if existing_record:
                await feedbackch.update_one(filter, {'$set': data})
            else:
                await feedbackch.insert_one(data)
            await interaction.response.edit_message(content=None)
            await refreshembed(interaction)
        except Exception as e:
            print(f"[⚠️] An error occurred: {str(e)}")

        print(f"[#️⃣] Channel ID: {channelid.id}")        

class ToggleFeedback(discord.ui.Select):
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Feedback': True}}, upsert=True)  
            await refreshembed(interaction)
        if color == 'Disable':    
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Feedback': False}}, upsert=True)
            await refreshembed(interaction)

class MultipleFeedback(discord.ui.View):    
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Multiple Feedback", style=discord.ButtonStyle.red) 
    async def bybuttontoggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        optionresult = await options.find_one({'guild_id': interaction.guild.id})
        if optionresult.get('multiplefeedback', False) == False:
                self.bybuttontoggle.style = discord.ButtonStyle.green
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'multiplefeedback': True}}, upsert=True)
        else:
                self.bybuttontoggle.style = discord.ButtonStyle.red        
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'multiplefeedback': False}}, upsert=True)
        await interaction.response.edit_message(content="", view=self)   


class FMoreOptions(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Multiple Feedbacks" ,description="Lets you give more then 1 feedback to people."),

            

        
            
        ]
        super().__init__(placeholder='More Options', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
        

        option_result = await options.find_one({'guild_id': interaction.guild.id})
        if option_result is None:
            await options.insert_one({'guild_id': interaction.guild.id})
        if selected_option == "Multiple Feedbacks":
                view = MultipleFeedback()
                embed = discord.Embed(title='Multiple Feedbacks', description="Allows you give someone feedback more then once.", color=discord.Colour.dark_embed())

                if option_result:
                    if option_result.get('multiplefeedback', False) == False:
                        view.bybuttontoggle.style = discord.ButtonStyle.red
                        
                    elif option_result.get('multiplefeedback', False) == True:
                        view.bybuttontoggle.style = discord.ButtonStyle.green
                        
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def refreshembed(interaction):
            feedbackchannelresult = await feedbackch.find_one({'guild_id': interaction.guild.id})
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            feedbackchannelmsg = "Not Configured"
            if moduleddata:
                modulemsg = f"{moduleddata['Feedback']}"
            if feedbackchannelresult:    
                channelid = feedbackchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    feedbackchannelmsg = "<:Error:1126526935716085810> Channel wasn't found please reconfigure."
                else:    
                 feedbackchannelmsg = channel.mention                
            embed = discord.Embed(title="<:Rate:1162135093129785364> Staff Feedback Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Staff Feedback Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Feedback Channel:** {feedbackchannelmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon) 
            try:
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("[⚠️] Couldn't edit module due to missing permissions.")              
                  
