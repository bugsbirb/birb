import discord
from discord.ext import commands
from discord.ext.commands import Context, clean_content
import random
from datetime import datetime
from typing import Union, Optional
from typing import Literal
from pymongo import MongoClient
import typing
mongo = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = mongo['astro']
badges = db['User Badges']


class HelpMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Halloween Event", value="Halloween Event", emoji="<:candysweet:1160591383158071376>"),
            discord.SelectOption(label="Modmail", value="Modmail", emoji="<:Mail:1162134038614650901>"),
            discord.SelectOption(label="Tickets", value="Tickets", emoji="<:Tickets:1162488340671643699>"),
            discord.SelectOption(label="Forums", value="Forums", emoji="<:forum:1162134180218556497>"),
            discord.SelectOption(label="Tags", value="Tags", emoji="<:tag:1162134250414415922>"),
            discord.SelectOption(label="Infractions", value="Infractions", emoji="<:Remove:1162134605885870180>"),
            discord.SelectOption(label="Promotions", value="Promotions", emoji="<:Promote:1162134864594735315>"),
            discord.SelectOption(label="Configuration", value="Configuration", emoji="<:Setting:1154092651193323661>"),
            discord.SelectOption(label="Utility", value="Utility", emoji="<:Folder:1148813584957194250>")
        ]
        super().__init__(placeholder="Help Categories", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        embed = discord.Embed(title="", description="", color=discord.Color.dark_embed())
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)

        if category == 'Halloween Event':
            embed.title = "<:candysweet:1160591383158071376> Trick Or Treating **[Limited Time Event]**"
            embed.description = "The Halloween event is an event that lasts until the **1st Of November**. Whoever gets the most candy will win <:nitro:1160656782054658148> **Nitro Basic**. You must be in the [**Support Server**](https://discord.gg/Pz2FzUqZWe)"
            embed.add_field(name="Commands", value="* -candy basket\n* -trickortreat\n* -halloween shop")
        elif category == 'Modmail':
            embed.title = "Modmail Module [Beta]"
            embed.description = "The Modmail module is a system for handling private messages sent by server members. It allows staff members to respond to user queries, feedback, or issues privately without cluttering the main chat channels. With this module, you can efficiently manage and respond to user inquiries, ensuring a smooth and organized support experience for your server members."
            embed.add_field(name="Commands", value="* /modmail reply\n* /modmail close\n* /modmail config")
        elif category == 'Tickets':
            embed.title = "Tickets Module [Beta]"
            embed.description = "This Ticket module is a system for handling messages face to face in a private channel. It allows staff members to respond to user queries, feedback, or issues privately without cluttering the main chats."
            embed.add_field(name="Commands", value="* /tickets close\n* /tickets claim\n* /tickets config")    
        elif category == 'Forums':
            embed.title = "Forums Utils Module"
            embed.description = "This module provides commands for managing forums within your server."
            embed.add_field(name="Commands", value="* /forums unlock\n* /forums lock\n* /forums archive")
        elif category == 'Tags':
            embed.title = "Tags Module"
            embed.description = "The Tags Module allows you to create, manage, and use custom text-based tags within your server. Tags are short snippets of text that can be easily retrieved and sent in chat. This module enhances communication and enables you to create quick responses or share information efficiently."
            embed.add_field(name="Commands", value="* /tags send\n* /tags info\n* /tags delete\n* /tags all")
        elif category == 'LOA':
            embed.title = "LOA Module"
            embed.description = "The LOA module serves as a dedicated system for managing staff breaks and Leave Of Absence (LOA) requests. Staff members can easily submit LOA requests when they need to take a break, ensuring smooth staff management and workflow."
            embed.add_field(name="Commands", value="* /loa request\n* /loa view\n* /loa manage")
        elif category == 'Infractions':
            embed.title = "Infractions Module"
            embed.description = "The Infractions Module is a powerful tool for managing staff discipline within your server. It offers a range of disciplinary actions, including 'Termination,' 'Demotion,' 'Warnings,' 'Verbal Warning,' and 'Activity Notice.' With these options, you can effectively address various staff-related issues and maintain a harmonious server environment."
            embed.add_field(name="Commands", value="* /infract\n* /infractions\n* /revoke infraction")
        elif category == 'Promotions':
            embed.title = "Promotions Module"
            embed.description = "The Promotion module is designed to recognize and reward exceptional staff members. It provides a straightforward way to promote active and highly skilled staff members, acknowledging their contributions and dedication to your server."
            embed.add_field(name="Commands", value="* /promote")
        elif category == 'Configuration':
            embed.title = "Configuration"
            embed.description = "The Configuration module allows you to customize the bot to meet your server's specific needs. You can configure Anti-Ping, Permissions, and Channels to tailor the bot's behavior to your server's requirements."
            embed.add_field(name="Commands", value="* /config\n* /modmail config\n* /tickets config")
        elif category == 'Utility':
            embed.title = "Utilities"
            embed.description = "The Utility commands module consists of commands unrelated to the bot itself. These commands are designed to provide various helpful functionalities for your server, enhancing its overall utility and convenience."
            embed.add_field(name="Commands", value="* /user\n* /server\n* /ping\n* /help")
        else:
            embed.title = "Unknown Category"
            embed.description = "The specified category does not exist."

        await interaction.response.edit_message(embed=embed)
