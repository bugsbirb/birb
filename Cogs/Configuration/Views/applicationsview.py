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
ApplicationsSubChannel = db['Applications Submissions']
ApplicationsRolesDB = db['Applications Roles']
application = db['applications']
options = db['module options']
premium = db['premium']



class AMoreOptions(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Application Roles", description="Roles given after being accepted."),
            discord.SelectOption(label="Application Results Channel", description="Where application results are sent."),
            discord.SelectOption(label="Deny/Accept Buttons", description="Once a application is submitted there will be buttons to accept or deny."),
            discord.SelectOption(label="Thread Discussion", description="Automaticly creates a thread attached to application submissions.")
            

        
            
        ]
        super().__init__(placeholder='More Options', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        if color == 'Application Roles':
            view = discord.ui.View()
            view.add_item(ApplicationsRoles(self.author))
            await interaction.response.send_message(view=view, ephemeral=True)
        elif color == ('Application Results Channel'):
            view = discord.ui.View()
            view.add_item(ApplicationChannel(self.author))
            await interaction.response.send_message(view=view, ephemeral=True)
        elif color == ('Deny/Accept Buttons'):
            view = AccepButtons()
            option_result = await options.find_one({'guild_id': interaction.guild.id})
            if option_result:
                    if option_result.get('acceptbuttons', False) is False:
                        view.AcceptButtons.style = discord.ButtonStyle.red
                        
                    elif option_result.get('acceptbuttons', False) is True:
                        view.AcceptButtons.style = discord.ButtonStyle.green            
            await interaction.response.send_message(view=view, ephemeral=True)
        elif color == ('Thread Discussion'):
            view = ResultThread()
            option_result = await options.find_one({'guild_id': interaction.guild.id})
            if option_result:
                    if option_result.get('threaddiscussion', False) is False:
                        view.AcceptButtons.style = discord.ButtonStyle.red
                        
                    elif option_result.get('threaddiscussion', False) is True:
                        view.AcceptButtons.style = discord.ButtonStyle.green            
            await interaction.response.send_message(view=view, ephemeral=True)
            
class RequiredRoles(discord.ui.RoleSelect):
    def __init__(self, author, name):
        super().__init__(placeholder='Required Roles', max_values=10)
        self.author = author
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
  
        data = {
            'guild_id': interaction.guild.id,
            'required': selected_role_ids
        }

        await application.update_one({'guild_id': interaction.guild.id, 'name': self.name}, {'$set': data}, upsert=True)
        await interaction.response.edit_message(content=f"{tick} Set required roles.", view=None) 

class AcceptedRoles(discord.ui.RoleSelect):
    def __init__(self, author, name):
        super().__init__(placeholder='Accepted Roles', max_values=10)
        self.author = author
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
  
        data = {
            'guild_id': interaction.guild.id,
            'Accepted': selected_role_ids
        }

        await application.update_one({'guild_id': interaction.guild.id, 'name': self.name}, {'$set': data}, upsert=True)
        await interaction.response.edit_message(content=f"{tick} Set accepted roles.", view=None) 
            
class AccepButtons(discord.ui.View):    
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Accept/Deny Buttons", style=discord.ButtonStyle.green) 
    async def AcceptButtons(self, interaction: discord.Interaction, button: discord.ui.Button):
        optionresult = await options.find_one({'guild_id': interaction.guild.id})
        if optionresult.get('acceptbuttons', False) is False:
                self.AcceptButtons.style = discord.ButtonStyle.green
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'acceptbuttons': True}}, upsert=True)
        else:
                self.AcceptButtons.style = discord.ButtonStyle.red        
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'acceptbuttons': False}}, upsert=True)
        await interaction.response.edit_message(content="", view=self)  

class ResultThread(discord.ui.View):    
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Application Thread Discussion", style=discord.ButtonStyle.green) 
    async def AcceptButtons(self, interaction: discord.Interaction, button: discord.ui.Button):
        optionresult = await options.find_one({'guild_id': interaction.guild.id})
        if optionresult.get('threaddiscussion', False) is False:
                self.AcceptButtons.style = discord.ButtonStyle.green
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'threaddiscussion': True}}, upsert=True)
        else:
                self.AcceptButtons.style = discord.ButtonStyle.red        
                await options.update_one({'guild_id': interaction.guild.id}, {'$set': {'threaddiscussion': False}}, upsert=True)
        await interaction.response.edit_message(content="", view=self)  

