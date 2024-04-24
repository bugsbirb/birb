import discord
import os
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *
import validators
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
customcommands = db['Custom Commands']
commandslogging = db['Commands Logging']


class CmdUsageChannel(discord.ui.ChannelSelect):
    def __init__(self, author, channels):
        super().__init__(placeholder='Command Usage Logging', channel_types=[discord.ChannelType.text, discord.ChannelType.news], default_values=channels)
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


            await commandslogging.update_one(filter, {'$set': data}, upsert=True)

            await refreshembed(interaction)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Channel ID: {channelid.id}")     


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
        amount = await customcommands.count_documents({"guild_id": interaction.guild.id})
        if amount >= 25:
         embed = discord.Embed()
         embed.title = f"{redx} {amount}/25"
         embed.description="You have reached the maximum amount of custom commands."
         embed.color = discord.Color.brand_red()
         await interaction.response.send_message(embed=embed, ephemeral=True)

         return
        result = await customcommands.find_one({"name": self.name.value, "guild_id": interaction.guild.id})
        embed = interaction.message.embeds[0]
        if result:
         embed = discord.Embed()
         embed.title = f"{redx} That already exists!"
         embed.color = discord.Color.brand_red()
         embed.description="Please try again."
         await interaction.response.send_message(embed=embed,  ephemeral=True)
         return           
        name = self.name.value
        view = NoEmbeds(self.author, name)
        await interaction.response.edit_message(embed=None,content=None,  view=view)
        await customcommands.insert_one({"name": name, "guild_id": interaction.guild.id, "creator": interaction.user.id})

class EditCommand(discord.ui.Modal, title='Edit Command'):
    def __init__(self, author):
        super().__init__()
        self.author = author




    name = discord.ui.TextInput(
        label='Name',
        placeholder='Whats the name of the command?',
        max_length=30
    )




    async def on_submit(self, interaction: discord.Interaction):
         result = await customcommands.find_one({"name": self.name.value, "guild_id": interaction.guild.id})
         embed = interaction.message.embeds[0]
         if result is None:
          embed.title = f"{redx} I could not find that."
          embed.description="I could not find the command you were trying to edit please try again."
          embed.color = discord.Color.brand_red()
          embed.clear_fields()
          await interaction.response.send_message(embed=embed, ephemeral=True)
          return

               
         if result.get('embed', False) is True:
            embed_title = result.get('title', None) 
            embed_description = result.get('description', None)   
            color_value = result.get('color', None)
            embed_author = result.get('author', None)

            colors = discord.Colour(int(color_value, 16)) if color_value else discord.Colour.dark_embed()               
            embed = discord.Embed(
                title=embed_title,
                description=embed_description, color=colors)
            if 'image' in result:
                embed.set_image(url=result['image'])
            if 'thumbnail' in result:
                embed.set_thumbnail(url=result['thumbnail'])


            if embed_author in ["None", None]:
                embed_author = ""

            if 'author' in result:
                embed.set_author(name=embed_author, icon_url=result['author_icon'])
                if 'author_icon' in result:
                    embed.set_author(name=embed_author, icon_url=result['author_icon'])
            if 'content' in result:
                contentmsg = result['content']    
            else:
                contentmsg = ""    
         
            await interaction.response.edit_message(content=contentmsg, embed=embed, view=Embeds(self.author, self.name.value))
         else:

            if 'content' in result:
                contentmsg = result['content']    
            else:
                contentmsg = ""               
            await interaction.response.edit_message(content=contentmsg, embed=None, view=NoEmbeds(self.author, self.name.value))   