class Help(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpMenu())


class Utility(commands.Cog):
    def __init__(self, client):
        self.client = client
        client.launch_time = datetime.utcnow()    
        self.client.help_command = None




    @commands.hybrid_command(aliases=["serverinfo"])
    async def server(self, ctx):
        """ Check info about current server """
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
            embed.set_author(name=f"{ctx.guild.owner}'s creation", icon_url=ctx.guild.owner.avatar.url)
            await ctx.send(embed=embed)
        

    @commands.hybrid_command()
    async def user(self, ctx, user: Optional[discord.Member] = None):
        """Displays users information"""
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
        server_icon = ctx.guild.icon.url if ctx.guild.icon else None


        discord_latency = self.client.latency * 1000
        discord_latency_message = f"**Latency:** {discord_latency:.0f}ms"


        embed = discord.Embed(title="", description=f"* {discord_latency_message}\n* **Up Since:** <t:{int(self.client.launch_time.timestamp())}:F>", color=0x2b2d31)
        embed.set_author(name=server_name, icon_url=server_icon)
        embed.set_footer(text=f"Shard {str(ctx.guild.shard_id)} | Guild ID: {str(ctx.guild.id)}")
        await ctx.send(embed=embed)        
        


    @commands.hybrid_command(description="Displays all the commands.")
    async def help(self, ctx):
     embed = discord.Embed(title="**Astro Help**", color=discord.Color.dark_embed())
     embed.description = "Welcome to the **Astro Birb** help menu. You can select a category from the dropdown below to get information about different modules and commands."
     embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
     embed.add_field(name="**Command Prefix**", value="`/` or `-`")
     embed.add_field(name="**Support Server**", value="[**Join our support server**](https://discord.gg/Pz2FzUqZWe) for assistance and updates.")     
     view = Help()

     await ctx.send(embed=embed, view=view)


    @commands.hybrid_command(description="Get support from the support server")
    async def support(self, ctx):
        view = Support()
        bot_user = self.client.user
        embed = discord.Embed(title="Support Server", description="You having issues? Join the support server and get some help.", color=0x2b2d31)
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
        embed = discord.Embed(title="Astro Birb - Restarting", description="Astro Birb is currently restarting.", color=discord.Color.orange())
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1139907646963597423/1148682557618147391/1140809567865933824.png")
        await ctx.send(embed=embed)

class invite(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = f'https://discord.com/api/oauth2/authorize?client_id=1113245569490616400&permissions=1632557853697&scope=bot%20applications.commands'
        self.add_item(discord.ui.Button(label='Invite', url=url, style=discord.ButtonStyle.blurple))

       
class Support(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = f'https://discord.gg/eSa72HAXsY'
        self.add_item(discord.ui.Button(label='Join', url=url, style=discord.ButtonStyle.blurple))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Utility(client))        
