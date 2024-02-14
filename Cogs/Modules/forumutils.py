import discord
import discord.ext
from discord.ext import commands
import os
import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from emojis import *
from permissions import *
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
forumsconfig = db['Forum Configuration']
modules = db['Modules']

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
        await interaction.response.edit_message(embed=embed)


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
        max_length=6
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

class Roleping(discord.ui.Modal, title='Role Ping'):
    def __init__(self):
        super().__init__()



    role = discord.ui.TextInput(
        label='Role ID',
        placeholder='What is the role id? (Has to be role ID)',
        max_length=50
    )




    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=f"{self.role.value}")

class Thumbnail(discord.ui.Modal, title='Thumbnail'):
    def __init__(self):
        super().__init__()



    Thumbnaile = discord.ui.TextInput(
        label='Thumbnail',
        placeholder='Whats the thumbnail URL?',
        required=False,
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
 


class ForumView(discord.ui.View):
    def __init__(self, author, name):
        super().__init__()
        self.author = author
        self.name = name
        self.add_item(ForumChannel(author, self.name))











class ForumChannel(discord.ui.ChannelSelect):
    def __init__(self, author, name):
        super().__init__(placeholder='Forum Channel', channel_types=[discord.ChannelType.forum])
        self.author = author
        self.name = name
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)                  
        channelid = self.values[0]

        
    

        view = Embed(self.author, self.name, channelid)
        embed = discord.Embed(title="Untitled Embed",  color=discord.Color.dark_embed())
        await interaction.response.edit_message(embed=embed ,view=view)


        

        print(f"Channel ID: {channelid.id}")      

class ForumView(discord.ui.View):
    def __init__(self, author, name):
        super().__init__()
        self.author = author
        self.name = name
        self.add_item(ForumChannel(author, self.name))



class CreateForum(discord.ui.Modal, title='Create Forum Message'):
    def __init__(self, author):
        super().__init__()
        self.author = author


    name = discord.ui.TextInput(
        label='Name',
        placeholder='What do you want the name to be?',
        max_length=30
        
    )




    async def on_submit(self, interaction: discord.Interaction):
        result = await forumsconfig.find_one({"name": self.name.value, "guild_id": interaction.guild.id})
        embed = interaction.message.embeds[0]
        if result:
         embed = discord.Embed()
         embed.title = f"{redx} That already exists."
         embed.color = discord.Color.brand_red()
         embed.description=f"Please try again."
         await interaction.response.edit_message(embed=embed, view=None)
         return           
        name = self.name.value
        embed = discord.Embed(title=f"<:tag:1162134250414415922> Forum Channel", description=f"> Okay, now select a **forum channel.**", color=discord.Color.dark_embed())
        view = ForumView(self.author, name)
        await interaction.response.edit_message(embed=embed, view=view)


class DeleteForum(discord.ui.Modal, title='Delete Forum'):
    def __init__(self):
        super().__init__()




    name = discord.ui.TextInput(
        label='Name',
        placeholder='Whats the name of the forum channel?',
        max_length=30
    )




    async def on_submit(self, interaction: discord.Interaction):
       result = await forumsconfig.find_one({"name": self.name.value})
       embed = interaction.message.embeds[0]
       if result is None:
        embed.title = f"{redx} I could not find that."
        embed.color = discord.Color.brand_red()
        await interaction.response.edit_message(embed=embed)
        return
       await forumsconfig.delete_one({"name": self.name.value})
       embed = discord.Embed(description="Succesfully deleted the Forum message.")
       embed.title = f"{greencheck} Forum Deleted"
       embed.color = discord.Color.brand_green()
       await interaction.response.edit_message(embed=embed, view=None)




