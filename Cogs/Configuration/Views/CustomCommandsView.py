import discord
import os
from pymongo import MongoClient
from emojis import *
import validators
MONGO_URL = os.getenv('MONGO_URL')

mongo = MongoClient(MONGO_URL)
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
customcommands = db['Custom Commands']

class CreateCommand(discord.ui.Modal, title='CreateCommand'):
    def __init__(self, author):
        super().__init__()
        self.author = author


    name = discord.ui.TextInput(
        label='Name',
        placeholder='What do you want the name to be?',
        max_length=30
    )




    async def on_submit(self, interaction: discord.Interaction):
        amount = customcommands.count_documents({"guild_id": interaction.guild.id})
        if amount >= 30:
         embed = discord.Embed()
         embed.title = f"{redx} {amount}/30"
         embed.description=f"You have reached the maximum amount of custom commands."
         embed.color = discord.Color.brand_red()
         await interaction.response.edit_message(embed=embed, view=None)

         return
        result = customcommands.find_one({"name": self.name.value})
        embed = interaction.message.embeds[0]
        if result:
         embed = discord.Embed()
         embed.title = f"{redx} That already exists!"
         embed.color = discord.Color.brand_red()
         embed.description=f"Please try again."
         await interaction.response.edit_message(embed=embed, view=None)
         return           
        name = self.name.value
        view = NoEmbeds(self.author, name)
        await interaction.response.edit_message(embed=None,content=None,  view=view)
        customcommands.insert_one({"name": name, "guild_id": interaction.guild.id, "creator": interaction.user.id})


class DeleteCommand(discord.ui.Modal, title='Delete Command'):
    def __init__(self, author):
        super().__init__()
        self.authot = author




    name = discord.ui.TextInput(
        label='Name',
        placeholder='Whats the name of the command?',
        max_length=30
    )




    async def on_submit(self, interaction: discord.Interaction):
       result = customcommands.find_one({"name": self.name.value})
       embed = interaction.message.embeds[0]
       if result is None:
        embed.title = f"{redx} I could not find that."
        embed.color = discord.Color.brand_red()
        await interaction.response.edit_message(embed=embed)
        return
       customcommands.delete_one({"name": self.name.value})
       embed = discord.Embed(description="Succesfully deleted the command.")
       embed.title = f"{greencheck} Command Deleted"
       embed.color = discord.Color.brand_green()
       await interaction.response.edit_message(embed=embed, view=None)

class ButtonURLView(discord.ui.Modal, title='Button URL'):
    def __init__(self, author, names):
        super().__init__()
        self.author = author
        self.names = names






    name = discord.ui.TextInput(
        label='URL',
        placeholder='Whats the url you wanna use? (https://example.com)',
        max_length=2048
    )

    label = discord.ui.TextInput(
        label='Button Name',
        placeholder='What text should be on the button?',
        max_length=80
    )


    async def on_submit(self, interaction: discord.Interaction):
        url = self.name.value
        if not validators.url(url):
            await interaction.response.send_message(f"{no} **{interaction.user.display_name},** that is not a valid website url.", ephemeral=True)
            return
        customcommands.update_one({'name': self.names,'guild_id': interaction.guild.id}, {'$set': {'url': url, 'buttons': 'Link Button', 'button_label': self.label.value}})
        await interaction.response.edit_message(content=f"{tick} **{interaction.user.display_name},** I've set the buttons to URL with the link `{self.name.value}`.")


class ButtonsSelectionView(discord.ui.Select):
    def __init__(self, author, name):
        self.author = author
        self.name = name
        options = [
            discord.SelectOption(label="Voting Buttons"),
            discord.SelectOption(label="Link Button"),
            

        
            
        ]
        super().__init__(placeholder='Buttons Selection', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)   
        if color == 'Voting Buttons':
         customcommands.update_one({'name': self.name,'guild_id': interaction.guild.id}, {'$set': {'buttons': color}})
         await interaction.response.edit_message(content=f"{tick} **{interaction.user.display_name},** I've set the buttons to `{color}`.")
        if color == 'Link Button':
            await interaction.response.send_modal(ButtonURLView(self.author, self.name))

 

