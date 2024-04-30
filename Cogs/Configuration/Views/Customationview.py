import discord
import os
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
Customisation = db['Customisation']
modules = db['Modules']



class ResetEmbeds(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Promotions"),
            discord.SelectOption(label="Infractions"),
            

        
            
        ]
        super().__init__(placeholder='Reset To Default', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            
        if color == "Promotions":
             result = Customisation.find_one({"guild_id": interaction.guild.id, "type": "Promotions"})
             if result is None:
                 await interaction.response.send_message(f"{tick} There are no embeds to reset.", ephemeral=True)
                 return             
             await Customisation.delete_one({"guild_id": interaction.guild.id, "type": "Promotions"})
             await interaction.response.send_message(f"{tick} **{interaction.user.display_name}**, promotions embed have been reset.", ephemeral=True)

        if color == "Infractions":
             result = Customisation.find_one({"guild_id": interaction.guild.id, "type": "Infractions"})
             if result is None:
                 await interaction.response.send_message(f"{tick} There are no embeds to reset.", ephemeral=True)
                 return
             await Customisation.delete_one({"guild_id": interaction.guild.id, "type": "Infractions"})
             await interaction.response.send_message(f"{tick} **{interaction.user.display_name}**, infractions embed have been reset.", ephemeral=True)
 
            

class CustomEmbeds(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Promotions"),
            discord.SelectOption(label="Infractions"),
            

        
            
        ]
        super().__init__(placeholder='Embeds', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)   
        result = await Customisation.find_one({"guild_id": interaction.guild.id, "type": color})
        if result:
            view = Infraction(interaction.user, color)
            
            title = result.get("title", "Title or description required")
            description = result.get("description", None)
            embed_thumbnail = result.get("thumbnail", None)

            embed = discord.Embed(title=title, description=description, color=discord.Color.dark_embed())

            

            if embed_thumbnail == "{staff.avatar}":
                embed_thumbnail = interaction.user.display_avatar.url

            authoricon = result.get("authoricon", None)
            if authoricon == "None":
                authoricon = None

            embed_author = result.get("embed_author", "")

            if embed_author:
                embed.set_author(name=embed_author, icon_url=authoricon)

            if embed_thumbnail:
                embed.set_thumbnail(url=embed_thumbnail)

            image = result.get("image", None)
            if image:
                embed.set_image(url=image)

            view = Infraction(interaction.user, color) 

            await interaction.response.edit_message(embed=embed, view=view)

            return


        if color == "Promotions":
         embed = discord.Embed(title="Staff Promotion", color=0x2b2d31, description="* **User:** {staff.mention}\n* **Updated Rank:** {newrank}\n* **Reason:** {reason}")
         embed.set_author(name="Signed, {author.name}", icon_url=interaction.user.display_avatar)
         embed.set_thumbnail(url=interaction.user.display_avatar)
         view = Infraction(interaction.user, color)
         await interaction.response.edit_message(embed=embed, view=view)
         embed = discord.Embed(title="Embed Variables", description="**Infractions**\n**Author Name:** {author.name}\n**Staff Name:** {staff}\n**Notes:** {notes}\n**Action:** {action}\n**Reason:** {reason}\n\n**Promotions**\n**Author Name:** {author.name}\n**Staff Name:** {staff}\n**New Rank:** {newrank}", color=discord.Color.dark_embed())
         await interaction.followup.send(embed=embed, ephemeral=True)
        if color == "Infractions":
         embed = discord.Embed(title="Staff Consequences & Discipline", description="* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
         embed.set_thumbnail(url=interaction.user.display_avatar)
         embed.set_author(name="Signed, {author.name}", icon_url=interaction.user.display_avatar)
         embed.set_footer(text="Infraction ID | Test")
         view = Infraction(interaction.user, color)
         await interaction.response.edit_message(embed=embed, view=view)
         embed = discord.Embed(title="Embed Variables", description="**Infractions**\n**Author Name:** {author.name}\n**Staff Name:** {staff}\n**Notes:** {notes}\n**Action:** {action}\n**Reason:** {reason}\n\n**Promotions**\n**Author Name:** {author.name}\n**Staff Name:** {staff}\n**New Rank:** {newrank}\n**Expiration:** {expiration}", color=discord.Color.dark_embed())
         await interaction.followup.send(embed=embed, ephemeral=True)


         

class Title(discord.ui.Modal, title='Title'):
    def __init__(self, default):
        super().__init__()




        self.Titles = discord.ui.TextInput(
            label='title',
            placeholder='What is the title?',
            max_length=256,
            default=default
        )
        self.add_item(self.Titles)






    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.title = self.Titles.value
        await interaction.response.edit_message(embed=embed)


class Description(discord.ui.Modal, title='Description'):
    def __init__(self, default):
        super().__init__()



        self.description = discord.ui.TextInput(
            label='Description',
            placeholder='What is the description?',
            style=discord.TextStyle.long,
            max_length=4000,
            default=default
            
        )
        self.add_item(self.description)





    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.description = self.description.value
        await interaction.response.edit_message(embed=embed)

class Colour(discord.ui.Modal, title='Colour'):
    def __init__(self, default):
        super().__init__()



        self.color = discord.ui.TextInput(
            label='Colour',
            placeholder='Do not include the hashtag',
            max_length=6,
            default=default
        )
        self.add_item(self.color)









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



class Thumbnail(discord.ui.Modal, title='Thumbnail'):
    def __init__(self, default):
        super().__init__()



        self.Thumbnaile = discord.ui.TextInput(
            label='Thumbnail',
            placeholder='Whats the thumbnail URL?',
            required= False,
            max_length=2048,
            default=default
        )
        self.add_item(self.Thumbnaile)


    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        try:
         embed.set_thumbnail(url=self.Thumbnaile.value)
         await interaction.response.edit_message(embed=embed)
        except:
           await interaction.response.send_message(f"{no} Please provide a valid url.", ephemeral=True)
           return
 
class Image(discord.ui.Modal, title='Image'):
    def __init__(self, default):
        super().__init__()



        self.Thumbnaile = discord.ui.TextInput(
            label='Image',
            placeholder='Whats the image URL?',
            max_length=2048,
            default=default
        )
        self.add_item(self.Thumbnaile)


    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        try:
         embed.set_image(url=self.Thumbnaile.value)
         await interaction.response.edit_message(embed=embed)
        except:
           await interaction.response.send_message(f"{no} Please provide a valid url.", ephemeral=True)
           return

class Author(discord.ui.Modal, title='Author'):
    def __init__(self, default, url):
        super().__init__()

        self.authortext = discord.ui.TextInput(
            label='Author Name',
            placeholder='Whats the author name?',
            required=False,
            max_length=256,
            default=default
        )

        self.iconUrl = discord.ui.TextInput(
            label='Icon URL',
            placeholder='Whats the icon URL?',
            required=False,
            max_length=2048,
            default=url
        )
        self.add_item(self.authortext)
        self.add_item(self.iconUrl)





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


class Infraction(discord.ui.View):
    def __init__(self, author, type):
        super().__init__(timeout=None)
        self.author = author
        self.type = type





    @discord.ui.button(label='Title', style=discord.ButtonStyle.grey, emoji="<:abc:1223062929709203487>")
    async def Title(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        embed = interaction.message.embeds[0]

        if embed and embed.title:
            default = embed.title
        else:
            default = "Untitled Embed"
        await interaction.response.send_modal(Title(default))


    @discord.ui.button(label='Description', style=discord.ButtonStyle.grey, emoji="<:description:1223062677572812920>")
    async def Description(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        embed = interaction.message.embeds[0]

        if embed and embed.description:
            default = embed.description
        else:
            default = None       
        await interaction.response.send_modal(Description(default))

    @discord.ui.button(label='Thumbnail', style=discord.ButtonStyle.grey, emoji="<:image:1223062544135094363>")
    async def Thumbnail(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)   
        embed = interaction.message.embeds[0]        
        if embed and embed.thumbnail:
            default = embed.thumbnail.url
        else:
            default = None             
        await interaction.response.send_modal(Thumbnail(default))

    @discord.ui.button(label='Image', style=discord.ButtonStyle.grey, emoji="<:Image:1223063095417765938>")
    async def photo(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        embed = interaction.message.embeds[0]        
        if embed and embed.image:
            default = embed.image.url
        else:
            default = None              
        await interaction.response.send_modal(Image(default))

    @discord.ui.button(label='Author', style=discord.ButtonStyle.grey, emoji="<:image:1223062544135094363>")
    async def Author(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        embed = interaction.message.embeds[0]

        if embed and embed.author.name:
            default = embed.author.name
        else:
            default = None
        if embed and embed.author.icon_url:
            default_url = embed.author.icon_url
        else:
            default_url = None
                
        await interaction.response.send_modal(Author(default, default_url))

    @discord.ui.button(label='Color', style=discord.ButtonStyle.grey, emoji="<:tag:1234998802948034721>")
    async def Color(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        if interaction.message.embeds[0].color:
            default = f"{interaction.message.embeds[0].color.value:06x}"
        else:
            default = None        
        await interaction.response.send_modal(Colour(default))        




    @discord.ui.button(label='Finish', style=discord.ButtonStyle.green, emoji=f"{tick}")
    async def Finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        embed = interaction.message.embeds[0]
        if embed.author.icon_url == interaction.user.display_avatar.url:
             author_icon = "{author.avatar}"
        else:
            author_icon = f"{embed.author.icon_url}"


        if embed.thumbnail.url == interaction.user.display_avatar.url:
             thumbnail = "{staff.avatar}"
        else:
            thumbnail = f"{embed.thumbnail.url}"
        filter = {"guild_id": interaction.guild.id, "type": self.type}
        color_hex = f"{embed.color.value:06x}"
        embed_data = {
            "type": self.type,
            "title": embed.title,
            "description": embed.description,
            "color": color_hex,
            "author": embed.author.name if embed.author else None,
            "author_icon": author_icon,
            "thumbnail": thumbnail,
            "image": embed.image.url if embed.image else None,
            "guild_id": interaction.guild.id
            }
        await Customisation.update_one(filter,  {"$set": embed_data}, upsert=True)
        embed = discord.Embed(title=f"{greencheck} Customisation Saved", description="Your embed has been saved." ,color=discord.Colour.brand_green())
        await interaction.response.edit_message(content=None, embed=embed, view=None)