class ToggleApplications(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Enabled"),
            discord.SelectOption(label="Disabled"),
            

        
            
        ]
        super().__init__(placeholder='Module Toggle', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        if color == 'Enabled':    
            await interaction.response.send_message(content=f"{tick} Enabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Applications': True}}, upsert=True) 
            await refreshembed(interaction)   

        if color == 'Disabled':  
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Applications': False}}, upsert=True)    
            await refreshembed(interaction)        

class ApplicationSubmissions(discord.ui.ChannelSelect):
    def __init__(self, author, channels):
        super().__init__(placeholder='Application Submissions Channel',  channel_types=[discord.ChannelType.text, discord.ChannelType.news], default_values=channels)
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
            existing_record = await ApplicationsSubChannel.find_one(filter)

            if existing_record:
                await ApplicationsSubChannel.update_one(filter, {'$set': data})
            else:
                await ApplicationsSubChannel.insert_one(data)

            await interaction.response.edit_message(content=None)
            await refreshembed(interaction)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")         

class ApplicationChannel(discord.ui.ChannelSelect):
    def __init__(self, author):
        super().__init__(placeholder='Application Results Channel',  channel_types=[discord.ChannelType.text, discord.ChannelType.news])
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
            existing_record = await ApplicationsChannel.find_one(filter)

            if existing_record:
                await ApplicationsChannel.update_one(filter, {'$set': data})
            else:
                await ApplicationsChannel.insert_one(data)

            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")            


class ApplicationsRoles(discord.ui.RoleSelect):
    def __init__(self, author):
        super().__init__(placeholder='Passed Application Roles', max_values=20)
        self.author = author
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
  
        data = {
            'guild_id': interaction.guild.id,
            'applicationroles': selected_role_ids
        }


        await ApplicationsRolesDB.update_one({'guild_id': interaction.guild.id}, {'$set': data}, upsert=True)
        await interaction.response.edit_message(content=None)
        print(f"Select Application Roles: {selected_role_ids}")

class ApplicationCreator(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Create"),
            discord.SelectOption(label="Edit"),
            discord.SelectOption(label="Delete")
            

        ]
        super().__init__(placeholder='Application Builder', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
       
        option = self.values[0]
        if option == 'Create':
            await interaction.response.send_modal(createapp(author=self.author))
        elif option == 'Delete':
            await interaction.response.send_modal(deleapp(author=self.author))
        elif option == 'Edit':
            await interaction.response.send_modal(editapp(author=self.author))



class createapp(discord.ui.Modal):
    def __init__(self, author):
        super().__init__(title="Create Application", timeout=None)
        self.author = author

    name = discord.ui.TextInput(
        label='Name',
        placeholder='What\'s the name of this application?'
    )

    async def on_submit(self, interaction: discord.Interaction):
        result = await application.find_one({'guild_id': interaction.guild.id, 'name': self.name.value})

        if result:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name},** This application already exists!", ephemeral=True)
            return
        results = await application.find({'guild_id': interaction.guild.id}).to_list(length=None)
        premiumresult = await premium.find_one({"guild_id": interaction.guild.id})
        if not premiumresult:        
         if len(results) >= 3:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name},** You can only have 3 applications!\nYou can upgrade your plan to have more applications", ephemeral=True, view=PRemium())
            return
            

        await application.insert_one({'guild_id': interaction.guild.id, 'name': self.name.value, 'saved': False})
        view = SectionButtons(author=self.author, name=self.name.value)
        embed = discord.Embed(title="Application Builder", description="No added sections...", color=discord.Colour.dark_embed())
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.display_avatar
        ) 
        await interaction.response.edit_message(embed=embed, view=view)

class deleapp(discord.ui.Modal):
    def __init__(self, author):
        super().__init__(title="Delete Application")
        self.author = author

    name = discord.ui.TextInput(
        label='Name',
        placeholder='What\'s the name of this application?'
    )

    async def on_submit(self, interaction: discord.Interaction):
        applicationresult = await application.find_one({'guild_id': interaction.guild.id, 'name': self.name.value})
        if applicationresult is None:
            await interaction.response.send_message(f"{no} I couldn't find the application specified.", ephemeral=True)
            return

        await application.delete_one({'guild_id': interaction.guild.id, 'name': self.name.value})
        await interaction.response.send_message(f"{no} Application deleted!", ephemeral=True)

