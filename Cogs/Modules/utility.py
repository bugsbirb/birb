import discord
from discord.ext import commands
from discord.ext.commands import Context, clean_content
import random
from datetime import datetime
from typing import Union, Optional
from typing import Literal
from pymongo import MongoClient
import typing
import os
import dotenv
from dotenv import load_dotenv
from emojis import *
MONGO_URL = os.getenv('MONGO_URL')
mongo = MongoClient(MONGO_URL)
db = mongo['astro']
badges = db['User Badges']
modules = db['Modules']



class SetupGuide(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Basic Settings", emoji="<:Help:1184535847513624586>"),
            discord.SelectOption(label="Message Quota", emoji="<:Messages:1148610048151523339>"),
            discord.SelectOption(label="Modmail", emoji="<:Mail:1162134038614650901>"),
            discord.SelectOption(label="Forums", emoji="<:forum:1162134180218556497>"),
            discord.SelectOption(label="Tags", emoji="<:tag:1162134250414415922>"),
            discord.SelectOption(label="Connection Roles", value="Connection Roles", emoji="<:Role:1162074735803387944>"), 
            discord.SelectOption(label="Infractions", emoji="<:Remove:1162134605885870180>"),
            discord.SelectOption(label="Promotions", emoji="<:Promote:1162134864594735315>"),
            discord.SelectOption(label="LOA", emoji="<:LOA:1164969910238203995>"),
            discord.SelectOption(label="Staff Feedback", emoji="<:Rate:1162135093129785364>"),         
            discord.SelectOption(label="Partnerships", emoji="<:Partner:1162135285031772300>"),   
            discord.SelectOption(label="Applications Results", emoji="<:ApplicationFeedback:1178754449125167254>"), 
            discord.SelectOption(label="Suspensions", emoji="<:Suspensions:1167093139845165229>"),
        ]
        super().__init__(placeholder="Setup Guides", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)           
        category = self.values[0]
        if category == 'Basic Settings':
            embed = discord.Embed(title="<:Help:1184535847513624586> Basic Settings Instructions", description="**1)** Set the `Admin Roles` & `Staff Roles`.\n**2)** Select A Module\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4) **Fill out the required data for that module.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        elif category =='Message Quota':    
            embed = discord.Embed(title="<:Help:1184535847513624586> Message Quota Instructions", description="**1)** Run `/config` \n**2)** Select the `message quota` module on `Config Menu`\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4)**Set the message quota amount.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        elif category == 'Modmail':
            embed = discord.Embed(title="<:Help:1184535847513624586> Modmail Instructions", description="**1)** Run `/modmail config` \n**2)** Fill the `category` argurement this is the category where the modmail channels will be created.\n**3)** Now dm the bot and test it out.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)            
        elif category == 'Forums':
            embed = discord.Embed(title="<:Help:1184535847513624586> Forums Instructions", description="**1)** Run `/forums config` \n**2)** Enable the module using the `Option` argurement. \n**3)** Create your desired embed using the categories or turn of the embed completely and just make it ping.\n**4)** Now test it go to your forum channel and create a forum and it'll send your embed/message", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)       
        elif category == 'Tags':
            embed = discord.Embed(title="<:Help:1184535847513624586> Tags Instructions", description="**1)** Run /config \n**2)** Select the `Tags` module on `Config Menu`\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4)** Run /tag create (make sure you have the `admin role`)", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)             
        elif category == 'Infractions':
            embed = discord.Embed(title="<:Help:1184535847513624586> Infractions Instructions", description="**1)** Run `/config` \n**2)** Select the `Infractions` module on `Config Menu`\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4)** Set the infractions channel.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)                         
        elif category == 'Promotions':
            embed = discord.Embed(title="<:Help:1184535847513624586> Promotions Instructions", description="**1)** Run `/config` \n**2)** Select the `Promotions` module on `Config Menu`\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4)** Set the promotions channel.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)                                              
        elif category == 'LOA':
            embed = discord.Embed(title="<:Help:1184535847513624586> LOAs Instructions", description="**1)** Run `/config` \n**2)** Select the `LOA` module on `Config Menu`\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4)** Select the LOA channel.\n**5)** Set the loa role this will be the role given once someone is on LOA.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)    
        elif category == 'Staff Feedback':
            embed = discord.Embed(title="<:Help:1184535847513624586> Staff Feedback Instructions", description="**1)** Run `/config` \n**2)** Select the `Staff Feedback` module on `Config Menu`\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4)** Set the Staff Feedback channel.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)         
        elif category == 'Partnerships':
            embed = discord.Embed(title="<:Help:1184535847513624586> Partnerships Instructions", description="**1)** Run `/config` \n**2)** Select the `Partnerships` module on `Config Menu`\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4)** Set the Partnerships channel.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)            
        elif category == 'Applications Results':
            embed = discord.Embed(title="<:Help:1184535847513624586> Applications Results Instructions", description="**1)** Run `/config` \n**2)** Select the `Partnerships` module on `Config Menu`\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4)** Set the Partnerships channel.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon) 
        elif category == 'Suspensions':
            embed = discord.Embed(title="<:Help:1184535847513624586> Suspensions Instructions", description="**1)** Run `/config` \n**2)** Select the `Suspensions` module on `Config Menu`\n**3)** On `Module Toggle` press enabled which will enable the module.", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon) 
        elif category == 'Connection Roles':
            embed = discord.Embed(title="<:Help:1184535847513624586> Connection Roles Instructions", description="**1)** Run /config \n**2)** Select the `Connection Roles` module on `Config Menu`\n**3)** On `Module Toggle` press enabled which will enable the module.\n**4)** Run /connectionrole add (make sure you have `Manage Roles` permission)`)", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=interaction.guild.icon)
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)   


        await interaction.response.edit_message(embed=embed)












class HelpMenu(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Message Quota", value="Message Quota", emoji="<:Messages:1148610048151523339>"),
            discord.SelectOption(label="Modmail", value="Modmail", emoji="<:Mail:1162134038614650901>"),
            discord.SelectOption(label="Forums", value="Forums", emoji="<:forum:1162134180218556497>"),
            discord.SelectOption(label="Tags", value="Tags", emoji="<:tag:1162134250414415922>"),
            discord.SelectOption(label="Infractions", value="Infractions", emoji="<:Remove:1162134605885870180>"),
            discord.SelectOption(label="Connection Roles", value="Connection Roles", emoji="<:Role:1162074735803387944>"), 
            discord.SelectOption(label="Staff List", value="Staff List", emoji="<:List:1179470251860185159>"),                   
            discord.SelectOption(label="Suspensions", value="Suspensions", emoji="<:Suspensions:1167093139845165229>"),
            discord.SelectOption(label="Applications Results", value="Applications Results", emoji="<:ApplicationFeedback:1178754449125167254>"),                        
            discord.SelectOption(label="Promotions", value="Promotions", emoji="<:Promote:1162134864594735315>"),
            discord.SelectOption(label="Configuration", value="Configuration", emoji="<:Setting:1154092651193323661>"),
            discord.SelectOption(label="Utility", value="Utility", emoji="<:Folder:1148813584957194250>"),
            discord.SelectOption(label="LOA", value="LOA", emoji="<:LOA:1164969910238203995>"),
            discord.SelectOption(label="Staff Feedback", value="Staff Feedback", emoji="<:Rate:1162135093129785364>"),            
            discord.SelectOption(label="Partnerships", value="Partnerships", emoji="<:Partner:1162135285031772300>")               
        ]
        super().__init__(placeholder="Help Categories", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)          
        category = self.values[0]
        embed = discord.Embed(title="", description="", color=discord.Color.dark_embed())
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)

        if category == 'Modmail':
            embed.title = "Modmail Module"
            embed.description = "The Modmail module is a system for handling private messages sent by server members. It allows staff members to respond to user queries, feedback, or issues privately without cluttering the main chat channels. With this module, you can efficiently manage and respond to user inquiries, ensuring a smooth and organized support experience for your server members."
            embed.add_field(name="Commands", value="* /modmail reply\n* /modmail close\n* /modmail config")
        elif category == 'Forums':
            embed.title = "Forums Utils Module"
            embed.description = "This module provides commands for managing forums within your server & on forum creation embeds."
            embed.add_field(name="Commands", value="* /forums unlock\n* /forums lock\n* /forums archive\n* /forums config")
        elif category == 'Tags':
            embed.title = "Tags Module"
            embed.description = "The Tags Module allows you to create, manage, and use custom text-based tags within your server. Tags are short snippets of text that can be easily retrieved and sent in chat. This module enhances communication and enables you to create quick responses or share information efficiently."
            embed.add_field(name="Commands", value="* /tags send\n* /tags info\n* /tags delete\n* /tags all")
        elif category == 'Infractions':
            embed.title = "Infractions Module"
            embed.description = "The Infractions Module is a powerful tool for managing staff discipline within your server. It offers a range of disciplinary actions, including 'Termination,' 'Demotion,' 'Warnings,' 'Verbal Warning,' and 'Activity Notice.' With these options, you can effectively address various staff-related issues and maintain a harmonious server environment."
            embed.add_field(name="Commands", value="* /infract\n* /infractions\n* /infraction void\n* /admin panel")
        elif category == 'Suspensions':
            embed.title = "Suspensions Module"
            embed.description = "Manage staff suspensions with ease. This module allows authorized users to suspend staff members for a specified duration, optionally removing their roles during the suspension. It also handles the automatic removal of suspensions when the duration expires and restoration of roles to the suspended staff members."
            embed.add_field(name="Commands", value="* /suspend\n* /suspension manage\n* /suspension active")
        elif category == 'Promotions':
            embed.title = "Promotions Module"
            embed.description = "The Promotion module is designed to recognize and reward exceptional staff members. It provides a straightforward way to promote active and highly skilled staff members, acknowledging their contributions and dedication to your server."
            embed.add_field(name="Commands", value="* /promote\n* /admin panel")
        elif category == 'Configuration':
            embed.title = "Configuration"
            embed.description = "The Configuration module allows you to customize the bot to meet your server's specific needs. You can configure Permissions, and Channels to tailor the bot's behavior to your server's requirements."
            embed.add_field(name="Commands", value="* /config\n* /modmail config\n* /forums config")
        elif category == 'Utility':
            embed.title = "Utilities"
            embed.description = "The Utility commands module consists of commands unrelated to the bot itself. These commands are designed to provide various helpful functionalities for your server, enhancing its overall utility and convenience."
            embed.add_field(name="Commands", value="* /user\n* /server\n* /ping\n* /help")
        elif category == 'LOA':
            embed.title = "LOA Module"
            embed.description = "The LOA (Leave of Absence) Module simplifies LOA requests in your Discord server. Members can easily request time off with a specified duration and reason. Server Admins can efficiently manage these requests and track active LOAs. When LOAs end, notifications ensure everyone is informed. A streamlined solution for a well-organized server."
            embed.add_field(name="Commands", value="* /loa request\n* /admin panel\n* /loa active")                        
        elif category == 'Staff Feedback':
            embed.title = "Staff Feedback Module"
            embed.description = "This module facilitates the process of providing feedback and ratings for staff members. Users can use the commands within this module to share their feedback and experiences with the staff, helping to maintain a positive and efficient community environment."
            embed.add_field(name="Commands", value="* /staff feedback\n* /staff rating")                
        elif category == 'Partnerships':
            embed.title = "Partnerships Module"
            embed.description = "Log partnerships, terminate partnerships, and view partnerships."
            embed.add_field(name="Commands", value="* /partnership log\n* /partnership all\n* /partnership terminate")               
        elif category == 'Message Quota':
            embed.title = "Message Quota Module"
            embed.description = "If you servers staff team has a message quota this feature is extremely helpful for tracking it."
            embed.add_field(name="Commands", value="* /staff leaderboard\n* /staff manage\n* /staff messages")   
        elif category == 'Connection Roles':
            embed.title = "Connection Roles Module"
            embed.description = "The connection roles module is a module where if the parent role is given to a member it also gives the child role to the member."
            embed.add_field(name="Commands", value="* /connectionrole add\n* /connectionrole remove\n* /connectionrole list")   

        elif category == 'Applications Results':
            embed.title = "Application Results Module"
            embed.description = """
❓ **How does this work?**
* **Application Results Module.** is a module that automatically assigns roles to applicants after passing based on your application results configuration settings. It also logs a application result in a channel of your choosing.
"""
            embed.add_field(name="Commands", value="* /application results")    


        elif category == 'Staff List':
            embed.title = "Staff List Module"
            embed.description = """
❓ **How does this work?**
* **Roles.** It uses the staff roles & admin roles from config.
* **Role Hierarchy Sorting.** It considers the role hierarchy, sorting roles based on their positions to ensure an accurate representation of the staff list.
* **Hoisted Roles.** It selects hoisted roles, ensuring that only roles marked as hoisted are included in the staff list.
"""
            embed.add_field(name="Commands", value="* /stafflist")               
        else:
            embed.title = "Error"
            embed.description = "The specified category could not be found, our team has been notified."
            print("Category not found in utility.py.")

        await interaction.response.edit_message(embed=embed)
class Help(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.add_item(HelpMenu(self.author))
        self.add_item(SetupGuide(self.author))


class Utility(commands.Cog):
    def __init__(self, client):
        self.client = client
        client.launch_time = datetime.now()    
        self.client.help_command = None

    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return True
     if modulesdata['Utility'] == True:   
        return True
     else:
        return False


    def check_database_connection(self):
        try:

            db.command("ping")
            return "Connected"
        except Exception as e:
            print(f"Error interacting with the database: {e}")
            return "Not Connected"


    @commands.hybrid_command(aliases=["serverinfo"])
    async def server(self, ctx):
        """ Check info about current server """        
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the **utilities** module is currently disabled.")
         return          

        if ctx.invoked_subcommand is None:
            find_bots = sum(1 for member in ctx.guild.members if member.bot)
            guild = ctx.guild
            text = ctx.guild.text_channels
            voice = ctx.guild.voice_channels
            total_members = len(ctx.guild.members)
            human_members = sum(1 for member in ctx.guild.members if not member.bot)
            embed = discord.Embed(title=f"**{ctx.guild.name}** in a nutshell", description=f"* **Owner:** {guild.owner.mention}\n* **Guild:** {guild.name}\n* **Guild ID:** {guild.id}\n* **Created:** <t:{guild.created_at.timestamp():.0f}:D> (<t:{guild.created_at.timestamp():.0f}:R>)", color=0x2b2d31)
            embed.add_field(name="Channels", value=f"* **Categories:** {len(ctx.guild.categories)}\n* **Text:** {len(text)}\n* **Forums:** {len(ctx.guild.forums)}\n* **Voice:** {len(voice)}", inline=True)
            embed.add_field(name="Stats", value=f"* **Total Members:** {total_members}\n* **Members:** {human_members}\n* **Bots:** {find_bots}\n* **Boosts:** {ctx.guild.premium_subscription_count} (Level: {ctx.guild.premium_tier})\n* **Total Roles:** {len(ctx.guild.roles)}", inline=True)         
            embed.add_field(name="Security", value=f"* **Verification Level:** {str(ctx.guild.verification_level).capitalize()}\n* **Content Filter:** `{str(ctx.guild.explicit_content_filter).capitalize()}`")
            embed.set_thumbnail(url=ctx.guild.icon)
            embed.set_author(name=f"{ctx.guild.owner}'s creation", icon_url=ctx.guild.owner.display_avatar)
            await ctx.send(embed=embed)
        

    @commands.hybrid_command()
    async def user(self, ctx, user: Optional[discord.Member] = None):
        """Displays users information"""        
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the **utilities** module is currently disabled.")
         return            

        if user is None:
            user = ctx.author
        user_badges = badges.find({'user_id': user.id})            
        badge_values = ""
        for badge_data in user_badges:
         badge = badge_data['badge']
         badge_values += f"{badge}\n"
      
        embed = discord.Embed(title=f"@{user.display_name}", description=f"{badge_values}", color=0x2b2d31)
        embed.set_thumbnail(url=user.display_avatar.url)    
        embed.add_field(name='**Profile**', value=f"* **User:** {user.mention}\n* **Display:** {user.display_name}\n* **ID:** {user.id}\n* **Join:** <t:{int(user.joined_at.timestamp())}:F>\n* **Created:** <t:{int(user.created_at.timestamp())}:F>", inline=False)
        user_roles = " ".join([role.mention for role in reversed(user.roles) if role != ctx.guild.default_role][:20])
        embed.add_field(name="**Roles**", value=user_roles, inline=False)        
        await ctx.send(embed=embed)


    @commands.hybrid_command(description="Check the bots latency & uptime")
    async def ping(self, ctx):
        server_name = ctx.guild.name
        server_icon = ctx.guild.icon
        discord_latency = self.client.latency * 1000
        discord_latency_message = f"**Latency:** {discord_latency:.0f}ms"
        database_status = self.check_database_connection()
        embed = discord.Embed(title="<:Network:1184525553294905444> Network Information", description=f"{discord_latency_message}\n**Database:** {database_status}\n**Uptime:** <t:{int(self.client.launch_time.timestamp())}:R>", color=0x2b2d31)
        embed.set_author(name=server_name, icon_url=server_icon)
        embed.set_thumbnail(url=ctx.guild.icon)
        await ctx.send(embed=embed)        
        


    @commands.hybrid_command(description="Displays all the commands.")
    async def help(self, ctx):         
     embed = discord.Embed(title="**Astro Help**", color=discord.Color.dark_embed())
     embed.description = "Welcome to the **Astro Birb** help menu. You can select a category from the dropdown below to get information about different modules and commands."
     embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
     embed.add_field(name="**Command Prefix**", value="`/`")
     embed.add_field(name="**Support Links**", value="[**Join our support server**](https://discord.gg/Pz2FzUqZWe) for assistance and updates.\n[**Read the documentation**](https://docs.astrobirb.dev) for some extra help.")     
     view = Help(ctx.author)

     await ctx.send(embed=embed, view=view)


    @commands.hybrid_command(description="Get support from the support server")
    async def support(self, ctx):
        view = Support()
        bot_user = self.client.user
        embed = discord.Embed(title="Support Server", description="Having bot issues? Join our support server and our team will help you.", color=0x2b2d31)
        embed.set_thumbnail(url=bot_user.avatar.url)
        await ctx.send(embed=embed, view=view)
       

    @commands.command(aliases=["joinme", "join", "botinvite"])
    async def invite(self, ctx):
     view = invite()
     await ctx.send(view=view)


    @commands.command()
    @commands.is_owner()    
    async def operational(self, ctx):
        embed = discord.Embed(title="Astro Birb - Operational", description="Astro Birb is currently operational and online.", color=discord.Color.brand_green())
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1139907646963597423/1148682178205589534/585894182128975914.png")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()    
    async def unstable(self, ctx):
        embed = discord.Embed(title="Astro Birb - Unstable", description="Astro Birb is currently unstable.", color=discord.Color.orange())
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1139907646963597423/1148682557618147391/1140809567865933824.png")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()    
    async def downtime(self, ctx):
        embed = discord.Embed(title="Astro Birb - Offline", description="Astro Birb is currently experiencing downtime.", color=discord.Color.red())
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1139907646963597423/1148682781321330789/1140809593598005358.png")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def restarting(self, ctx):
        embed = discord.Embed(title="Astro Birb - Restarting", description="Astro Birb is currently restarting, this will take about five minutes.", color=discord.Color.orange())
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1139907646963597423/1148682557618147391/1140809567865933824.png")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        embed = discord.Embed(title="Stopping Astro Birb", description="Shutdown command was invoked", color=discord.Color.red())
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        await ctx.send(embed=embed)
        exit(0)

class invite(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = f'https://discord.com/api/oauth2/authorize?client_id=1113245569490616400&permissions=1632557853697&scope=bot%20applications.commands'
        self.add_item(discord.ui.Button(label='Invite', url=url, style=discord.ButtonStyle.blurple))

       
class Support(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = f'https://discord.gg/DhWdgfh3hN'
        self.add_item(discord.ui.Button(label='Join', url=url, style=discord.ButtonStyle.blurple))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Utility(client))        
