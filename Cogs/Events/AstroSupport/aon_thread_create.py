import discord
from discord.ext import commands
import asyncio
from emojis import *


class AForumCreaton(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener('on_thread_create')
    async def on_created_thread(self, thread: discord.Thread):
        if thread.guild.id != 1092976553752789054:
            print(thread.guild.id)
            return
        if thread.parent_id != 1101807246079442944:
            return

        await asyncio.sleep(2)
        banner = discord.Embed(title="", color=discord.Color.dark_embed())
        applied_tags = [tag.name for tag in thread.applied_tags]

            
        
        banner.set_image(url="https://cdn.discordapp.com/attachments/1104358043598200882/1169328494044528710/006_2.png?ex=65550106&is=65428c06&hm=392ce6de8fa7f60763c87ac8f2ee9cbad49ed5603ea6555d6be6da36fc8ce6ea&")
        embed = discord.Embed(title=f"<:forum:1162134180218556497> Astro Support", description="> Welcome to Astro Support please wait for a support representative to respond!", color=discord.Color.dark_embed())
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")
        embed.set_thumbnail(url="https://cdn.discordapp.com/icons/1092976553752789054/bf1e0138243c734664bbf9fbf8d5ae20.png?size=512")
        view = ForumManage()
        if 'Bugs' in applied_tags:
            embed.title = "🐛 Bug Report"
            embed.description ="> Welcome to Astro Support please wait for a developer to respond!\n\n<:Information:1115338749728002089> Please provide as much detail as possible to help us resolve the issue!"
            await thread.send(content='<@&1092977919858593912>', embeds=(banner, embed), allowed_mentions=discord.AllowedMentions(roles=True), view=view)
            return
        else: 
         await thread.send(content='<@&1092977110412439583>', embeds=(banner, embed), allowed_mentions=discord.AllowedMentions(roles=True), view=view) 

class ForumManage(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        

    @discord.ui.button(label="Mark Resolved", style=discord.ButtonStyle.success, custom_id="PERSISTENT:RESOLVE")    
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        requiredrole = discord.utils.get(interaction.guild.roles, id=1160257124060893365)
        if requiredrole not in interaction.user.roles:
            return await interaction.response.send_message(f"{no} You do not have the required role to mark this thread as resolved.", ephemeral=True)        
        button.disabled = True
        channel = interaction.guild.get_channel(1170350695220789258)

        all_tags = channel.available_tags
        tag = discord.utils.get(all_tags, name="Resolved")
        await interaction.channel.add_tags(tag)
        await interaction.response.edit_message(content=None, view=self)
        owner = interaction.channel.owner
        
        if owner:
            embed = discord.Embed(title=f"{tick} Thread Resolved", description="Your thread has been marked as resolved, if you need further assistance please create a new thread.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=f"Resolved by {interaction.user}", icon_url=interaction.user.display_avatar)
            view = Feedback()
            await interaction.channel.send(owner.mention, embed=embed, view=view)
        else:
            return await interaction.response.send_message(f"{no} Thread owner not found. (Still marked as resolved)", ephemeral=True)    
        


    @discord.ui.button(label="Lock", style=discord.ButtonStyle.danger, custom_id="PERSISTENT:LOCK")
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        requiredrole = discord.utils.get(interaction.guild.roles, id=1160257124060893365)
        if requiredrole not in interaction.user.roles:
            return await interaction.response.send_message(f"{no} You do not have the required role to lock this thread.", ephemeral=True)        
        button.disabled = True
        await interaction.channel.edit(locked=True)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Request Administration+", style=discord.ButtonStyle.primary, custom_id="PERSISTENT:REQUEST")    
    async def request(self, interaction: discord.Interaction, button: discord.ui.Button):
        requiredrole = discord.utils.get(interaction.guild.roles, id=1160257124060893365)
        if requiredrole not in interaction.user.roles:
            return await interaction.response.send_message(f"{no} You do not have the required role to request adminstration.", ephemeral=True)
        button.disabled = True
        embed = discord.Embed(title="<:announcement:1192867080408682526> Administration Requested!", description="Please wait for a administrator representative to respond.", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.set_author(name=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar)
        await interaction.message.reply(content="<@&1092977224501710848>/<@&1092977378638188594> ", embed=embed)
        await interaction.response.edit_message(view=self)

class Feedback(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Submit Feedback", style=discord.ButtonStyle.success, emoji="📝", custom_id="PERSISTENT:SUBMIT")
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel.owner == interaction.user:
            return await interaction.response.send_message(f"{no} You are not the owner of this thread.", ephemeral=True)
        await interaction.response.send_modal(FeedbackModal())
        

class FeedbackModal(discord.ui.Modal, title='Feedback'):

    rating = discord.ui.TextInput(label="What would you rate your support?",placeholder="From 1 - 10", min_length=1, max_length=2)
    feedback = discord.ui.TextInput(label="What feedback would you like to provide?", placeholder="Your feedback here", min_length=1, max_length=500, required=False)

    

    async def on_submit(self, interaction: discord.Interaction):

        channel = interaction.guild.get_channel(1207718356073844736)
        feedback = self.feedback.value
        if self.feedback is None:
            feedback = "No feedback provided"
        embed = discord.Embed(title="Support Feedback", description=f"> **Support Author:** {interaction.channel.owner.mention}\n> **Rating:** {self.rating}/10\n> **Feedback:** {feedback}\n> **Support Thread:** {interaction.channel.jump_url}", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=interaction.channel.owner.display_avatar)
        embed.set_footer(text=f"User ID: {interaction.user.id}")
        embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar)
        view=discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="Support Feedback (Submitted)", disabled=True, emoji="📝"))
        await interaction.message.edit(view=view)

        msg = await channel.send(embed=embed)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="View Feedback", url=msg.jump_url))        
        await interaction.response.send_message(f"{tick} Feedback submitted successfully!", ephemeral=True, view=view)

        

async def setup(client: commands.Bot) -> None:
    await client.add_cog(AForumCreaton(client))   