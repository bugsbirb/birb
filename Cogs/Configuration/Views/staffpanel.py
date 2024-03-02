import discord
import os
from pymongo import MongoClient
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')

mongo = MongoClient(MONGO_URL)
db = mongo['astro']
modules = db['Modules']
Customisation = db['Customisation']
StaffPanelLabel = db['StaffPanel Label']

class StaffCustomise(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Reset To Default"),
            discord.SelectOption(label="Customize"),
            discord.SelectOption(label="Dropdown Label"),
            

        
            
        ]
        super().__init__(placeholder='Panel Customisation', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        

        if color == 'Reset To Default':
            await interaction.response.send_message(content=f"{tick} Reset To Default", ephemeral=True)
            Customisation.delete_one({"name": "Staff Panel", "guild_id": interaction.guild.id})
        elif color == 'Customize':
            view = NoEmbeds( interaction.user)


            
             
            await interaction.response.edit_message(embed=None, view=view)

        elif color == 'Dropdown Label':
            await interaction.response.send_modal(DropdownLabel())    
        


class StaffData(discord.ui.Select):
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
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Staff Database': True}}, upsert=True)    
            await refreshembed(interaction)
        if color == 'Disable':    
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'Staff Database': False}}, upsert=True)    
            await refreshembed(interaction)        


class DropdownLabel(discord.ui.Modal, title='Dropdown Label'):
    def __init__(self):
        super().__init__()




    Titles = discord.ui.TextInput(
        label='Label',
        placeholder='What do you want the dropdown label to be?',
        required=False,
        max_length=20
    )




    async def on_submit(self, interaction: discord.Interaction):
        StaffPanelLabel.update_one({'guild_id': interaction.guild.id},  {'$set': {'label': self.Titles.value}}, upsert=True)
        await interaction.response.send_message(f"{tick} **{interaction.user.display_name}**, set the dropdown label to {self.Titles.value}", ephemeral=True)





class Title(discord.ui.Modal, title='Title'):
    def __init__(self):
        super().__init__()




    Titles = discord.ui.TextInput(
        label='title',
        placeholder='What is the title?',
        required=False
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
        max_length=2000,
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
        required= False
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
        required=False
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
        required=False
    )

    iconUrl = discord.ui.TextInput(
        label='Icon URL',
        placeholder='Whats the icon URL?',
        required=False
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
    def __init__(self, author):
        super().__init__()
        self.author = author



    @discord.ui.button(label='Add Embed', style=discord.ButtonStyle.blurple, emoji="<:Add:1163095623600447558>")
    async def add_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        embed = discord.Embed(title="Untitled Embed", color=discord.Colour.dark_embed())
        view = Embeds(interaction.user)
        await interaction.response.edit_message(embed=embed, view=view)
     

    @discord.ui.button(label='Content', style=discord.ButtonStyle.blurple, emoji="<:Pen:1126527802255085628>")
    async def context(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        await interaction.response.send_modal(Context())



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
            "guild_id": interaction.guild.id,
            "content": message.content

            }        
        else: 
         embed = message.embeds[0]
         color_hex = f"{embed.color.value:06x}"
         embed_data = {
            "title": embed.title,
            "description": embed.description,
            "color": color_hex,
            "author": embed.author.name if embed.author else None,
            "author_icon": embed.author.icon_url if embed.author else None,
            'embed': True,
            "thumbnail": embed.thumbnail.url if embed.thumbnail else None,
            "image": embed.image.url if embed.image else None,
            "guild_id": interaction.guild.id
            }

       

        Customisation.update_one({"name": "Staff Panel", "guild_id": interaction.guild.id}, {"$set": embed_data}, upsert=True)
        embed = discord.Embed()
        embed.title = f"{greencheck} Succesfully Updated"
        embed.description = f"Start by using /staffpanel"
        embed.color = discord.Colour.brand_green()
        await interaction.response.edit_message(content=None, embed=embed, view=None)

class Embeds(discord.ui.View):
    def __init__(self, author):
        super().__init__()    
        self.author = author 


    @discord.ui.button(label='Remove Embed', style=discord.ButtonStyle.blurple, emoji="<:bin:1160543529542635520>")
    async def removeembed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        
        await interaction.response.edit_message(embed=None, view=NoEmbeds(interaction.user))        

    @discord.ui.button(label='Content', style=discord.ButtonStyle.blurple, emoji="<:Pen:1126527802255085628>")
    async def context(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        await interaction.response.send_modal(Context())


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
        
        if not message.embeds:
             embed_data = {
            "name": "Staff Panel",
            "guild_id": interaction.guild.id,
            "content": message.content

            }        
        else: 
         embed = message.embeds[0]
         color_hex = f"{embed.color.value:06x}"
         embed_data = {
            "title": embed.title,
            "description": embed.description,
            "color": color_hex,
            'embed': True,
            'name': "Staff Panel",
            "author": embed.author.name if embed.author else None,
            "author_icon": embed.author.icon_url if embed.author else None,
            "thumbnail": embed.thumbnail.url if embed.thumbnail else None,
            "image": embed.image.url if embed.image else None,
            "guild_id": interaction.guild.id
            }

       

        Customisation.update_one({"name": "Staff Panel", "guild_id": interaction.guild.id}, {"$set": embed_data}, upsert=True)
        embed = discord.Embed()
        embed.title = f"{greencheck} Succesfully Updated"
        embed.description = f"Start by using /staff panel"
        embed.color = discord.Colour.brand_green()
        await interaction.response.edit_message(content=None, embed=embed, view=None)


async def refreshembed(interaction):
            moduleddata = modules.find_one({'guild_id': interaction.guild.id})
            if moduleddata:
                modulemsg = moduleddata.get('Staff Database', 'False')     
            embed = discord.Embed(title="<:staffdb:1206253848298127370> Staff Database & Panel", description=f"**Enabled:** {modulemsg}\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon) 
            try:
             await interaction.message.edit(embed=embed)
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.") 
             