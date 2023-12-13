import discord
import discord
from discord.ext import commands
from typing import Literal
import datetime
from datetime import timedelta
import asyncio
from discord import app_commands
from discord.ext import commands, tasks
import pytz
from pymongo import MongoClient
import platform
import os
from dotenv import load_dotenv
from emojis import * 
MONGO_URL = os.getenv('MONGO_URL')
mongo = MongoClient(MONGO_URL)
db = mongo['astro']
badges = db['User Badges']


class HelpdeskDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Whats the servers rules?', emoji='<:arrow:1166529434493386823>'),
            discord.SelectOption(label='What is Astro Birb?', emoji='<:arrow:1166529434493386823>'),
            discord.SelectOption(label="How do I become staff here?", emoji="<:arrow:1166529434493386823>"),
            discord.SelectOption(label="Wheres the documentation?", emoji="<:arrow:1166529434493386823>"),
            discord.SelectOption(label="How do you setup the bot?", emoji="<:arrow:1166529434493386823>")


        
            
        ]
        super().__init__(placeholder='Helpdesk', min_values=1, max_values=1, options=options, custom_id='persitent:HelpDeskDropwon')
    async def callback(self, interaction: discord.Interaction):

        selected = self.values[0] 
        if selected == 'What is Astro Birb?':
            embed = discord.Embed(title="", description="## 🐦 What is Astro Birb?\n> Astro Birb is designed to simplify tasks related to managing punishments and staff. It includes features such as handling infractions, promotions, and monitoring message quotas.", color=discord.Color.dark_embed())
        elif selected == 'How do I become staff here?':
            embed = discord.Embed(title="", description="## <:leaf:1160541147320553562> How do I become staff?\nCurrently support & QA is handpicked meaning you have to show your activity in the support server by either answering support forums or activily talking in the server.", color=discord.Color.dark_embed())
        elif selected == 'Whats the servers rules?':
            embed = discord.Embed(title="", description=f"## 🌿 Community Guidelines\n* **Respectful Conduct.** Let's keep the atmosphere respectful and welcoming. Avoid spam, NSFW content, advertising, and political discussions. Help us maintain a community free from these topics in both general discussions and private messages.\n* **Maturity Matters.** When a healthy debate begins to escalate into an argument, consider taking a step back. Our team is here to assist, so please cooperate with their guidance. We're all striving for a positive environment.\n* **Mindful Conversations.** Join us in keeping conversations relevant to their respective channels and maintaining a high standard of quality. Engage in meaningful discussions that contribute positively to our volunteer-driven Discord community.\n\nYour adherence to these guidelines ensures that our community remains a friendly and enjoyable space for all members. Thank you for your cooperation! 🌿", color=discord.Color.dark_embed())
        elif selected =='Wheres the documentation?':    
            embed = discord.Embed(description="**https://docs.astrobirb.dev/**", color=discord.Color.dark_embed())
        elif selected =='How do you setup the bot?':                
            embed = discord.Embed(title="<:Help:1184535847513624586> Setup Instructions", description="**1)** Set the `Admin Roles` & `Staff Roles`.\n**2)** Select A Module\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4)**Fill out the required data for that module.\n\n> **Any problems?** Head to <#1101807246079442944>!", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        embed.color = discord.Color.dark_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)
            

class Helpdesk(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpdeskDropdown())

class management(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command()
    @commands.is_owner()    
    async def addbadge(self, ctx, user: discord.Member, *, badge):
        badge = {
            'user_id': user.id,
            'badge': badge
        }
        badges.insert_one(badge)  
        await ctx.send(f"{tick} added **`{badge}`** to **@{user.display_name}**")

    @commands.command()
    @commands.is_owner()
    async def removebadge(self, ctx, user: discord.Member, *, badge):
        badge = {
            'user_id': user.id,
            'badge': badge
        }
        badges.delete_one(badge)  
        await ctx.send(f"{tick} removed **`{badge}`** to **@{user.display_name}**")
  
    @commands.command()
    @commands.is_owner()
    async def helpdesk(self, ctx):
        banner = discord.Embed(title="", color=discord.Color.dark_embed())
        banner.set_image(url="https://cdn.discordapp.com/attachments/1176591593797582848/1176595220511588382/ASTRO.png?ex=656f70b0&is=655cfbb0&hm=b126ffe5b3f45209b51660e90bc96a819fcfaeabd4bae92bcc6e3127645779c6&")

        main = discord.Embed(color=discord.Color.dark_embed(), title="<:forum:1162134180218556497> Astro Support", description="> Welcome to the support server for Astro Birb! Here you can look for you inquirys. If you can't find what you need help head to <#1101807246079442944>!")
        main.set_thumbnail(url="https://cdn.discordapp.com/icons/1092976553752789054/bf1e0138243c734664bbf9fbf8d5ae20.png?size=512")
        main.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")
        view = Helpdesk()
        await ctx.send(embeds=(banner, main), view=view)

    @commands.Cog.listener('on_thread_create')
    async def on_created_thread(self, thread: discord.Thread):
        if thread.guild.id != 1092976553752789054:
            return
        if thread.parent_id != 1101807246079442944:
            return

        await asyncio.sleep(2)
        banner = discord.Embed(title="", color=discord.Color.dark_embed())
        banner.set_image(url="https://cdn.discordapp.com/attachments/1104358043598200882/1169328494044528710/006_2.png?ex=65550106&is=65428c06&hm=392ce6de8fa7f60763c87ac8f2ee9cbad49ed5603ea6555d6be6da36fc8ce6ea&")
        embed = discord.Embed(title=f"<:forum:1162134180218556497> Astro Support", description="> Welcome to Astro Support please wait for a support resprenstive to respond!", color=discord.Color.dark_embed())
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")
        embed.set_thumbnail(url="https://cdn.discordapp.com/icons/1092976553752789054/bf1e0138243c734664bbf9fbf8d5ae20.png?size=512")
        msg = await thread.send(content='<@&1092977110412439583>', embeds=(banner, embed), allowed_mentions=discord.AllowedMentions(roles=True)) 

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel_id = 1178362100737916988 
        channel = self.client.get_channel(channel_id)
        if channel:
         webhook = discord.utils.get(await channel.webhooks(), name="Public Bot Logs")

        await webhook.send(f"<:join:1140670830792159373> Welcomed to **@{guild.name}.** I am now in {len(self.client.guilds)} guilds.", username=guild.name, avatar_url=guild.icon)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel_id = 1178362100737916988 
        channel = self.client.get_channel(channel_id)
        if channel:
         webhook = discord.utils.get(await channel.webhooks(), name="Public Bot Logs")

        await webhook.send(f"<:leave:1140670848664096789> Farewell, **@{guild.name}.** I am now in {len(self.client.guilds)} guilds.", username=guild.name, avatar_url=guild.icon)
     

async def setup(client: commands.Bot) -> None:
    await client.add_cog(management(client))     
