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
premium = db['premium']

nfractiontypes = db['infractiontypes']
infractiontypeactions = db['infractiontypeactions']
options = db['module options']
class InfractionChannel(discord.ui.ChannelSelect):
    def __init__(self, author, channels):
        super().__init__(placeholder='Infractions Channel', channel_types=[discord.ChannelType.text, discord.ChannelType.news], default_values=channels)
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'infractions': True}}, upsert=True)  
            await refreshembed(self, interaction)
        if color == 'Disabled':  
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'infractions': False}}, upsert=True)            
            await refreshembed(self, interaction)

class IMoreOptions(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Infraction Issuer Button" ,description="A disabled button that displays the username of the issuer."),
            discord.SelectOption(label="Show Issuer", description="This toggle will make all infractions annonymous."),
            discord.SelectOption(label="Notify on Void", description="Notifys the user when their infraction is voided.")
            

        
            
        ]
        super().__init__(placeholder='More Options', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
 
        

        option_result = await options.find_one({'guild_id': interaction.guild.id})
        if option_result is None:
            await options.insert_one({'guild_id': interaction.guild.id})
        if selected_option == "Infraction Issuer Button":
                view = InfractByButton()
                embed = discord.Embed(title='Infraction Issuer Button', color=discord.Colour.dark_embed())
                embed.set_image(url="https://cdn.discordapp.com/attachments/1119278150086570045/1218941681752080485/image.png?ex=66097ee7&is=65f709e7&hm=f3ca0f7f9706bc4e2f50e1fa33b21ca0005f324abeb6b66b7f8b226b64e15bdd&")
                if option_result:
                    if option_result.get('infractedbybutton', False) is False:
                        view.bybuttontoggle.style = discord.ButtonStyle.red
                        
                    elif option_result.get('infractedbybutton', False) is True:
                        view.bybuttontoggle.style = discord.ButtonStyle.green
                        
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        elif selected_option == 'Show Issuer':
                view = ShowIssuer()
                embed = discord.Embed(title='Show Issuer', description="If you disable this, the infraction will be annonymous which doesn't work with customisation embeds and it removes the embed author so if the `Infraction Issuer Button` is enabled the button will still appear.", color=discord.Colour.dark_embed())
                if option_result:
                    if option_result.get('showissuer', True) is False:
                        view.issuer.style = discord.ButtonStyle.red
                        
                    elif option_result.get('showissuer', True) is True:
                        view.issuer.style = discord.ButtonStyle.green
                        
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)                    

        elif selected_option == 'Notify on Void':
                view = onvoid()
                embed = discord.Embed(title='Notify On Void', description="", color=discord.Colour.dark_embed())
                embed.set_image(url="https://cdn.discordapp.com/attachments/1119278150086570045/1218950005952352286/image.png?ex=660986a8&is=65f711a8&hm=cff17f86c88e52d800d03451cc58a295e5868465cfa1b1262cc318e0d7247058&")
                if option_result:
                    if option_result.get('onvoid', False) is False:
                        view.void.style = discord.ButtonStyle.red
                        
                    elif option_result.get('onvoid', False) is True:
                        view.void.style = discord.ButtonStyle.green
                        
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)    
        

 
            


class InfractByButton(discord.ui.View):    
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Issuer Button Display", style=discord.ButtonStyle.red) 
    async def bybuttontoggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        optionresult = await options.find_one({'guild_id': interaction.guild.id})
        if optionresult.get('infractedbybutton', False) is False:
                self.bybuttontoggle.style = discord.ButtonStyle.green
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'infractedbybutton': True}}, upsert=True)
        else:
                self.bybuttontoggle.style = discord.ButtonStyle.red        
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'infractedbybutton': False}}, upsert=True)
        await interaction.response.edit_message(content="", view=self)        

class ShowIssuer(discord.ui.View):    
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Show Issuer", style=discord.ButtonStyle.green) 
    async def issuer(self, interaction: discord.Interaction, button: discord.ui.Button):
        optionresult = await options.find_one({'guild_id': interaction.guild.id})
        if optionresult.get('showissuer', True) is False:
                self.issuer.style = discord.ButtonStyle.green
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'showissuer': True}}, upsert=True)
        else:
                self.issuer.style = discord.ButtonStyle.red        
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'showissuer': False}}, upsert=True)
        await interaction.response.edit_message(content="", view=self)        