class ButtonsSelection(discord.ui.View):
    def __init__(self, author, name):
        super().__init__()
        self.add_item(ButtonsSelectionView(author, name))


        

class ToggleCommands(discord.ui.Select):
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
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'customcommands': True}}, upsert=True)    
            await refreshembed(interaction)  
        if color == 'Disable':    
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'customcommands': False}}, upsert=True)   
            await refreshembed(interaction)   

async def refreshembed(interaction):
            commands = customcommands.find({'guild_id': interaction.guild.id})
            
            amount = customcommands.count_documents({'guild_id': interaction.guild.id})
            embed = discord.Embed(title=f"<:command1:1199456319363633192> Custom Commands ({amount}/30)", description="", color=discord.Color.dark_embed())
            for result in commands:
                embed.add_field(name=f"<:command1:1199456319363633192> {result['name']}", value=f"<:arrow:1166529434493386823> **Created By:** <@{result['creator']}>", inline=False)
            await interaction.message.edit(embed=embed)


class CreateButtons(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Create", emoji=f"{add}"),
            discord.SelectOption(label="Delete", emoji=f"{bin}"),
            

        
            
        ]
        super().__init__(placeholder='Commands', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)  

        if color == 'Create':
            await interaction.response.send_modal(CreateCommand(self.author))

        elif color == 'Delete':
            await interaction.response.send_modal(DeleteCommand(self.author))  


    
class Title(discord.ui.Modal, title='Title'):
    def __init__(self):
        super().__init__()




    Titles = discord.ui.TextInput(
        label='title',
        placeholder='What is the title?',
        required=False,
        max_length=256
    )




    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.title = self.Titles.value
        try:
         await interaction.response.edit_message(embed=embed)
        except discord.HTTPException():
            return await interaction.response.send_message(f"{no} {interaction.user.display_name}, had an error adding the title please try again.", ephemeral=True)


class Description(discord.ui.Modal, title='Description'):
    def __init__(self):
        super().__init__()



    description = discord.ui.TextInput(
        label='Description',
        placeholder='What is the description?',
        style=discord.TextStyle.long,
        max_length=4000,
        required=False
    )




    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.description = self.description.value
        await interaction.response.edit_message(embed=embed)

class Colour(discord.ui.Modal, title='Colour'):
    def __init__(self):
        super().__init__()



    color = discord.ui.TextInput(
        label='Colour',
        placeholder='Do not include the hashtag',
        max_length=6,
    )





    async def on_submit(self, interaction: discord.Interaction):
        color_value = self.color.value
        try:
            color = discord.Color(int(color_value, 16))
        except ValueError:
            await interaction.response.send_message(f" {no} Please provide a valid hex color without the hashtag.", ephemeral=True)
            return
        
        embed = interaction.message.embeds[0]
        embed.color = color
        await interaction.response.edit_message(embed=embed)

class Context(discord.ui.Modal, title='Content'):
    def __init__(self):
        super().__init__()



    color = discord.ui.TextInput(
        label='Content',
        placeholder='What do you want the content to be?',
        
        required=False,
        style=discord.TextStyle.long,
        max_length=2000
    )





    async def on_submit(self, interaction: discord.Interaction):
        color_value = self.color.value
        await interaction.response.edit_message(content=color_value)


class Thumbnail(discord.ui.Modal, title='Thumbnail'):
    def __init__(self):
        super().__init__()



    Thumbnaile = discord.ui.TextInput(
        label='Thumbnail',
        placeholder='Whats the thumbnail URL?',
        required= False,
        max_length=2048
    )




    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        try:
         embed.set_thumbnail(url=self.Thumbnaile.value)
         await interaction.response.edit_message(embed=embed)
        except:
           await interaction.response.send_message(f"{no} Please provide a valid url.", ephemeral=True)
           return
 
