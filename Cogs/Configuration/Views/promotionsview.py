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
promotionroles = db['promotion roles']

class Promotionchannel(discord.ui.ChannelSelect):
    def __init__(self, author, channels):
        super().__init__(placeholder='Promotion Channel',   channel_types=[discord.ChannelType.text], default_values=channels)
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
            await promochannel.update_one(filter, {'$set': data}, upsert=True)
            await refreshembed(interaction) 
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")        

class Promotionrank(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Create"),
            discord.SelectOption(label="Delete"),
            discord.SelectOption(label="View")
            

        
            
        ]
        super().__init__(placeholder='Promotion Ranks', min_values=1, max_values=1, options=options)
         
        


    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == 'Create':
             view = discord.ui.View(timeout=None)
             view.add_item(PromotionRanks(self.author))
             await interaction.response.send_message(content=f"{dropdown} Now select the rank you want to manage.", view=view, ephemeral=True)
        elif selected == 'Delete':
             view = discord.ui.View(timeout=None)
             view.add_item(DeleteRank(self.author))
             await interaction.response.send_message(content=f"{dropdown} Now select the rank you want to delete.", view=view, ephemeral=True)
        elif selected == 'View':
            ranks = promotionroles.find({'guild_id': interaction.guild.id})
            
            embed = discord.Embed(title="Promotion Ranks")
            embed.set_thumbnail(url=interaction.guild.icon)

            if ranks is None:
                embed.description = "There is no current promotion ranks."
            ranks = await ranks.to_list(None)       
            if ranks:         
             for rank in ranks:
                role = interaction.guild.get_role(rank['rank'])
                roles = [interaction.guild.get_role(role_id) for role_id in rank['promotionranks'] if interaction.guild.get_role(role_id)]
                if roles:
                    value = ', '.join([f"<@&{role.id}>" for role in roles])
                    if role:
                     embed.add_field(name=f"{role.name}", value=value)
            await interaction.response.send_message(embed=embed, ephemeral=True)


             
                  

class PromotionRanks(discord.ui.RoleSelect):
    def __init__(self, author):
        super().__init__(placeholder='Add Rank', max_values=1)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          
        view = discord.ui.View(timeout=None)
        view.add_item(AdditonalRoles(self.author, self.values[0].id))
        await interaction.response.edit_message(content=f"{dropdown} Now select roles that will also be added when promoted with `{self.values[0].name}`.", view=view)

class DeleteRank(discord.ui.RoleSelect):
    def __init__(self, author):
        super().__init__(placeholder='Delete Rank', max_values=1)
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await promotionroles.delete_one({'guild_id': interaction.guild.id, 'rank': self.values[0].id})
        await interaction.response.edit_message(content=f"{tick} Succesfully deleted promotion rank.", view=None)



class AdditonalRoles(discord.ui.RoleSelect):
    def __init__(self, author, rank):
        super().__init__(placeholder='Additional roles', max_values=10)
        self.author = author
        self.rank = rank
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
  
        data = {
            'guild_id': interaction.guild.id,
            'rank': self.rank,
            'promotionranks': selected_role_ids
        }


        await promotionroles.update_one({'guild_id': interaction.guild.id, 'rank': self.rank}, {'$set': data}, upsert=True)
        await interaction.response.edit_message(content=f"{tick} Succesfully set up additional roles for the rank.", view=None)


class PromotionModuleToggle(discord.ui.Select):
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Promotions': True}}, upsert=True)  
            await refreshembed(interaction)

            
        if color == 'Disabled':  
             
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
                 promochannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else: 
                 promochannelmsg = channel.mention                          
            embed = discord.Embed(title="<:Promote:1162134864594735315> Promotions Module", color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Promotions Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Promotion Channel:** {promochannelmsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)\n\n<:Information:1115338749728002089> **What are Promotion Ranks?:** Promotion ranks enable you to choose a primary role and automatically include any additional selected roles. When you use the command /promote and select a rank, it will assign the chosen primary role along with any additional roles you've selected.", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    
            try:
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.")              