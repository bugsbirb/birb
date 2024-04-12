import discord
from discord.ext import commands
from discord import app_commands

from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
import os
from emojis import *
from typing import Literal
MONGO_URL = os.getenv('MONGO_URL')
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo['astro']
badges = db['User Badges']
modules = db['Modules']



class SetupGuide(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(label="Basic Settings", emoji="<:Help:1184535847513624586>"),
            discord.SelectOption(label="Message Quota", emoji="<:messageup:1224722310687359106>"),
            discord.SelectOption(label="Modmail", emoji="<:Mail:1162134038614650901>"),
            discord.SelectOption(label="Forums", emoji="<:forum:1162134180218556497>"),
            discord.SelectOption(label="Tags", emoji="<:tag:1162134250414415922>"),
            discord.SelectOption(label="Connection Roles", value="Connection Roles", emoji="<:Role:1162074735803387944>"), 
            discord.SelectOption(label="Infractions", emoji="<:Remove:1162134605885870180>"),
            discord.SelectOption(label="Promotions", emoji="<:Promote:1162134864594735315>"),
            discord.SelectOption(label="LOA", emoji=f"{loa}"),
            discord.SelectOption(label="Staff Feedback", emoji="<:Rate:1162135093129785364>"),         
            discord.SelectOption(label="Partnerships", emoji="<:partnerships:1224724406144733224>"),   
            discord.SelectOption(label="Applications Results", emoji="<:Application:1224722901328986183>"), 
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













class Help(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.add_item(SetupGuide(self.author))


class Utility(commands.Cog):
    def __init__(self, client):
        self.client = client
        client.launch_time = datetime.now()    
        self.client.help_command = None

    async def modulecheck(self, ctx): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return True
     if modulesdata['Utility'] is True:   
        return True
     else:
        return False


    async def check_database_connection(self):
        try:

            await db.command("ping")
            return "Connected"
        except Exception as e:
            print(f"Error interacting with the database: {e}")
            return "Not Connected"


    @commands.hybrid_command()
    async def server(self, ctx: commands.Context):
        """ Check info about current server """        

        find_bots = sum(1 for member in ctx.guild.members if member.bot)
        guild = ctx.guild
        text = ctx.guild.text_channels
        voice = ctx.guild.voice_channels
        total_members = len(ctx.guild.members)
        human_members = sum(1 for member in ctx.guild.members if not member.bot)
        embed = discord.Embed(title=f"**{ctx.guild.name}** in a nutshell", description=f"<:crown:1226668264260894832> **Owner:** {guild.owner.mention}\n<:link:1226672596284866631> **Guild:** {guild.name}\n<:ID:1226671706022740058> **Guild ID:** {guild.id}\n<:Member:1226674150463111299> **Members** {guild.member_count}\n<:pin:1226671966413389864> **Created:** <t:{guild.created_at.timestamp():.0f}:D> (<t:{guild.created_at.timestamp():.0f}:R>)\n<:Discord_channel:1226674545050783817> **Channels:** {len(ctx.guild.channels)}\n<:Role:1223077527984144474> **Roles:** {len(ctx.guild.roles)}" , color=0x2b2d31)
        embed.add_field(name="<:tag:1162134250414415922> Channels", value=f"* **Categories:** {len(ctx.guild.categories)}\n* **Text:** {len(text)}\n* **Forums:** {len(ctx.guild.forums)}\n* **Voice:** {len(voice)}", inline=True)
        embed.add_field(name="<:poll:1192866397043306586> Stats", value=f"* **Total Members:** {total_members}\n* **Members:** {human_members}\n* **Bots:** {find_bots}\n* **Boosts:** {ctx.guild.premium_subscription_count} (Level {ctx.guild.premium_tier})\n* **Total Roles:** {len(ctx.guild.roles)}", inline=True)         
        if str(ctx.guild.explicit_content_filter).capitalize() == 'All_members':
            content_filter = 'Everyone'
        else:
            content_filter = {str(ctx.guild.explicit_content_filter).capitalize()}    
        embed.add_field(name="<:Promotion:1162134864594735315> Security", value=f"* **Verifiy Level:** {str(ctx.guild.verification_level).capitalize()}\n* **Content Filter:** `{content_filter}`")
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=f"{ctx.guild.owner}'s creation", icon_url=ctx.guild.owner.display_avatar)
        
        await ctx.send(embed=embed)
        
    
        
    @app_commands.command(description="View someones avatar")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        if user is None:
            user = interaction.user
        embed = discord.Embed(title=f"{(user.name).capitalize()}'s Avatar", color=discord.Color.dark_embed())
        embed.set_image(url=user.display_avatar)
        await interaction.response.send_message(embed=embed)



    @app_commands.command()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def user(self, interaction: discord.Interaction, user: Optional[discord.User] = None) -> None:
        """Displays users information"""        
        if user is None:
            user = interaction.user
        user_badges = badges.find({'user_id': user.id})            
        badge_values = ""
   
        public_flags_emojis = {
            "staff": "<:Staff:1221449338744602655>",
            "partner": "<:blurple_partner:1221449485792841791>",
            "hypesquad": "<:hypesquad_events:1221444926995169361>",
            "bug_hunter": "<:bug_hunter_2:1221449642328457237>",
            "hypesquad_bravery": "<:hypesquad_bravery:1221444906409660529>",
            "hypesquad_brilliance": "<:hypesquad_brilliance:1221444915515490334>",
            "hypesquad_balance": "<:hypesquad_balance:1221444890827817090>",
            "early_supporter": "<:early:1221444939733536868>",
            "verified_bot": "<:Twitter_VerifiedBadge:1221450046625812591>",
            "verified_developer": "<:verified:1221450133997097052>",
            "active_developer": "<:Active_Developer_Badge:1221444993873477714>"
        }
        badgecount = 0
        async for badge_data in user_badges:
         badge = badge_data['badge']
         badge_values += f"{badge}\n"
         badgecount += 1 
        member = None 
        if interaction.guild: 
         try:
          member = await interaction.guild.fetch_member(user.id)
         except discord.HTTPException:
            member = None 
        userFlags = user.public_flags.all()
        for flag in userFlags:
            flag_name = flag.name
            if flag_name in public_flags_emojis:
                flag_name2 = str(flag_name).replace("Userflags.", "").replace("_", " ").title()
                badge_values += f"{public_flags_emojis[flag_name]} {flag_name2}\n"
                badgecount += 1 
          
        if not member:
            embed = discord.Embed(title=f"@{user.display_name}", description=f"", color=0x2b2d31)
            embed.set_thumbnail(url=user.display_avatar.url)    
            if userFlags or badge_values:
                embed.add_field(name=f'Flags [{badgecount}]', value=f"{badge_values}")
            embed.add_field(name='**Profile**', value=f"* **User:** {user.mention}\n* **Display:** {user.display_name}\n* **ID:** {user.id}\n* **Created:** <t:{int(user.created_at.timestamp())}:F>", inline=False)
            await interaction.response.send_message(embed=embed)
            return
        embed = discord.Embed(title=f"@{user.display_name}", description=f"", color=discord.Color.dark_embed())
        if userFlags or badge_values:
                embed.add_field(name=f'Flags [{badgecount}]', value=f"{badge_values}") 
        embed.set_thumbnail(url=user.display_avatar.url)    
        embed.add_field(name='**Profile**', value=f"* **User:** {user.mention}\n* **Display:** {user.display_name}\n* **ID:** {user.id}\n* **Join:** <t:{int(user.joined_at.timestamp())}:F>\n* **Created:** <t:{int(user.created_at.timestamp())}:F>", inline=False)
        user_roles = " ".join([role.mention for role in reversed(user.roles) if role != interaction.guild.default_role][:20])
        rolecount = len(user.roles) - 1
        embed.add_field(name=f"**Roles** [{rolecount}]", value=user_roles, inline=False)        
        await interaction.response.send_message(embed=embed)

    async def fetch_birb_image(self):
        birb_api_url = "https://api.alexflipnote.dev/birb"
        async with aiohttp.ClientSession() as session:
            async with session.get(birb_api_url) as response:
                response.raise_for_status()
                data = await response.json()
                return data["file"]

    @app_commands.command(name='birb', description="Get silly birb photo")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def birb(self, interaction: discord.Interaction):
        try:
            birb_image_url = await self.fetch_birb_image()

            embed = discord.Embed(color=discord.Color.dark_embed())
            embed.set_image(url=birb_image_url)
            await interaction.response.send_message(embed=embed)

        except aiohttp.ClientError as e:
            await interaction.response.send_message(f"{crisis} {interaction.user.mention}, I couldn't get a birb image for you :c\n**Error:** `{e}`", allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name='ping',description="Check the bots latency & uptime")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ping(self, interaction: discord.Interaction):
        server_name = "Astro Birb"
        server_icon = self.client.user.display_avatar
        discord_latency = self.client.latency * 1000
        discord_latency_message = f"**Latency:** {discord_latency:.0f}ms"
        database_status = await self.check_database_connection()
        embed = discord.Embed(title="<:Network:1184525553294905444> Network Information", description=f"{discord_latency_message}\n**Database:** {database_status}\n**Uptime:** <t:{int(self.client.launch_time.timestamp())}:R>", color=0x2b2d31)

        embed.set_author(name=server_name, icon_url=server_icon)
        embed.set_thumbnail(url=server_icon)
        if interaction.guild:
         await interaction.response.send_message(embed=embed, view=NetWorkPage(self.client, interaction.user))    
        else:
            await interaction.response.send_message(embed=embed)
        

 
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def divider(self, ctx: commands.Context, * ,rolename):
        guild = ctx.guild
        if len(rolename) > 100:
            await ctx.send("Role name is too long. Please provide a name with 100 characters or fewer.")
            return

        rolewidth = 19
        divider_text = "\u200b" + "​ " * ((rolewidth - len(rolename)) // 2) + rolename + "​ " * ((rolewidth - len(rolename)) // 2) + "\u200b"
        try:
            role = await guild.create_role(name=divider_text)
            await ctx.send(f"Role divider created: {role.name}")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to create role divider: {e}")



    
        
      

    @commands.hybrid_command(description="Get help with Astro Birb.")
    async def help(self, ctx: commands.Context):         
     embed = discord.Embed(title="**Astro Help**", color=discord.Color.dark_embed())
     embed.description = "Welcome to the **Astro Birb** help menu. You can select a category from the dropdown below to get setup guides."
     embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
     embed.add_field(name="**Command Prefix**", value="`/`")
     embed.add_field(name="**Support Links**", value="[**Join our support server**](https://discord.gg/Pz2FzUqZWe) for assistance and updates.\n[**Read the documentation**](https://docs.astrobirb.dev) for some extra help.")     
     view = Help(ctx.author)
     await ctx.send(embed=embed, view=view)


    @app_commands.command(description="Get support from the support server")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)    
    async def support(self, interaction: discord.Interaction):
        view = Support()
        bot_user = self.client.user
        embed = discord.Embed(
        title="🚀 Astro Support",
        description="Encountering issues with Astro Birb? Our support team is here to help! Join our official support server using the link below.",
        color=0x2b2d31
    )
        embed.set_thumbnail(url=bot_user.avatar.url)
        embed.set_author(name=bot_user.display_name, icon_url=bot_user.display_avatar)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(description="Invite Astro Birb to your server")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)     
    async def invite(self, interaction: discord.Interaction):
     view = invite()
     await interaction.response.send_message(view=view)


    @app_commands.command(name='vote',description="❤️ Support Astro Birb!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def vote(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🚀 Support Astro Birb", description="Hi there! If you enjoy using **Astro Birb**, consider upvoting it on the following platforms to help us grow and reach more servers. Your support means a lot! 🌟", color=discord.Color.dark_embed())
        button = discord.ui.Button(label="Upvote", url="https://top.gg/bot/1113245569490616400/vote", emoji="<:topgg:1206665848408776795>", style=discord.ButtonStyle.blurple)
        button2 = discord.ui.Button(label="Upvote", url="https://wumpus.store/bot/1113245569490616400/vote", emoji="<:wumpus_store:1206665807011258409>", style=discord.ButtonStyle.blurple)
        button3 = discord.ui.Button(label="Upvote", url="https://discords.com/bots/bot/1113245569490616400/vote", emoji="<:Discords_noBG:1206666304107446352>", style=discord.ButtonStyle.blurple)
        embed.set_thumbnail(url=self.client.user.display_avatar)
        embed.set_author(name=self.client.user.display_name, icon_url=self.client.user.display_avatar)
        view = discord.ui.View()
        view.add_item(button)
        view.add_item(button2)
        view.add_item(button3)
        await interaction.response.send_message(embed=embed
                       , view=view)
   
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