class Forums(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_group()
    async def forums(self, ctx):
        return





    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Forums'] == True:   
        return True
    @forums.command(description="Lock a forum thread")        
    async def lock(self, ctx):
     if not await has_staff_role(ctx):
        
         return              
     if isinstance(ctx.channel, discord.Thread):   
        try:                  
         await ctx.channel.edit(locked=True, reason=f"{ctx.author.display_name}, locked the forum")
        except discord.Forbidden:
            return await ctx.send(f"{no} **{ctx.author.display_name},** I don't have permission to unlock this forum.")
        await ctx.send(f"{tick} Forum **Locked.**")
     else:   
        await ctx.send(f"{no} This command only works in **forum channels.**")

    @forums.command(description="Unlock a forum thread")        
    async def unlock(self, ctx):
     if not await has_staff_role(ctx):
         return              
     if isinstance(ctx.channel, discord.Thread):
        try:        
         await ctx.channel.edit(locked=False, reason=f"{ctx.author.display_name}, unlocked the forum")
        except discord.Forbidden:
            return await ctx.send(f"{no} **{ctx.author.display_name},** I don't have permission to unlock this forum.")
         
        await ctx.send(f"{tick} Forum **Unlocked.**")
     else:   
        await ctx.send(f"{no} This command only works in **forum channels.**")

    @forums.command(description="Archive a forum thread")        
    async def archive(self, ctx):
     if not await has_staff_role(ctx):
         return            
     if isinstance(ctx.channel, discord.Thread):        

        try:
         await ctx.channel.edit(archived=True, reason=f"{ctx.author.display_name}, archived the forum")
        except discord.Forbidden:
            return await ctx.send(f"{no} **{ctx.author.display_name},** I don't have permission to unlock this forum.")       
        await ctx.send(f"{tick} Forum **Archived.**")  
     else:   
        await ctx.send(f"{no} This command only works in **forum channels.**")


    @forums.command(description="Create a Forum Creation Embed")
    @commands.has_guild_permissions(administrator=True)
    async def manage(self, ctx):   
       embed = discord.Embed(title="<:forum:1162134180218556497> Forum Message Manager", description="When an individual opens a forum post, a forum message is automatically posted", color=discord.Color.dark_embed())
       async for result in forumsconfig.find({"guild_id": ctx.guild.id}):
        role = result['role']
        
        
        if role == "" or None:
           role = None
           rolemention = f"None"

        else:   
            rolemention = f"<@&{role}>"
              
        embed.add_field(name=f"<:Document:1166803559422107699> {result['name']}", value=f"<:arrow:1166529434493386823>**Channel:** <#{result['channel_id']}>\n<:arrow:1166529434493386823>**Role:** {rolemention}\n<:arrow:1166529434493386823>**Title:** {result['title']}\n<:arrow:1166529434493386823>**Description:** {result['description']}\n<:arrow:1166529434493386823>**Thumbnail:** {result['thumbnail']}", inline=False)
       embed.set_thumbnail(url=ctx.guild.icon.url)
       embed.set_author(name=f"{ctx.author.display_name}", icon_url=ctx.author.display_avatar)
       view = ForumsManage(ctx.author)
       await ctx.send(embed=embed, view=view)





     


    @manage.error
    async def permissionerror(self, ctx, error):
        if isinstance(error, commands.MissingPermissions): 
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to manage forums.\n<:Arrow:1115743130461933599>**Required:** ``Administrator``")              


class ForumsManage(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author


    @discord.ui.button(label='Create', style=discord.ButtonStyle.green,  emoji="<:Add:1163095623600447558>")
    async def Create(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(CreateForum(self.author))


    @discord.ui.button(label='Delete', style=discord.ButtonStyle.red,  emoji="<:bin:1160543529542635520>")
    async def Delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)   
        await interaction.response.send_modal(DeleteForum())




class Embed(discord.ui.View):
    def __init__(self, author, name,channel):
        super().__init__(timeout=None)
        self.author = author
        self.name = name
        self.channel = channel




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

    @discord.ui.button(label='Image', style=discord.ButtonStyle.grey, emoji="<:image:1193191680690630706>")
    async def Images(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Image())

    @discord.ui.button(label='Color', style=discord.ButtonStyle.grey, emoji="<:tag:1162134250414415922>")
    async def Color(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Colour())        

    @discord.ui.button(label='Ping', style=discord.ButtonStyle.grey, emoji="<:Role:1162074735803387944>")
    async def Ping(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        await interaction.response.send_modal(Roleping())


    @discord.ui.button(label='Finish', style=discord.ButtonStyle.green, emoji=f"{tick}")
    async def Finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    

        embed = interaction.message.embeds[0]
        message = interaction.message.content     
        if message is None:
           message = None
        color_hex = f"{embed.color.value:06x}"
        embed_data = {
            "title": embed.title,
            "description": embed.description,
            "color": color_hex,
            "thumbnail": embed.thumbnail.url if embed.thumbnail else None,
            "image": embed.image.url if embed.image else None,
            "guild_id": interaction.guild.id,
            "channel_id": self.channel.id,
            "role": message,
            "name": self.name
            }
        await forumsconfig.insert_one(embed_data)
        embed = discord.Embed()
        embed.title = f"{greencheck} Succesfully Created"
        embed.description = f"Start by trying to create forum in <#{self.channel.id}>!"
        embed.color = discord.Colour.brand_green()
        await interaction.response.edit_message(content=None, embed=embed, view=None)
           




async def setup(client: commands.Bot) -> None:
    await client.add_cog(Forums(client))     
                