class DeleteCommand(discord.ui.Modal, title='Delete Command'):
    def __init__(self, author):
        super().__init__()
        self.author = author




    name = discord.ui.TextInput(
        label='Name',
        placeholder='Whats the name of the command?',
        max_length=30
    )




    async def on_submit(self, interaction: discord.Interaction):
       result = await customcommands.find_one({"name": self.name.value, "guild_id": interaction.guild.id})
       embed = interaction.message.embeds[0]
       if result is None:
        embed.title = f"{redx} I could not find that."
        embed.description = "I couldn't find the command you were trying to delete please try again."
        embed.color = discord.Color.brand_red()
        embed.clear_fields()
        await interaction.response.send_message(embed=embed,  ephemeral=True)
        return
       customcommands.delete_one({"name": self.name.value, "guild_id": interaction.guild.id})
       embed = discord.Embed(description="Succesfully deleted the command.")
       embed.title = f"{greencheck} Command Deleted"
       embed.color = discord.Color.brand_green()
       await interaction.response.send_message(embed=embed,  ephemeral=True)

class CustomButton(discord.ui.Modal, title='Button Embed'):
    def __init__(self, author, names):
        super().__init__()
        self.author = author
        self.names = names






    name = discord.ui.TextInput(
        label='Custom Command Name',
        placeholder='What is the name of the custom command?',
        max_length=2048
    )

    label = discord.ui.TextInput(
        label='Button Name',
        placeholder='What text should be on the button?',
        max_length=80
    )
    emoji = discord.ui.TextInput(
        label='Emoji',
        placeholder='What emoji should be on the button? (Example: <:Alert:1208972002803712000>)',
        max_length=80,
        required=False
    )
    colour = discord.ui.TextInput(
        label='Colour',
        placeholder='Blurple, Red, Green, Grey',
        max_length=80,
        required=True
    )


    async def on_submit(self, interaction: discord.Interaction):
        colour = self.colour.value.lower()
        valid_colours = ['blurple', 'red', 'green', 'grey']
        result = await customcommands.find_one({"name": self.name.value, "guild_id": interaction.guild.id})
        if result is None:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name},** I could not find the custom command.", ephemeral=True)
            return

        if colour not in valid_colours:
         await interaction.response.send_message(f"{redx} **{interaction.user.display_name},** I could not find that colour. (Blurple, Red, Green, Grey)", ephemeral=True)
         return
        await customcommands.update_one({'name': self.names,'guild_id': interaction.guild.id}, {'$set': {'buttons': 'Embed Button', 'cmd': self.name.value, 'button_label': self.label.value, 'colour': self.colour.value, 'emoji': self.emoji.value}})
        await interaction.response.edit_message(content=f"{tick} **{interaction.user.display_name},** I've set the custom embed button with the command `{self.name.value}`.")

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
        await customcommands.update_one({'name': self.names,'guild_id': interaction.guild.id}, {'$set': {'url': url, 'buttons': 'Link Button', 'button_label': self.label.value}})
        await interaction.response.edit_message(content=f"{tick} **{interaction.user.display_name},** I've set the buttons to URL with the link `{self.name.value}`.")


class ButtonsSelectionView(discord.ui.Select):
    def __init__(self, author, name):
        self.author = author
        self.name = name
        options = [
            discord.SelectOption(label="Voting Buttons", description="Lets you view and vote."),
            discord.SelectOption(label="Link Button"),
            discord.SelectOption(label="Embed Button", description="Sends a custom command in an ephemeral embed.")
            

        
            
        ]
        super().__init__(placeholder='Buttons Selection', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)   
        if color == 'Voting Buttons':
         await customcommands.update_one({'name': self.name,'guild_id': interaction.guild.id}, {'$set': {'buttons': color}})
         await interaction.response.edit_message(content=f"{tick} **{interaction.user.display_name},** I've set the buttons to `{color}`.")
        if color == 'Link Button':
            await interaction.response.send_modal(ButtonURLView(self.author, self.name))
        if color == 'Embed Button':
            await interaction.response.send_modal(CustomButton(self.author, self.name))            


class ButtonsSelection(discord.ui.View):
    def __init__(self, author, name):
        super().__init__()
        self.add_item(ButtonsSelectionView(author, name))


class ToggleCommands(discord.ui.Select):
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'customcommands': True}}, upsert=True)    
            await refreshembed(interaction)  
        if color == 'Disabled':  
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'customcommands': False}}, upsert=True)   
            await refreshembed(interaction)   