class editapp(discord.ui.Modal):
    def __init__(self, author):
        super().__init__(title="Edit Application", timeout=None)
        self.author = author

    name = discord.ui.TextInput(
        label='Name',
        placeholder='What\'s the name of this application?'
    )

    async def on_submit(self, interaction: discord.Interaction):
        applicationresult = await application.find_one({'guild_id': interaction.guild.id, 'name': self.name.value})
        if applicationresult is None:
            await interaction.response.send_message(f"{no} I couldn't find the application specified.", ephemeral=True)
            return
        view = SectionButtons(author=self.author, name=self.name.value)
        embed = discord.Embed(title="Application Builder", description="", color=discord.Colour.dark_embed())
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.display_avatar
        )         
        
        sections_found = False
        
        if applicationresult:
            for i in range(1, 6):
                section_name = f'section{i}'
                if applicationresult.get(section_name):
                    section = applicationresult.get(section_name)
                    embed.add_field(
                        name=f"Section {i}",
                        value=f">>> **Question 1**: {section.get('question1')}\n"
                            f"**Question 2**: {section.get('question2')}\n"
                            f"**Question 3**: {section.get('question3')}\n"
                            f"**Question 4**: {section.get('question4')}\n"
                            f"**Question 5**: {section.get('question5')}",
                        inline=False
                    )         
        
        
        if applicationresult.get('section1'):
            view.section2.disabled = False
            view.save.disabled = False
        elif applicationresult.get('section2'):
            view.section3.disabled = False
            view.save.disabled = False            
        elif applicationresult.get('section3'):
            view.section4.disabled = False
            view.save.disabled = False            
        elif applicationresult.get('section4'):
            view.section5.disabled = False    
            view.save.disabled = False
        else:  
              embed.description = "No sections found for this application."



        await interaction.response.edit_message(embed=embed, view=view)