class onvoid(discord.ui.View):    
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Notify on Void", style=discord.ButtonStyle.red) 
    async def void(self, interaction: discord.Interaction, button: discord.ui.Button):
        optionresult = await options.find_one({'guild_id': interaction.guild.id})
        if optionresult.get('onvoid', False) is False:
                self.void.style = discord.ButtonStyle.green
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'onvoid': True}}, upsert=True)
        else:
                self.void.style = discord.ButtonStyle.red        
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'onvoid': False}}, upsert=True)
        await interaction.response.edit_message(content="", view=self)            

class InfractionTypesAction(discord.ui.Select):
    def __init__(self, author, name):
        self.author = author
        self.name = name
        options = [
            discord.SelectOption(label="Send to channel", emoji="<:tag:1162134250414415922>"),
            discord.SelectOption(label="Give Roles", emoji="<:Promotion:1162134864594735315>"),
            discord.SelectOption(label='Remove Roles', emoji="<:Infraction:1162134605885870180>")
        ]
        super().__init__(placeholder='Infraction Type Action', min_values=1, max_values=3, options=options, row=0)
        

    async def callback(self, interaction: discord.Interaction):
        options = self.values
        view = discord.ui.View()
        if 'Send to channel' in options:
            view.add_item(TypeChannel(self.author, self.name, options))  
            await interaction.response.edit_message(view=view)
            return 
        elif 'Give Roles' in options:
            view.add_item(GiveRoles(self.author, self.name, options)) 
            await interaction.response.edit_message(view=view)
            return               
        elif 'Remove Roles' in options:
            view.add_item(
                Removeroles(self.author, self.name, options))   
            await interaction.response.edit_message(view=view)
            return         

class TypeChannel(discord.ui.ChannelSelect):
    def __init__(self, author, name, selected):
        super().__init__(placeholder='Infractions Type Channel', channel_types=[discord.ChannelType.text, discord.ChannelType.news])
        self.author = author
        self.name = name
        self.selected = selected
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                  
        channelid = self.values[0]

        
        filter = {
            'guild_id': interaction.guild.id,
            'name': self.name
        }        


        await infractiontypeactions.update_one(filter, {'$set': {'name': self.name, 'channel': channelid.id}}, upsert=True)



        if 'Give Roles' in self.selected:
                view = discord.ui.View()
                view.add_item(GiveRoles(self.author, self.name, self.selected))
                await interaction.response.edit_message(content=f"{tick} Succesfully set channel, now set the given roles!", view=view)
        elif 'Remove Roles' in self.selected:
                view = discord.ui.View()
                view.add_item(Removeroles(self.author, self.name, self.selected))
                await interaction.response.edit_message(content=f"{tick} Succesfully set channel, now set the removed roles!", view=view)
        else:        
            await interaction.response.edit_message(content=f"{tick} Succesfully setup Infraction type.", view=None)




class GiveRoles(discord.ui.RoleSelect):
    def __init__(self, author, name, selected):
        super().__init__(placeholder='Given Roles', max_values=10)
        self.author = author
        self.name = name
        self.selected = selected
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
        filter = {
            'guild_id': interaction.guild.id,
            'name': self.name
        }
        await infractiontypeactions.update_one(filter, {'$set': {'name': self.name, 'givenroles': selected_role_ids}}, upsert=True)


        if 'Remove Roles' in self.selected:
                view = discord.ui.View()
                view.add_item(Removeroles(self.author, self.name, self.selected))
                await interaction.response.edit_message(content=f"{tick} Succesfully set channel, now set the removed roles!", view=view)   
        else:
            await interaction.response.edit_message(content=f"{tick} Succesfully setup Infraction type.", view=None)
class Removeroles(discord.ui.RoleSelect):
    def __init__(self, author, name, selected):
        super().__init__(placeholder='Removed Roles', max_values=10)
        self.author = author
        self.name = name
        self.selected = selected
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
        filter = {
            'guild_id': interaction.guild.id,
            'name': self.name
        }
        await infractiontypeactions.update_one(filter, {'$set': {'name': self.name, 'removedroles': selected_role_ids}}, upsert=True)


        await interaction.response.edit_message(content=f"{tick} Succesfully setup Infraction type.", view=None)

class InfractionTypes(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Create"),
            discord.SelectOption(label="Delete"),
            discord.SelectOption(label="Edit")
        ]
        super().__init__(placeholder='Infraction Types', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        type_action = self.values[0]

        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)   

        if type_action == 'Create':
            await interaction.response.send_modal(CreateInfractionModal(self.author))
        elif type_action == 'Delete':
            await interaction.response.send_modal(DeleteInfractionModal(self.author))
        elif type_action =='Edit':
             await interaction.response.send_modal(EditInfractionModal(self.author))   