class CreateButtons(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Create", emoji=f"{add}"),
            discord.SelectOption(label="Delete", emoji=f"{bin}"),
            discord.SelectOption(label="Edit", emoji=f"{pen}"),
            

        
            
        ]
        super().__init__(placeholder='Commands', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)  

        if color == 'Create':
            await interaction.response.send_modal(CreateCommand(self.author))

        elif color == 'Delete':
            await interaction.response.send_modal(DeleteCommand(self.author))  

        elif color == 'Edit':
            await interaction.response.send_modal(EditCommand(self.author))    


class Title(discord.ui.Modal, title='Title'):
    def __init__(self, title):
        super().__init__()
        self.title = title




        self.Titles = discord.ui.TextInput(
            label='title',
            placeholder='What is the title?',
            required=False,
            max_length=256,
            default=self.title
        )
        self.add_item(self.Titles)





    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.title = self.Titles.value
        try:
         await interaction.response.edit_message(embed=embed)
        except discord.HTTPException():
            return await interaction.response.send_message(f"{no} {interaction.user.display_name}, had an error adding the title please try again.", ephemeral=True)


class Description(discord.ui.Modal, title='Description'):
    def __init__(self, description):
        super().__init__()
        self.descriptions = description


    
        self.description = discord.ui.TextInput(
            label='Description',
            placeholder='What is the description?',
            style=discord.TextStyle.long,
            max_length=4000,
            required=False,
            default=self.descriptions

        )



        self.add_item(self.description)
    async def on_submit(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.description = self.description.value

        await interaction.response.edit_message(embed=embed)

class Colour(discord.ui.Modal, title='Colour'):
    def __init__(self, colour):
        super().__init__()
        self.colour = colour



        self.color = discord.ui.TextInput(
        label='Colour',
        placeholder='Do not include the hashtag',
        max_length=6,
        default=self.colour
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

class Context(discord.ui.Modal, title='Content'):
    def __init__(self, content):
        super().__init__()
        self.content = content



        self.color = discord.ui.TextInput(
            label='Content',
            placeholder='What do you want the content to be?',
            
            required=False,
            style=discord.TextStyle.long,
            max_length=2000,
            default=self.content
        )
        self.add_item(self.color)






    async def on_submit(self, interaction: discord.Interaction):
        color_value = self.color.value
        await interaction.response.edit_message(content=color_value)


class Thumbnail(discord.ui.Modal, title='Thumbnail'):
    def __init__(self, thumb):
        super().__init__()
        self.thumb =thumb



        self.Thumbnaile = discord.ui.TextInput(
            label='Thumbnail',
            placeholder='Whats the thumbnail URL?',
            required= False,
            max_length=2048,
            default=self.thumb
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
    def __init__(self, ima):
        super().__init__()
        self.ima = ima



        self.Thumbnaile = discord.ui.TextInput(
            label='Image',
            placeholder='Whats the image URL?',
            required=False,
            max_length=2048,
            default=self.ima
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
    def __init__(self, authotext, iconurl):
        super().__init__()
        self.authotext = authotext
        self.iconurl = iconurl

        self.authortext = discord.ui.TextInput(
            label='Author Name',
            placeholder='Whats the author name?',
            required=False,
            max_length=256,
            default=self.authotext
        )

        self.iconUrl = discord.ui.TextInput(
            label='Icon URL',
            placeholder='Whats the icon URL?',
            required=False,
            max_length=2048,
            default=self.iconurl
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


class NoEmbeds(discord.ui.View):
    def __init__(self, author, name):
        super().__init__()
        self.author = author
        self.name = name


    @discord.ui.button(label='Add Embed', style=discord.ButtonStyle.blurple, emoji="<:Add:1163095623600447558>")
    async def add_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        embed = discord.Embed(title="Untitled Embed", color=discord.Colour.dark_embed())
        view = Embeds(interaction.user, self.name)
        await interaction.response.edit_message(embed=embed, view=view)
     

    @discord.ui.button(label='Content', style=discord.ButtonStyle.blurple, emoji="<:Pen:1126527802255085628>")
    async def context(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        if interaction.message.content:
            default = interaction.message.content
        else:
            default = None


        await interaction.response.send_modal(Context(default))



    @discord.ui.button(label='Buttons', style=discord.ButtonStyle.blurple, emoji="<:Button:1223063359184830494>")
    async def Buttons(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                  
        await interaction.response.send_message(view= ButtonsSelection(self.author, self.name), ephemeral=True)     
         

    @discord.ui.button(label='Variables', style=discord.ButtonStyle.blurple, emoji="<:List:1179470251860185159>")
    async def Var(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)         

        embed = discord.Embed(title="Variables List", description="**{author.name}** = The name of the person who is using the command\n**{author.id}** = The user id who is using the command\n**{author.mention}** = Mention of the user using the command\n**{timestamp}** = Time stamp of when the command was used\n**{guild.name}** = The name of the server\n**{guild.id}** = The id of the server\n**{guild.owner.name}** = The name of the server owner\n**{guild.owner.id}** = The id of the server owner\n**{guild.owner.mention}** = The mention of the server owner", color=discord.Colour.dark_embed())  
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label='Permissions', style=discord.ButtonStyle.blurple, emoji="<:Permissions:1207365901956026368>")    
    async def Permissions(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_message(content=f"{tick} Please select the required roles for this command.", ephemeral=True, view=PermissionsView(self.author, self.name))


    @discord.ui.button(label='Finish', style=discord.ButtonStyle.green, emoji=f"{tick}", row=2)
    async def Finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        result = await customcommands.find_one({"name": self.name, "guild_id": interaction.guild.id})
        perm = result.get('permissionroles', None)
        if perm is None: 
            await interaction.response.send_message(content=f"{tick} **{interaction.user.display_name},** please select the required permissions for this command using the `Permission` button!", ephemeral=True)
            return
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

        await customcommands.update_one({"name": self.name, "guild_id": interaction.guild.id}, {"$set": embed_data}, upsert=True)
        embed = discord.Embed()
        embed.title = f"{greencheck} Success!"
        embed.description = f"Start by using </command run:1199462063202902077> and selecting `{self.name}`"
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
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            

        await interaction.response.edit_message(embed=None, view=NoEmbeds(interaction.user, self.name))        

    @discord.ui.button(label='Content', style=discord.ButtonStyle.blurple, emoji="<:Pen:1126527802255085628>")
    async def context(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)   
        result = await customcommands.find_one({'guild_id': interaction.guild.id, 'name': self.name})
        if result and result.get('content'):
            default = result.get('content')
        else:
            default = None                 
        await interaction.response.send_modal(Context(default))

    @discord.ui.button(label='Buttons', style=discord.ButtonStyle.blurple, emoji="<:Button:1223063359184830494>")
    async def Buttons(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                  
        await interaction.response.send_message(view= ButtonsSelection(self.author, self.name), ephemeral=True)     

    @discord.ui.button(label='Variables', style=discord.ButtonStyle.blurple, emoji="<:List:1179470251860185159>")
    async def Var(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)         

        embed = discord.Embed(
            title="Variables List",
            description="**{author.name}:** The name of the person who is using the command\n**{author.id}:** The user id who is using the command\n**{author.mention}** = Mention of the user using the command\n**{timestamp}:** Time stamp of when the command was used\n**{guild.name}:** The name of the server\n**{guild.id}:** The id of the server\n**{guild.owner.name}:** The name of the server owner\n**{guild.owner.id}** = The id of the server owner\n**{guild.owner.mention}:**  The mention of the server owner\n**{random}:** Randomly generated number.\n**{channel.name}:** Name of the channel where the custom command is sent\n**{channel.id}:** Id of the channel where the custom command is sent\n**{channel.mention}:** Mention of the channel where the custom command is sent",
            color=discord.Colour.dark_embed(),
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label='Permissions', style=discord.ButtonStyle.blurple, emoji="<:Permissions:1207365901956026368>")    
    async def Permissions(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_message(content=f"{tick} Please select the required roles for this command.", ephemeral=True, view=PermissionsView(self.author, self.name))

    @discord.ui.button(label='Title', style=discord.ButtonStyle.grey, emoji="<:abc:1193192444938956800>")
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

    @discord.ui.button(label='Description', style=discord.ButtonStyle.grey, emoji="<:description:1193192044307415040>")
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

    @discord.ui.button(label='Thumbnail', style=discord.ButtonStyle.grey, emoji="<:image:1193191680690630706>")
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

    @discord.ui.button(label='Image', style=discord.ButtonStyle.grey, emoji="<:Image:1195058849741295748>")
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

    @discord.ui.button(label='Author', style=discord.ButtonStyle.grey, emoji="<:image:1193191680690630706>")
    async def Author(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        result = await customcommands.find_one({'guild_id': interaction.guild.id, 'name': self.name})
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

    @discord.ui.button(label='Color', style=discord.ButtonStyle.grey, emoji="<:tag:1162134250414415922>")
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

    @discord.ui.button(label='Finish', style=discord.ButtonStyle.green, emoji=f"{tick}", row=2)
    async def Finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        result = await customcommands.find_one({"name": self.name, "guild_id": interaction.guild.id})
        perm = result.get('permissionroles', None)
        if perm is None: 
            await interaction.response.send_message(content=f"{tick} **{interaction.user.display_name},** please select the required permissions for this command using the `Permission` button!", ephemeral=True)
            return
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

        await customcommands.update_one({"name": self.name, "guild_id": interaction.guild.id}, {"$set": embed_data}, upsert=True)
        embed = discord.Embed()
        embed.title = f"{greencheck} Success!"
        embed.description = f"Start by using </command run:1199462063202902077> and selecting `{self.name}`"
        embed.color = discord.Colour.brand_green()
        await interaction.response.edit_message(content=None, embed=embed, view=None)

class Permission(discord.ui.RoleSelect):
    def __init__(self, author, name):

        super().__init__(placeholder='Command Permission', max_values=20)
        self.author = author
        self.name = name
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        selected_role_ids = [role.id for role in self.values]    
  
        data = {
            'permissionroles': selected_role_ids
        }

        await customcommands.update_one({'name': self.name, 'guild_id': interaction.guild.id}, {'$set': data}, upsert=True)
        await interaction.response.edit_message(content=f"{tick} **{interaction.user.display_name},** I've set the permission requirement.",  view=None)


async def refreshembed(interaction):
            commands = customcommands.find({'guild_id': interaction.guild.id})
            moduledata = await modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = 'False'
            if moduledata:
                modulemsg = moduledata.get('customcommands', 'False')
                
        

            logging = await commandslogging.find_one({'guild_id': interaction.guild.id})
            loggingmsg = "Not Configured"
            if logging:
                loggingid = logging['channel_id']
                loggingmsg = f"<#{loggingid}>"




            
            amount = await customcommands.count_documents({'guild_id': interaction.guild.id})
            commands = await commands.to_list(length=amount)
            embed = discord.Embed(title=f"<:command1:1199456319363633192> Custom Commands ({amount}/25)", description="", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            embed.add_field(name="<:settings:1207368347931516928> Custom Commands Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Logging Channel:** {loggingmsg}")
            for result in commands:
                permissions = result.get('permissionroles', 'None')
                if permissions == 'None':
                    permissions = "None"
                else:
                    permissions = ", ".join([f"<@&{roleid}>" for roleid in permissions])
                embed.add_field(name=f"<:command1:1199456319363633192> {result['name']}", value=f"{arrow} **Created By:** <@{result['creator']}>\n{arrow} **Required Permissions:** {permissions}", inline=False)
            try:    
             await interaction.message.edit(embed=embed)
            except:
                return print("[⚠️] Couldn't edit module due to missing permissions.") 


class PermissionsView(discord.ui.View):
    def __init__(self, author, name):
        super().__init__()
        self.add_item(Permission(author, name))