class Image(discord.ui.Modal, title='Image'):
    def __init__(self):
        super().__init__()



    Thumbnaile = discord.ui.TextInput(
        label='Image',
        placeholder='Whats the image URL?',
        required=False,
        max_length=2048
    )




    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        try:
         embed.set_image(url=self.Thumbnaile.value)
         await interaction.response.edit_message(embed=embed)
        except:
           await interaction.response.send_message(f"{no} Please provide a valid url.", ephemeral=True)
           return

class Author(discord.ui.Modal, title='Author'):
    def __init__(self):
        super().__init__()

    authortext = discord.ui.TextInput(
        label='Author Name',
        placeholder='Whats the author name?',
        required=False,
        max_length=256
    )

    iconUrl = discord.ui.TextInput(
        label='Icon URL',
        placeholder='Whats the icon URL?',
        required=False,
        max_length=2048
    )




    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        author_name = self.authortext.value
        icon_url = self.iconUrl.value

        if author_name is None:
         author_name = ""


        if icon_url is None and embed.author and embed.author.icon_url is not None:
         embed.set_author(name=author_name, icon_url=embed.author.icon_url)
        else:
         embed.set_author(name=author_name, icon_url=icon_url)

        try:
         await interaction.response.edit_message(embed=embed)
        except:
         await interaction.response.send_message(f"{no} Please provide a valid url or name.", ephemeral=True)
         return

                

     



