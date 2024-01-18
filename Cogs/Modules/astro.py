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
analytics = db['analytics']
scollection = db['staffrole']
arole = db['adminrole']
blacklists = db['blacklists']

modules = db['Modules']
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

        main = discord.Embed(color=discord.Color.dark_embed(), title="<:forum:1162134180218556497> Astro Support", description="Welcome to the support server for Astro Birb! Here, you can find answers to your inquiries. If you can't find what you need on the helpdesk, feel free to head to <#1101807246079442944> for further assistance!")
        main.set_thumbnail(url="https://cdn.discordapp.com/icons/1092976553752789054/bf1e0138243c734664bbf9fbf8d5ae20.png?size=512")
        main.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")
        view = Helpdesk()
        await ctx.send(embeds=(banner, main), view=view)


    @commands.command()
    @commands.is_owner()
    async def analytics(self, ctx):
     result = analytics.find({})

     description = ""
     for x in result:
        for key, value in x.items():
            if key != '_id':
                description += f"**{key}:** `{value}`\n"
        description += ""

     embed = discord.Embed(title="Command Analytics", description=description, color=discord.Color.dark_embed())
     embed.set_thumbnail(url=ctx.guild.icon)
     embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
     embed.set_footer(text=f"Analytics started on 14th December 2024", icon_url="https://media.discordapp.net/ephemeral-attachments/1114281227579559998/1197680763341111377/1158064756104630294.png?ex=65bc2621&is=65a9b121&hm=9e278e5e96573663fb42396dd52e56ece56ba6af59e53f9720873ca484fabf19&=&format=webp&quality=lossless")
     await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def guildinfo(self, ctx, guildid: int):
        await ctx.defer()  
        guild = await self.client.fetch_guild(guildid)
        if guild is None:
            await ctx.send(f"{no} Guild not found!")
            return
        staffroleresult = scollection.find_one({'guild_id': guild.id})
        adminroleresult = arole.find_one({'guild_id': guild.id})

        if adminroleresult:
            admin_roles_ids = adminroleresult.get('staffrole', [])
            if not isinstance(admin_roles_ids, list):
                admin_roles_ids = [admin_roles_ids]
            admin_roles_mentions = [discord.utils.get(guild.roles, id=role_id).name
                                    for role_id in admin_roles_ids if discord.utils.get(guild.roles, id=role_id) is not None]
            if not admin_roles_mentions:
                adminrolemessage = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
            else:
                adminrolemessage = ", ".join(admin_roles_mentions)
        
        if staffroleresult:
            staff_roles_ids = staffroleresult.get('staffrole', [])
            if not isinstance(staff_roles_ids, list):
                staff_roles_ids = [staff_roles_ids]
            staff_roles_mentions = [discord.utils.get(guild.roles, id=role_id).name
                                    for role_id in staff_roles_ids if discord.utils.get(guild.roles, id=role_id) is not None]
            if not staff_roles_mentions:
                staffrolemessage = "<:Error:1126526935716085810> Roles weren't found, please reconfigure."
            else:
                staffrolemessage = ", ".join(staff_roles_mentions)       

        all_servers_data = modules.find_one({'guild_id': guildid})
        print(all_servers_data)
    

        modules_info = ""
    
        if all_servers_data:
         modules_info = ""
         for module, enabled in all_servers_data.items():
          if module != '_id' and module != 'guild_id':
            modules_info += f"**{module}:** {f'{tick}' if enabled else f'{no}'}\n"
        else:
          modules_info = "No document found in the collection."


        if guild.owner is None:
            owner = "Unknown"
        else:
            owner = guild.owner.display_name
        embed = discord.Embed(title=f"{guild.name}", description=f"**Owner:** {owner}\n**Guild ID:** {guild.id}\n**Roles:** {len(guild.roles)}\n**Created:** <t:{guild.created_at.timestamp():.0f}:D>", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=guild.icon)
        if guild.banner:
         embed.set_image(url=guild.banner)
        embed.add_field(name=f"{Settings} Basic Settings", value=f"**Admin Roles:** {adminrolemessage}\n**Staff Roles:** {staffrolemessage}")
        if modules_info:
         embed.add_field(name=f"Modules", value=modules_info, inline=False)
        embed.set_author(name=guild.name, icon_url=guild.icon)

         
     
        await ctx.send(embed=embed)

        


        
        
      
        
        

async def setup(client: commands.Bot) -> None:
    await client.add_cog(management(client))     