class NetWorkPage(discord.ui.View):
    def __init__(self, client, author):
        super().__init__(timeout=1028)
        self.client = client
        self.author = author

    @discord.ui.button(
        label="",
        style=discord.ButtonStyle.grey,
        emoji=f"<:chevronleft:1220806425140531321>",  
        disabled=True)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
     pass

    @discord.ui.button(
        label="Network",
        style=discord.ButtonStyle.blurple,
        emoji="<:Network:1184525553294905444>")
    async def network(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="")

    @discord.ui.button(
        label="",
        style=discord.ButtonStyle.grey,
        emoji=f"<:chevronright:1220806430010118175>"  )
    async def Right(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)    
        server_name = "Astro Birb"
        server_icon = self.client.user.display_avatar
        embed = discord.Embed(title="Sharding Information", color=discord.Color.dark_embed())
        if interaction.guild:
         for shard_id, shard_instance in self.client.shards.items():
            shard_info = f"> **Latency:** {shard_instance.latency * 1000:.0f} ms\n"  
            guild_count = sum(1 for guild in self.client.guilds if guild.shard_id == shard_id)
            shard_info += f"> **Guilds:** {guild_count}\n" 
            urguild = ""
            if shard_id == interaction.guild.shard_id:
                urguild = "(This Guild)"
            embed.add_field(name=f"<:pingpong:1227283504501358715> Shard {shard_id} {urguild}", value=shard_info, inline=False)        
        embed.set_author(name=server_name, icon_url=server_icon)
        embed.set_thumbnail(url=server_icon)
        await interaction.response.edit_message(
            embed=embed,
            view=ShardsPage(self.client, self.author))


