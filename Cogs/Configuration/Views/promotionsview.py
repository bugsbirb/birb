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
options = db['module options']
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
            await promochannel.update_one(filter, {'$set': data}, upsert=True)
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
            
class PMoreOptions(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
             discord.SelectOption(label="Promotion Issuer Button" ,description="A disabled button that displays the username of the issuer."),
            discord.SelectOption(label="Auto Role" ,description="Automaticly roles the user the rank."),
            discord.SelectOption(label="Show Issuer", description="If disabled this will make all promotions annonymous."),
            

        
            
        ]
        super().__init__(placeholder='More Options', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
        

        option_result = await options.find_one({'guild_id': interaction.guild.id})
        if option_result is None:
            await options.insert_one({'guild_id': interaction.guild.id})
        if selected_option == "Auto Role":
                view = AutoRole()
                embed = discord.Embed(title='Auto Role', description="If you **disable** this it will no longer give the user the rank automatically.", color=discord.Colour.dark_embed())
                if option_result:
                    if option_result.get('Auto Role', True) == False:
                        view.bybuttontoggle.style = discord.ButtonStyle.red
                        
                    elif option_result.get('Auto Role', True) == True:
                        view.bybuttontoggle.style = discord.ButtonStyle.green
                        
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        elif selected_option == 'Show Issuer':
                view = PShowIssuer()
                embed = discord.Embed(title='Show Issuer', description="If you **disable** this it will make all promotions annonymous. This doesn't work with customisation embeds and it removes the embed author so if the `Promotion Issuer Button` is enabled the button will still appear.", color=discord.Colour.dark_embed())
                if option_result.get('pshowissuer', True) == False:
                        view.bybuttontoggle.style = discord.ButtonStyle.red
                         
                elif option_result.get('pshowissuer', True) == True:
                        view.bybuttontoggle.style = discord.ButtonStyle.green
                        
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)                    

        elif selected_option == 'Promotion Issuer Button':
                view = PromotionByButton()
                embed = discord.Embed(title='Promotion Issuer Button', description="", color=discord.Colour.dark_embed())
                embed.set_image(url="https://cdn.discordapp.com/attachments/1119278127772860489/1218957171560153098/image.png?ex=66098d54&is=65f71854&hm=dfa18ebbb548fc18cf2c4f640d28ff29e392d42e208ed8574ba04e5ebbcbef0f&")
                if option_result:
                    if option_result.get('promotionissuer', False) == False:
                        view.bybuttontoggle.style = discord.ButtonStyle.red
                        
                    elif option_result.get('promotionissuer', False) == True:
                        view.bybuttontoggle.style = discord.ButtonStyle.green
                        
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)   

class AutoRole(discord.ui.View):    
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Autorole", style=discord.ButtonStyle.green) 
    async def bybuttontoggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        optionresult = await options.find_one({'guild_id': interaction.guild.id})
        if optionresult.get('autorole', True) == False:
                self.bybuttontoggle.style = discord.ButtonStyle.green
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'autorole': True}}, upsert=True)
        else:
                self.bybuttontoggle.style = discord.ButtonStyle.red        
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'autorole': False}}, upsert=True)
        await interaction.response.edit_message(content="", view=self)     
class PShowIssuer(discord.ui.View):    
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Show Issuer", style=discord.ButtonStyle.green) 
    async def bybuttontoggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        optionresult = await options.find_one({'guild_id': interaction.guild.id})
        if optionresult.get('pshowissuer', True) == False:
                self.bybuttontoggle.style = discord.ButtonStyle.green
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'pshowissuer': True}}, upsert=True)
        else:
                self.bybuttontoggle.style = discord.ButtonStyle.red        
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'pshowissuer': False}}, upsert=True)
        await interaction.response.edit_message(content="", view=self)     
    
class PromotionByButton(discord.ui.View):    
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Issuer Button Display", style=discord.ButtonStyle.red) 
    async def bybuttontoggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        optionresult = await options.find_one({'guild_id': interaction.guild.id})
        if optionresult.get('promotionissuer', False) == False:
                self.bybuttontoggle.style = discord.ButtonStyle.green
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'promotionissuer': True}}, upsert=True)
        else:
                self.bybuttontoggle.style = discord.ButtonStyle.red        
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'promotionissuer': False}}, upsert=True)
        await interaction.response.edit_message(content="", view=self)      


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