class NoEmbeds(discord.ui.View):
    def __init__(self, author, name):
        super().__init__()
        self.author = author
        self.name = name


    @discord.ui.button(label='Add Embed', style=discord.ButtonStyle.blurple, emoji="<:Add:1163095623600447558>")
    async def add_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        embed = discord.Embed(title="Untitled Embed", color=discord.Colour.dark_embed())
        view = Embeds(interaction.user, self.name)
        await interaction.response.edit_message(embed=embed, view=view)
     

    @discord.ui.button(label='Context', style=discord.ButtonStyle.blurple, emoji="<:Pen:1126527802255085628>")
    async def context(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        await interaction.response.send_modal(Context())



    @discord.ui.button(label='Buttons', style=discord.ButtonStyle.blurple, emoji="<:Button:1199443313082769498>")
    async def Buttons(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                  
        await interaction.response.send_message(view= ButtonsSelection(self.author, self.name), ephemeral=True)     
         

    @discord.ui.button(label='Variables', style=discord.ButtonStyle.blurple, emoji="<:List:1179470251860185159>")
    async def Var(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)         

        embed = discord.Embed(title="Variables List", description="**{author.name}** = The name of the person who is using the command\n**{author.id}** = The user id who is using the command\n**{author.mention}** = Mention of the user using the command\n**{timestamp}** = Time stamp of when the command was used\n**{guild.name}** = The name of the server\n**{guild.id}** = The id of the server\n**{guild.owner.name}** = The name of the server owner\n**{guild.owner.id}** = The id of the server owner\n**{guild.owner.mention}** = The mention of the server owner", color=discord.Colour.dark_embed())  
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label='Finish', style=discord.ButtonStyle.green, emoji=f"{tick}", row=2)
    async def Finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    


        message = interaction.message
        
        if not message.embeds:
             embed_data = {
            "name": self.name,
            "guild_id": interaction.guild.id,
            "content": message.content

            }        
        else: 
         embed = message.embeds[0]
         color_hex = f"{embed.color.value:06x}"
         embed_data = {
            "title": embed.title,
            "name": self.name,
            "description": embed.description,
            "color": color_hex,
            "author": embed.author.name if embed.author else None,
            "author_icon": embed.author.icon_url if embed.author else None,
            "thumbnail": embed.thumbnail.url if embed.thumbnail else None,
            "image": embed.image.url if embed.image else None,
            "guild_id": interaction.guild.id
            }

       

        customcommands.update_one({"name": self.name, "guild_id": interaction.guild.id}, {"$set": embed_data}, upsert=True)
        embed = discord.Embed()
        embed.title = f"{greencheck} Succesfully Created"
        embed.description = f"Start by using /command run and selecting `{self.name}`"
        embed.color = discord.Colour.brand_green()
        await interaction.response.edit_message(content=None, embed=embed, view=None)

class Embeds(discord.ui.View):
    def __init__(self, author, name):
        super().__init__()     
        self.author = author
        self.name = name

    @discord.ui.button(label='Remove Embed', style=discord.ButtonStyle.blurple, emoji="<:bin:1160543529542635520>")
    async def removeembed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        
        await interaction.response.edit_message(embed=None, view=NoEmbeds(interaction.user, self.name))        

    @discord.ui.button(label='Context', style=discord.ButtonStyle.blurple, emoji="<:Pen:1126527802255085628>")
    async def context(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        await interaction.response.send_modal(Context())



    @discord.ui.button(label='Buttons', style=discord.ButtonStyle.blurple, emoji="<:Button:1199443313082769498>")
    async def Buttons(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                  
        await interaction.response.send_message(view= ButtonsSelection(self.author, self.name), ephemeral=True)     
         

    @discord.ui.button(label='Variables', style=discord.ButtonStyle.blurple, emoji="<:List:1179470251860185159>")
    async def Var(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)         

        embed = discord.Embed(title="Variables List", description="**{author.name}** = The name of the person who is using the command\n**{author.id}** = The user id who is using the command\n**{author.mention}** = Mention of the user using the command\n**{timestamp}** = Time stamp of when the command was used\n**{guild.name}** = The name of the server\n**{guild.id}** = The id of the server\n**{guild.owner.name}** = The name of the server owner\n**{guild.owner.id}** = The id of the server owner\n**{guild.owner.mention}** = The mention of the server owner", color=discord.Colour.dark_embed())  
        await interaction.response.send_message(embed=embed, ephemeral=True)
    @discord.ui.button(label='Title', style=discord.ButtonStyle.grey, emoji="<:abc:1193192444938956800>")
    async def Title(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Title())


    @discord.ui.button(label='Description', style=discord.ButtonStyle.grey, emoji="<:description:1193192044307415040>")
    async def Description(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Description())

    @discord.ui.button(label='Thumbnail', style=discord.ButtonStyle.grey, emoji="<:image:1193191680690630706>")
    async def Thumbnail(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Thumbnail())

    @discord.ui.button(label='Image', style=discord.ButtonStyle.grey, emoji="<:Image:1195058849741295748>")
    async def photo(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Image())

    @discord.ui.button(label='Author', style=discord.ButtonStyle.grey, emoji="<:image:1193191680690630706>")
    async def Author(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Author())

    @discord.ui.button(label='Color', style=discord.ButtonStyle.grey, emoji="<:tag:1162134250414415922>")
    async def Color(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Colour())        

    @discord.ui.button(label='Finish', style=discord.ButtonStyle.green, emoji=f"{tick}", row=2)
    async def Finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    


        message = interaction.message
        if interaction.message.content is None:
            messagecontent = None
        else:
            messagecontent = interaction.message.content

        if not message.embeds:
             embed_data = {
            "name": self.name,
            "embed": False,
            "guild_id": interaction.guild.id,
            "content": messagecontent

            }        
        else: 
         embed = message.embeds[0]
         color_hex = f"{embed.color.value:06x}" if embed.color else None
         embed_data = {
            "title": embed.title,
            "embed": True,
            "name": self.name,
            "description": embed.description,
            "color": color_hex,
            "author": embed.author.name if embed.author else None,
            "author_icon": embed.author.icon_url if embed.author else None,
            "thumbnail": embed.thumbnail.url if embed.thumbnail else None,
            "image": embed.image.url if embed.image else None,
            "guild_id": interaction.guild.id,
            "content": messagecontent
            }

       

        customcommands.update_one({"name": self.name, "guild_id": interaction.guild.id}, {"$set": embed_data}, upsert=True)
        embed = discord.Embed()
        embed.title = f"{greencheck} Succesfully Created"
        embed.description = f"Start by using </command run:1199462063202902077> and selecting `{self.name}`"
        embed.color = discord.Colour.brand_green()
        await interaction.response.edit_message(content=None, embed=embed, view=None)