class ShardsPage(discord.ui.View):
    def __init__(self, client, author):
        super().__init__()
        self.client = client
        self.author = author

    async def check_database_connection(self):
        try:

            await db.command("ping")
            return "Connected"
        except Exception as e:
            print(f"Error interacting with the database: {e}")
            return "Not Connected"
        
    @discord.ui.button(
        label="",
        style=discord.ButtonStyle.grey,
        emoji=f"<:chevronleft:1220806425140531321>",  
        disabled=False)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button,):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.global_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)        
        server_name = "Astro Birb"
        server_icon = self.client.user.display_avatar
        discord_latency = self.client.latency * 1000
        discord_latency_message = f"**Latency:** {discord_latency:.0f}ms"
        database_status = await self.check_database_connection()
        embed = discord.Embed(title="<:Network:1184525553294905444> Network Information", description=f"{discord_latency_message}\n**Database:** {database_status}\n**Uptime:** <t:{int(self.client.launch_time.timestamp())}:R>", color=0x2b2d31)

        embed.set_author(name=server_name, icon_url=server_icon)
        embed.set_thumbnail(url=server_icon)
        await interaction.response.edit_message(embed=embed, view=NetWorkPage(self.client, self.author)) 

    @discord.ui.button(
        label="Shards",
        style=discord.ButtonStyle.blurple,
        emoji=f"<:pingpong:1227283504501358715>")
    async def shards(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="")

    @discord.ui.button(
        label="",
        style=discord.ButtonStyle.grey,
        emoji=f"<:chevronright:1220806430010118175>", disabled=True)
    async def Right(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass


class invite(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = f'https://discord.com/api/oauth2/authorize?client_id=1113245569490616400&permissions=1632557853697&scope=bot%20applications.commands'
        self.add_item(discord.ui.Button(label='Invite', url=url, style=discord.ButtonStyle.blurple, emoji="<:link:1206670134064717904>"))


       
class Support(discord.ui.View):
    def __init__(self):
        super().__init__()
        url = f'https://discord.gg/DhWdgfh3hN'
        self.add_item(discord.ui.Button(label='Join', url=url, style=discord.ButtonStyle.blurple, emoji="<:link:1206670134064717904>"))
        self.add_item(discord.ui.Button(label='Documentation', url="https://docs.astrobirb.dev", style=discord.ButtonStyle.blurple, emoji="📚"))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Utility(client))        