class SectionButtons(discord.ui.View):
    def __init__(self, author, name):
        super().__init__(timeout=None)
        self.author = author
        self.name = name
    
    @discord.ui.button(label="Section 1", style=discord.ButtonStyle.primary, custom_id="section1")
    async def section1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)  
        await interaction.response.send_modal(Section1(author=self.author, name=self.name))

    @discord.ui.button(label="Section 2", style=discord.ButtonStyle.primary, custom_id="section2", disabled=True)
    async def section2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          
        await interaction.response.send_modal(Section2(author=self.author, name=self.name))

    @discord.ui.button(label="Section 3", style=discord.ButtonStyle.primary, custom_id="section3", disabled=True)
    async def section3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          
        await interaction.response.send_modal(Section3(author=self.author, name=self.name))

    @discord.ui.button(label="Section 4", style=discord.ButtonStyle.primary, custom_id="section4", disabled=True)
    async def section4(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          
        await interaction.response.send_modal(Section4(author=self.author, name=self.name))

    @discord.ui.button(label="Section 5", style=discord.ButtonStyle.primary, custom_id="section5", disabled=True)
    async def section5(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          
        await interaction.response.send_modal(Section5(author=self.author, name=self.name))

    @discord.ui.button(style=discord.ButtonStyle.gray, label="Required Roles", emoji="<:Role:1162074735803387944>")
    async def role(self, interaction: discord.Interaction, button:discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)         
        view = discord.ui.View()
        view.add_item(RequiredRoles(self.author, self.name))
        await interaction.response.send_message(view=view, ephemeral=True)
    
    @discord.ui.button(style=discord.ButtonStyle.gray, label="Accepted Roles", emoji="<:Role:1162074735803387944>")
    async def acceptedroles(self, interaction: discord.Interaction, button:discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)  
        view = discord.ui.View()
        view.add_item(AcceptedRoles(self.author, self.name))
        await interaction.response.send_message(view=view, ephemeral=True)


    @discord.ui.button(style=discord.ButtonStyle.success, emoji="<:Save:1223293419678470245>", custom_id="save", disabled=True)
    async def save(self, interaction: discord.Interaction, button:discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          
        await application.update_one({'guild_id': interaction.guild.id, 'name': self.name}, {'$set': {'saved': True}})
        embed = discord.Embed(color=discord.Color.brand_green())
        embed.title =f"{greencheck} Succesfully Saved"
        embed.description = "Application Successfully saved!"
        await interaction.response.edit_message(
            embed=embed,
            view=None
        )



class Section1(discord.ui.Modal):
    def __init__(self, author, name):
        super().__init__(title="Section 1", timeout=None)
        self.author = author
        self.name = name

    question1 = discord.ui.TextInput(
        label='Question 1',
        placeholder='',
        max_length=45
    )

    question2 = discord.ui.TextInput(
        label='Question 2',
        placeholder='',
        max_length=45
    )

    question3 = discord.ui.TextInput(
        label='Question 3',
        placeholder='',
        max_length=45
    )

    question4 = discord.ui.TextInput(
        label='Question 4',
        placeholder='',
        max_length=45
    )

    question5 = discord.ui.TextInput(
        label='Question 5',
        placeholder='',
        max_length=45
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        await application.update_one(
            {'guild_id': interaction.guild.id, 'name': self.name},
            {'$set': {'section1': {'question1': self.question1.value,
                                   'question2': self.question2.value,
                                   'question3': self.question3.value,
                                   'question4': self.question4.value,
                                   'question5': self.question5.value}}}
        )
        embed.description = None
        
        
        view = SectionButtons(self.author, self.name)
        view.section2.disabled = False
        view.save.disabled = False
        embed.clear_fields()

        
        applicationresult = await application.find_one({'guild_id': interaction.guild.id, 'name': self.name})

        if applicationresult:
            if applicationresult.get('section1'):
                view.section2.disabled = False
                view.save.disabled = False
            if applicationresult.get('section2'):
                view.section3.disabled = False
                view.save.disabled = False            
            if applicationresult.get('section3'):
                view.section4.disabled = False
                view.save.disabled = False            
            if applicationresult.get('section4'):
                view.section5.disabled = False    
                view.save.disabled = False            
            for i in range(1, 6):
                section_name = f'section{i}'
                if applicationresult.get(section_name):
                    section = applicationresult.get(section_name)
                    embed.add_field(
                        name=f"Section {i}",
                        value=f">>> **Question 1**: {section.get('question1')}\n"
                            f"**Question 2**: {section.get('question2')}\n"
                            f"**Question 3**: {section.get('question3')}\n"
                            f"**Question 4**: {section.get('question4')}\n"
                            f"**Question 5**: {section.get('question5')}",
                        inline=False
                    )                                                               
        await interaction.response.edit_message(embed=embed, view=view, content=None)
        
class Section2(discord.ui.Modal):
    def __init__(self, author, name):
        super().__init__(title="Section 2", timeout=None)
        self.author = author
        self.name = name

    question1 = discord.ui.TextInput(
        label='Question 1',
        placeholder='',
        max_length=45
    )

    question2 = discord.ui.TextInput(
        label='Question 2',
        placeholder='',
        max_length=45
    )

    question3 = discord.ui.TextInput(
        label='Question 3',
        placeholder='',
        max_length=45
    )

    question4 = discord.ui.TextInput(
        label='Question 4',
        placeholder='',
        max_length=45
    )

    question5 = discord.ui.TextInput(
        label='Question 5',
        placeholder='',
        max_length=45
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        await application.update_one(
            {'guild_id': interaction.guild.id, 'name': self.name},
            {'$set': {'section2': {'question1': self.question1.value,
                                   'question2': self.question2.value,
                                   'question3': self.question3.value,
                                   'question4': self.question4.value,
                                   'question5': self.question5.value}}}
        )
        embed.description = None
        
        view = SectionButtons(self.author, self.name)
        view.section2.disabled = False
        view.save.disabled = False
        embed.clear_fields()
        
        applicationresult = await application.find_one({'guild_id': interaction.guild.id, 'name': self.name})
        if applicationresult:
            if applicationresult.get('section1'):
                view.section2.disabled = False
                view.save.disabled = False
            if applicationresult.get('section2'):
                view.section3.disabled = False
                view.save.disabled = False            
            if applicationresult.get('section3'):
                view.section4.disabled = False
                view.save.disabled = False            
            if applicationresult.get('section4'):
                view.section5.disabled = False    
                view.save.disabled = False            
            for i in range(1, 6):
                section_name = f'section{i}'
                if applicationresult.get(section_name):
                    section = applicationresult.get(section_name)
                    embed.add_field(
                        name=f"Section {i}",
                        value=f">>> **Question 1**: {section.get('question1')}\n"
                            f"**Question 2**: {section.get('question2')}\n"
                            f"**Question 3**: {section.get('question3')}\n"
                            f"**Question 4**: {section.get('question4')}\n"
                            f"**Question 5**: {section.get('question5')}",
                        inline=False
                    )                                                                    
        await interaction.response.edit_message(embed=embed, view=view, content=None)        

class Section3(discord.ui.Modal):
    def __init__(self, author, name):
        super().__init__(title="Section 3", timeout=None)
        self.author = author
        self.name = name

    question1 = discord.ui.TextInput(
        label='Question 1',
        placeholder='',
        max_length=45
    )

    question2 = discord.ui.TextInput(
        label='Question 2',
        placeholder='',
        max_length=45
    )

    question3 = discord.ui.TextInput(
        label='Question 3',
        placeholder='',
        max_length=45
    )

    question4 = discord.ui.TextInput(
        label='Question 4',
        placeholder='',
        max_length=45
    )

    question5 = discord.ui.TextInput(
        label='Question 5',
        placeholder='',
        max_length=45
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        await application.update_one(
            {'guild_id': interaction.guild.id, 'name': self.name},
            {'$set': {'section3': {'question1': self.question1.value,
                                   'question2': self.question2.value,
                                   'question3': self.question3.value,
                                   'question4': self.question4.value,
                                   'question5': self.question5.value}}}
        )
        embed.description = None
        view = SectionButtons(self.author, self.name)
        view.section2.disabled = False
        view.save.disabled = False
        embed.clear_fields()

        applicationresult = await application.find_one({'guild_id': interaction.guild.id, 'name': self.name})
        if applicationresult:
            if applicationresult.get('section1'):
                view.section2.disabled = False
                view.save.disabled = False
            if applicationresult.get('section2'):
                view.section3.disabled = False
                view.save.disabled = False            
            if applicationresult.get('section3'):
                view.section4.disabled = False
                view.save.disabled = False            
            if applicationresult.get('section4'):
                view.section5.disabled = False    
                view.save.disabled = False            
            for i in range(1, 6):
                section_name = f'section{i}'
                if applicationresult.get(section_name):
                    section = applicationresult.get(section_name)
                    embed.add_field(
                        name=f"Section {i}",
                        value=f">>> **Question 1**: {section.get('question1')}\n"
                            f"**Question 2**: {section.get('question2')}\n"
                            f"**Question 3**: {section.get('question3')}\n"
                            f"**Question 4**: {section.get('question4')}\n"
                            f"**Question 5**: {section.get('question5')}",
                        inline=False
                    )                                                            
        await interaction.response.edit_message(embed=embed, view=view, content=None)      

class Section4(discord.ui.Modal):
    def __init__(self, author, name):
        super().__init__(title="Section 4", timeout=None)
        self.author = author
        self.name = name

    question1 = discord.ui.TextInput(
        label='Question 1',
        placeholder='',
        max_length=45
    )

    question2 = discord.ui.TextInput(
        label='Question 2',
        placeholder='',
        max_length=45
    )

    question3 = discord.ui.TextInput(
        label='Question 3',
        placeholder='',
        max_length=45
    )

    question4 = discord.ui.TextInput(
        label='Question 4',
        placeholder='',
        max_length=45
    )

    question5 = discord.ui.TextInput(
        label='Question 5',
        placeholder='',
        max_length=45
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        await application.update_one(
            {'guild_id': interaction.guild.id, 'name': self.name},
            {'$set': {'section4': {'question1': self.question1.value,
                                   'question2': self.question2.value,
                                   'question3': self.question3.value,
                                   'question4': self.question4.value,
                                   'question5': self.question5.value}}}
        )
        embed.description = None
        
        view = SectionButtons(self.author, self.name)
        view.section2.disabled = False
        view.save.disabled = False
        embed.clear_fields()

        applicationresult = await application.find_one({'guild_id': interaction.guild.id, 'name': self.name})
        if applicationresult:
            if applicationresult.get('section1'):
                view.section2.disabled = False
                view.save.disabled = False
            if applicationresult.get('section2'):
                view.section3.disabled = False
                view.save.disabled = False            
            if applicationresult.get('section3'):
                view.section4.disabled = False
                view.save.disabled = False            
            if applicationresult.get('section4'):
                view.section5.disabled = False    
                view.save.disabled = False            
            for i in range(1, 6):
                section_name = f'section{i}'
                if applicationresult.get(section_name):
                    section = applicationresult.get(section_name)
                    embed.add_field(
                        name=f"Section {i}",
                        value=f">>> **Question 1**: {section.get('question1')}\n"
                            f"**Question 2**: {section.get('question2')}\n"
                            f"**Question 3**: {section.get('question3')}\n"
                            f"**Question 4**: {section.get('question4')}\n"
                            f"**Question 5**: {section.get('question5')}",
                        inline=False
                    )                                                      
        await interaction.response.edit_message(embed=embed, view=view, content=None)

class Section5(discord.ui.Modal):
    def __init__(self, author, name):
        super().__init__(title="Section 5")
        self.author = author
        self.name = name

    question1 = discord.ui.TextInput(
        label='Question 1',
        placeholder='',
        max_length=45
    )

    question2 = discord.ui.TextInput(
        label='Question 2',
        placeholder='',
        max_length=45
    )

    question3 = discord.ui.TextInput(
        label='Question 3',
        placeholder='',
        max_length=45
    )

    question4 = discord.ui.TextInput(
        label='Question 4',
        placeholder='',
        max_length=45
    )

    question5 = discord.ui.TextInput(
        label='Question 5',
        placeholder='',
        max_length=45
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        await application.update_one(
            {'guild_id': interaction.guild.id, 'name': self.name},
            {'$set': {'section5': {'question1': self.question1.value,
                                   'question2': self.question2.value,
                                   'question3': self.question3.value,
                                   'question4': self.question4.value,
                                   'question5': self.question5.value}}}
        )
        embed.description = None
        embed.add_field(name="Section 5", value=f">>> **Question 21**: {self.question1.value}\n**Question 22**: {self.question2.value}\n**Question 23**: {self.question3.value}\n**Question 24**: {self.question4.value}\n**Question 25**: {self.question5.value}", inline=False)
        view = SectionButtons(self.author, self.name)
        view.section2.disabled = False
        view.save.disabled = False
        embed.clear_fields()

        applicationresult = await application.find_one({'guild_id': interaction.guild.id, 'name': self.name})
        if applicationresult:
            for i in range(1, 6):
                section_name = f'section{i}'
                if applicationresult.get(section_name):
                    section = applicationresult.get(section_name)
                    embed.add_field(
                        name=f"Section {i}",
                        value=f">>> **Question 1**: {section.get('question1')}\n"
                            f"**Question 2**: {section.get('question2')}\n"
                            f"**Question 3**: {section.get('question3')}\n"
                            f"**Question 4**: {section.get('question4')}\n"
                            f"**Question 5**: {section.get('question5')}",
                        inline=False
                    )                                                     
        await interaction.response.edit_message(embed=embed, view=view, content=None)  

async def refreshembed(interaction: discord.Interaction):


            applicationchannelresult = await ApplicationsChannel.find_one({'guild_id': interaction.guild.id})
            submissionchannelresult = await ApplicationsSubChannel.find_one({'guild_id': interaction.guild.id})

            staffroleresult = await ApplicationsRolesDB.find_one({'guild_id': interaction.guild.id})
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})
            applications = await application.find({'guild_id': interaction.guild.id}).to_list(length=None)


            approlemsg = "Not Configured"
            subchannelmsg = "Not Configured"
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
                    approlemsg = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
                else:
                    approlemsg = ", ".join(staff_roles_mentions)

            if submissionchannelresult:
                channelid = submissionchannelresult['channel_id']
                subchannelmsg = f"<#{channelid}>"

            if applicationchannelresult:
                channelid = applicationchannelresult['channel_id']
                channel = interaction.guild.get_channel(channelid)
                if channel is None:
                    appchannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                else:
                    appchannelmsg = channel.mention
            premiumresult = await premium.find_one({'guild_id': interaction.guild.id})
            if premiumresult:
                premiummsg = "∞"
            else:
                premiummsg = 3


            embed = discord.Embed(title="<:Application:1224722901328986183> Applications Module",
                                   description=f"",
                                   color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Applications Configuration",
                            value=f"{replytop}**Enabled:** {modulemsg}\n{replymiddle}**Submission Channel:** {subchannelmsg}\n{replymiddle}**Results Channel:** {appchannelmsg}\n{replymiddle}**Application Roles:** {approlemsg}\n{replybottom}**Applications:** {len(applications)}/{premiummsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)",
                            inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            

            try:
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.") 
class PRemium(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="Premium", emoji="<:Tip:1167083259444875264>",style=discord.ButtonStyle.link, url="https://patreon.com/astrobirb/membership/membership"))
