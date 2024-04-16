import discord
import os
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *
import validators
MONGO_URL = os.getenv('MONGO_URL')

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo['astro']
modules = db['Modules']
welcome = db['welcome settings']
customcommands = db['Custom Commands']


class ToggleWelcome(discord.ui.Select):
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
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'welcome': True}}, upsert=True)    
            await refreshembed(interaction)   
        if color == 'Disabled':  
            await interaction.response.send_message(content=f"{no} Disabled", ephemeral=True)
            await modules.update_one({'guild_id': interaction.guild.id}, {'$set': {'welcome': False}}, upsert=True)
            await refreshembed(interaction)            

class WelcomeChannel(discord.ui.ChannelSelect):
    def __init__(self, author, channels):
        super().__init__(placeholder='Welcome Channel', channel_types=[discord.ChannelType.text, discord.ChannelType.news], default_values=channels)
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
            'welcome_channel': channelid.id,  
            'guild_id': interaction.guild_id
        }

        try:


            await welcome.update_one(filter, {'$set': data}, upsert=True)

            await refreshembed(interaction)
            await interaction.response.edit_message(content=None)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        print(f"Welcome Channel ID: {channelid.id}")        

class Welcomemessage(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Customise"),
            discord.SelectOption(label="Default Welcome Message"),
            discord.SelectOption(label="Manage Buttons")
        ]
        super().__init__(placeholder='Welcome Message', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        color = self.values[0]
        try:
            if interaction.user.id != self.author.id:
                embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                      color=discord.Colour.dark_embed())
                return await interaction.response.send_message(embed=embed, ephemeral=True)

            if color == 'Customise':
                if await welcome.find_one({'guild_id': interaction.guild.id}):
                    result = await welcome.find_one({'guild_id': interaction.guild.id})

                    if 'embed' in result and result['embed']:
                        embed_title = result.get('title')
                        embed_description = result.get('description')
                        embed_author = result.get('author')

                        if embed_title in ["None", None]:
                            embed_title = ""
                        if embed_description in ["None", None]:
                            embed_description = ""
                        color_value = result.get('color', None)
                        colors = discord.Colour(int(color_value, 16)) if color_value else discord.Colour.dark_embed()

                        embed = discord.Embed(
                            title=embed_title,
                            description=embed_description, color=colors)

                        if embed_author in ["None", None]:
                            embed_author = ""
                        if 'image' in result:
                            embed.set_image(url=result['image'])
                        if 'thumbnail' in result:
                            embed.set_thumbnail(url=result['thumbnail'])
                        if 'author' in result and 'author_icon' in result:
                            embed.set_author(name=embed_author, icon_url=result['author_icon'])
                        contentresult = result.get('content')
                        if contentresult in ["None", None]:
                            contentresult = ""
                        await interaction.response.edit_message(
                            content=contentresult, embed=embed, view=Embeds(interaction.user))
                    elif 'content' in result and result['content']:
                        contentresult = result.get('content')
                        if contentresult in ["None", None]:
                            return
                        await interaction.response.edit_message(
                            content=contentresult, embed=None, view=NoEmbeds(interaction.user))
                    else:
                        await interaction.response.edit_message(view=NoEmbeds(interaction.user), embed=None, content=None)
                        

                else:
                    await interaction.response.edit_message(view=NoEmbeds(interaction.user), embed=None, content=None)

            elif color == 'Default Welcome Message':
                await welcome.update_one({'guild_id': interaction.guild.id}, {
                    '$set': {'content': '👋 Welcome {user.mention} to **{guild.name}**! We hope you enjoy your stay here.',
                             'embed': False}}, upsert=True)
                await interaction.response.edit_message(content=None)
            elif color == 'Manage Buttons':
                view = ButtonManage(interaction.user)
                await interaction.response.send_message(ephemeral=True, view=view)
        except Exception as e:
            print(f"An error occurred at {interaction.guild.name}: {e}")
            await interaction.response.send_message(f"{crisis} An error occurred if this continues contact support.", ephemeral=True)
 