class EditInfractionModal(discord.ui.Modal):
    def __init__(self, author):
        self.author = author
        super().__init__(title="Create Infraction Type")

    type_input = discord.ui.TextInput(
            label='Type',
            placeholder='What is the infraction type?',
            max_length=30,
        )


    async def on_submit(self, interaction: discord.Interaction):
         type = self.type_input.value   
         filterm = {
            'guild_id': interaction.guild.id,
            'types': {'$in': [type]}
         }         
         result = await nfractiontypes.find_one(filterm)
         if result is None:
             return await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, Infraction type not found.", ephemeral=True)
         view = discord.ui.View()
         view.add_item(InfractionTypesAction(self.author, type))
         await interaction.response.send_message(content=f"{tick} **{interaction.user.display_name}**, Editing infraction type. Please select the action you want to take.", view=view, ephemeral=True)
       
         


class CreateInfractionModal(discord.ui.Modal):
    def __init__(self, author):
        self.author = author
        super().__init__(title="Create Infraction Type")

    type_input = discord.ui.TextInput(
            label='Type',
            placeholder='What is the infraction type?',
            max_length=30,
        )


    async def on_submit(self, interaction: discord.Interaction):
        
        type_value = self.type_input.value   
        filterm = {
            'guild_id': interaction.guild.id,
            'types': {'$in': [type_value]}
        }

        types = await nfractiontypes.find_one(filterm)
        infractiontypesresult = await nfractiontypes.find_one({'guild_id': interaction.guild.id})

        infractiontypescount = len(infractiontypesresult['types'])
        premiumresult = await premium.find_one({'guild_id': interaction.guild.id})

        if not premiumresult:
         if infractiontypescount >= 15:
            return await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, You have reached the maximum amount of infraction types (15) but to upgrade you can [**buy premium**](https://patreon.com/astrobirb/membership)!", ephemeral=True)
        if types:
            return await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, Infraction type already exists", ephemeral=True)



        await nfractiontypes.update_one(
    {'guild_id': interaction.guild.id},
    {'$addToSet': {'types': type_value}},
    upsert=True
)
        await refreshembed(self, interaction)
        view = NoThanks()
        
        view.add_item(InfractionTypesAction(self.author, type_value))
        await interaction.response.send_message(content=f"{tick} **{interaction.user.display_name}**, Do you want to add extra stuff to this infraction type?", view=view, ephemeral=True)

class NoThanks(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()

    @discord.ui.button(label="No Thanks", style=discord.ButtonStyle.red, row=1)
    async def no_thanks(self,  interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"{tick} **{interaction.user.display_name}**, No problem!, I've created the infraction type for you!", view=None)

   

class DeleteInfractionModal(discord.ui.Modal):
    def __init__(self, author):
        self.author = author
        super().__init__(title="Delete Infraction Type")

    type_input = discord.ui.TextInput(
            label='Type',
            placeholder='What is the infraction type?',
        )



    async def on_submit(self, interaction: discord.Interaction):
        type_value = self.type_input.value   
        filterm = {
            'guild_id': interaction.guild.id,
            'types': {'$in': [type_value]}
        }

        types = await nfractiontypes.find_one(filterm)
        if types is None:
            return await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, Infraction type not found.", ephemeral=True)
        await infractiontypeactions.delete_one({'guild_id': interaction.guild.id, 'name': type_value})  
        await nfractiontypes.update_one(
    {'guild_id': interaction.guild.id},
    {'$pull': {'types': type_value}},
    upsert=True
)


        await interaction.response.send_message(content=f"{tick} **{interaction.user.display_name}**, Infraction type deleted successfully", ephemeral=True)
        await refreshembed(self, interaction)
async def refreshembed(self, interaction: discord.Interaction):
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
                    infchannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else:    
                 infchannelmsg = channel.mention          

            infractiontypescount = len(infractiontyperesult['types'])
            if infractiontypescount is None:
                infractiontypess = "0"
            premiumresult = await premium.find_one({'guild_id': interaction.guild.id})
            if premiumresult:
                maxamount = "∞"
            else:
                maxamount = "15"                
            embed = discord.Embed(title="<:Infraction:1223063128275943544> Infractions Module",  color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Infractions Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Infraction Channel:** {infchannelmsg}\n{replybottom}**Infraction Types [{infractiontypescount}/{maxamount}]** {infractiontypess}\n\n<:Tip:1223062864793702431> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    
            
            try:
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.")              