class managebuttons(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="URL Button"),
            discord.SelectOption(label="Custom Command Button"),
            discord.SelectOption(label="Reset To Default")

            

        
            
        ]
        super().__init__(placeholder='Manage Buttons', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        options = self.values[0]
        if options == 'URL Button':    
            await interaction.response.send_modal(ButtonURLView(interaction.user))
        elif options == 'Custom Command Button':    
            await interaction.response.send_modal(CustomButton(interaction.user))
        elif options == 'Reset To Default':
              await welcome.update_one({'guild_id': interaction.guild.id}, {'$set': {'buttons': None}}, upsert=True)
              await interaction.response.edit_message(f"{tick} Succesfully reset the buttons to default.", view=None)


## --- Custom Welcome Message Below

class CustomButton(discord.ui.Modal, title='Button Embed'):
    def __init__(self, author):
        super().__init__()
        self.author = author






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
        result = await customcommands.find_one({"guild_id": interaction.guild.id})
        if result is None:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name},** I could not find the custom command.")
            return

        if colour not in valid_colours:
         await interaction.response.send_message(f"{redx} **{interaction.user.display_name},** I could not find that colour. (Blurple, Red, Green, Grey)", ephemeral=True)
         return
        await welcome.update_one({'guild_id': interaction.guild.id}, {'$set': {'buttons': 'Embed Button', 'cmd': self.name.value, 'button_label': self.label.value, 'colour': self.colour.value, 'emoji': self.emoji.value}}, upsert=True)
        await interaction.response.edit_message(content=f"{tick} **{interaction.user.display_name},** I've set the custom embed button with the command `{self.name.value}`.", view=None)


class ButtonURLView(discord.ui.Modal, title='Button URL'):
    def __init__(self, author):
        super().__init__()
        self.author = author






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
        await welcome.update_one({'guild_id': interaction.guild.id}, {'$set': {'url': url, 'buttons': 'Link Button', 'button_label': self.label.value}}, upsert=True)
        await interaction.response.edit_message(content=f"{tick} **{interaction.user.display_name},** I've set the buttons to URL with the link `{self.name.value}`.", view=None)



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
        if embed.title and embed.description is None:
            await interaction.response.send_message(f"{no} You need either a title or description.", ephemeral=True)
            return
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

class ButtonManage(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.add_item(managebuttons(author))

class NoEmbeds(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author


    @discord.ui.button(label='Add Embed', style=discord.ButtonStyle.blurple, emoji="<:Add:1163095623600447558>")
    async def add_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        embed = discord.Embed(title="Untitled Embed", color=discord.Colour.dark_embed())
        view = Embeds(interaction.user)
        await interaction.response.edit_message(embed=embed, view=view)
     

    @discord.ui.button(label='Content', style=discord.ButtonStyle.blurple, emoji="<:Pen:1126527802255085628>")
    async def context(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        await interaction.response.send_modal(Context())

   
         

    @discord.ui.button(label='Variables', style=discord.ButtonStyle.blurple, emoji="<:List:1179470251860185159>")
    async def Var(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)         

        embed = discord.Embed(
            title="Variables List",
            description="**{membercount}:** How many members are in the server.\n**{user}** = The name of the person whos joining.\n**{user.id}** = The user id who joined.\n**{user.mention}** = Mention of the user using the command\n**{timestamp}** = Time stamp the user joined.\n**{guild.name}** = The name of the server\n**{guild.id}** = The id of the server\n**{guild.owner.name}** = The name of the server owner\n**{guild.owner.id}** = The id of the server owner\n**{guild.owner.mention}** = The mention of the server owner",
            color=discord.Colour.dark_embed(),
        )


        await interaction.response.send_message(embed=embed, view=Button(), ephemeral=True)

    @discord.ui.button(label='Finish', style=discord.ButtonStyle.green, emoji=f"{tick}", row=2)
    async def Finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        message = interaction.message
        if interaction.message.content is None:
            messagecontent = None
        else:
            messagecontent = interaction.message.content

        if not message.embeds:
            embed_data = {
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
            "description": embed.description,
            "color": color_hex,
            "author": embed.author.name if embed.author else None,
            "author_icon": embed.author.icon_url if embed.author else None,
            "thumbnail": embed.thumbnail.url if embed.thumbnail else None,
            "image": embed.image.url if embed.image else None,
            "guild_id": interaction.guild.id,
            "content": messagecontent
            }

        await welcome.update_one({"guild_id": interaction.guild.id}, {"$set": embed_data}, upsert=True)
        embed = discord.Embed()
        embed.title = f"{greencheck} Success!"
        embed.description = "Your welcome message has been updated!"
        embed.color = discord.Colour.brand_green()
        await interaction.response.edit_message(content=None, embed=embed, view=None)   

class Embeds(discord.ui.View):
    def __init__(self, author):
        super().__init__()     
        self.author = author

    @discord.ui.button(label='Remove Embed', style=discord.ButtonStyle.blurple, emoji="<:bin:1160543529542635520>")
    async def removeembed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            

        await interaction.response.edit_message(embed=None, view=NoEmbeds(interaction.user))        

    @discord.ui.button(label='Content', style=discord.ButtonStyle.blurple, emoji="<:Pen:1126527802255085628>")
    async def context(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)            
        await interaction.response.send_modal(Context())

    @discord.ui.button(label='Variables', style=discord.ButtonStyle.blurple, emoji="<:List:1179470251860185159>")
    async def Var(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)         

        embed = discord.Embed(
            title="Variables List",
            description="**{membercount}:** How many members are in the server.\n**{user}** = The name of the person whos joining.\n**{user.id}** = The user id who joined.\n**{user.mention}** = Mention of the user using the command\n**{timestamp}** = Time stamp the user joined.\n**{guild.name}** = The name of the server\n**{guild.id}** = The id of the server\n**{guild.owner.name}** = The name of the server owner\n**{guild.owner.id}** = The id of the server owner\n**{guild.owner.mention}** = The mention of the server owner",
            color=discord.Colour.dark_embed(),
        )
        


        await interaction.response.send_message(embed=embed, ephemeral=True, view=Button())

    @discord.ui.button(label='Title', style=discord.ButtonStyle.grey, emoji="<:abc:1193192444938956800>")
    async def Title(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Title())

    @discord.ui.button(label='Description', style=discord.ButtonStyle.grey, emoji="<:description:1193192044307415040>")
    async def Description(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Description())

    @discord.ui.button(label='Thumbnail', style=discord.ButtonStyle.grey, emoji="<:image:1193191680690630706>")
    async def Thumbnail(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Thumbnail())

    @discord.ui.button(label='Image', style=discord.ButtonStyle.grey, emoji="<:Image:1195058849741295748>")
    async def photo(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Image())

    @discord.ui.button(label='Author', style=discord.ButtonStyle.grey, emoji="<:image:1193191680690630706>")
    async def Author(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Author())

    @discord.ui.button(label='Color', style=discord.ButtonStyle.grey, emoji="<:tag:1162134250414415922>")
    async def Color(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Colour())        

    @discord.ui.button(label='Finish', style=discord.ButtonStyle.green, emoji=f"{tick}", row=2)
    async def Finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        message = interaction.message
        if interaction.message.content is None:
            messagecontent = None
        else:
            messagecontent = interaction.message.content

        if not message.embeds:
            embed_data = {
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
            "description": embed.description,
            "color": color_hex,
            "author": embed.author.name if embed.author else None,
            "author_icon": embed.author.icon_url if embed.author else None,
            "thumbnail": embed.thumbnail.url if embed.thumbnail else None,
            "image": embed.image.url if embed.image else None,
            "guild_id": interaction.guild.id,
            "content": messagecontent
            }

        await welcome.update_one({"guild_id": interaction.guild.id}, {"$set": embed_data}, upsert=True)
        embed = discord.Embed()
        embed.title = f"{greencheck} Success!"
        embed.description = "Your welcome message has been updated!"
        embed.color = discord.Colour.brand_green()
        await interaction.response.edit_message(content=None, embed=embed, view=None)            



async def refreshembed(interaction):
            welcomechannelresult = await welcome.find_one({'guild_id': interaction.guild.id})
            moduleddata = await modules.find_one({'guild_id': interaction.guild.id})
            modulemsg = ""
            wchannelmsg = "Not Configured"

                

                
            if moduleddata:
                modulemsg = moduleddata.get('welcome', False)
            if welcomechannelresult:    
                channelid = welcomechannelresult.get('welcome_channel', None)
                if channelid is None:
                   wchannelmsg = "Not Configured"
                else:   
                   
                 channel = interaction.guild.get_channel(channelid)
                 if channel is None:
                    wchannelmsg = "<:Error:1223063223910010920> Channel wasn't found please reconfigure."
                 else:    
                  wchannelmsg = channel.mention          

            embed = discord.Embed(title="<:welcome:1218531757691764738> Welcome Module",  color=discord.Color.dark_embed())
            embed.add_field(name="<:settings:1207368347931516928> Welcome Configuration", value=f"{replytop}**Enabled:** {modulemsg}\n{replybottom}**Welcome Channel:** {wchannelmsg}\n\n\n<:Tip:1167083259444875264> If you need help either go to the [support server](https://discord.gg/36xwMFWKeC) or read the [documentation](https://docs.astrobirb.dev)", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
            try:
             await interaction.message.edit(embed=embed)   
            except discord.Forbidden:
                print("Couldn't edit module due to missing permissions.")       
class Button(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = 'https://discord.gg/DhWdgfh3hN'
        
        self.add_item(discord.ui.Button(label='All Variables', url="https://docs.astrobirb.dev/astro-birb/configuration/variables", style=discord.ButtonStyle.blurple, emoji="📚"))
