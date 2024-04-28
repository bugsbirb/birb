import discord
import discord
from discord.ext import commands
from discord.ext import commands
import os
from emojis import * 
import requests
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
deploy_URL = os.getenv('deploy_url')
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo['astro']
badges = db['User Badges']
analytics = db['analytics']
scollection = db['staffrole']
arole = db['adminrole']
blacklists = db['blacklists']
modules = db['Modules']
customroles = db['customroles']
modules = db['Modules']
premium = db['premium']

class management(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
 
    @commands.command()
    @commands.is_owner()
    async def addbadge(self, ctx: commands.Context, user: discord.Member, *, badge):
        badge = {
            'user_id': user.id,
            'badge': badge
        }
        await badges.insert_one(badge)
        await ctx.send(f"{tick} added **`{badge}`** to **@{user.display_name}**")

    @commands.command()
    @commands.is_owner()
    async def removebadge(self, ctx: commands.Context, user: discord.Member, *, badge):
        badge = {
            'user_id': user.id,
            'badge': badge
        }
        await badges.delete_one(badge)
        await ctx.send(f"{tick} removed **`{badge}`** to **@{user.display_name}**")

    @commands.command()
    @commands.is_owner()
    async def givepremium(self, ctx, user: discord.User):
        await premium.insert_one({'user_id': user.id})
        await ctx.send(f"{tick} I've succesfully given {user.display_name} premium!")

    @commands.command()
    @commands.is_owner()
    async def removepremium(self, ctx, user: discord.User):
        result = await premium.delete_one({'user_id': user.id})
        if result.deleted_count == 0:
            await ctx.send(f"{no} this user does not have premium.")
            return
        await ctx.send(f"{tick} I've removed premium from **@{user.display_name}**")   
         
    @commands.command()
    @commands.is_owner()
    async def analytics(self, ctx: commands.Context):
        result = await analytics.find({}).to_list(length=None)

        description = ""
        for x in result:
            for key, value in x.items():
                if key != '_id':
                    description += f"**{key}:** `{value}`\n"
            description += ""

        embed = discord.Embed(title="Command Analytics", description=description, color=discord.Color.dark_embed())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        embed.set_footer(text="Analytics started on 14th December 2024",
                         icon_url="https://media.discordapp.net/ephemeral-attachments/1114281227579559998/1197680763341111377/1158064756104630294.png?ex=65bc2621&is=65a9b121&hm=9e278e5e96573663fb42396dd52e56ece56ba6af59e53f9720873ca484fabf19&=&format=webp&quality=lossless")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def guildinfo(self, ctx: commands.Context, guildid: int):
        await ctx.defer()
        guild = await self.client.fetch_guild(guildid)
        if guild is None:
            await ctx.send(f"{no} Guild not found!")
            return
        staffroleresult = await scollection.find_one({'guild_id': guild.id})
        adminroleresult = await arole.find_one({'guild_id': guild.id})
        staffrolemessage = "Not Configured"
        adminrolemessage = "Not Configured"
        if adminroleresult:
            admin_roles_ids = adminroleresult.get('staffrole', [])
            if not isinstance(admin_roles_ids, list):
                admin_roles_ids = [admin_roles_ids]
            admin_roles_mentions = [discord.utils.get(guild.roles, id=role_id).name
                                    for role_id in admin_roles_ids if discord.utils.get(guild.roles, id=role_id) is not None]
            if not admin_roles_mentions:
                adminrolemessage = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
            else:
                adminrolemessage = ", ".join(admin_roles_mentions)

        if staffroleresult:
            staff_roles_ids = staffroleresult.get('staffrole', [])
            if not isinstance(staff_roles_ids, list):
                staff_roles_ids = [staff_roles_ids]
            staff_roles_mentions = [discord.utils.get(guild.roles, id=role_id).name
                                    for role_id in staff_roles_ids if discord.utils.get(guild.roles, id=role_id) is not None]
            if not staff_roles_mentions:
                staffrolemessage = "<:Error:1223063223910010920> Roles weren't found, please reconfigure."
            else:
                staffrolemessage = ", ".join(staff_roles_mentions)

        all_servers_data = await modules.find_one({'guild_id': guildid})
        print(all_servers_data)

        modules_info = ""

        if all_servers_data:
            modules_info = ""
            for module, enabled in all_servers_data.items():
                if module not in ('_id', 'guild_id'):
                    modules_info += f"**{module}:** {f'{tick}' if enabled else f'{no}'}\n"
        else:
            modules_info = "No document found in the collection."

        if guild.owner is None:
            owner = "Unknown"
        else:
            owner = guild.owner.display_name
            
        embed = discord.Embed(title=f"{guild.name}", description=f"**Owner:** {owner}\n**Guild ID:** {guild.id}\n**Roles:** {len(guild.roles)}\n**Created:** <t:{guild.created_at.timestamp():.0f}:D>",
                              color=discord.Color.dark_embed())
        embed.set_thumbnail(url=guild.icon)
        if guild.banner:
            embed.set_image(url=guild.banner)
        embed.add_field(name=f"{Settings} Basic Settings",
                        value=f"**Admin Roles:** {adminrolemessage}\n**Staff Roles:** {staffrolemessage}")
        if modules_info:
            embed.add_field(name="Modules", value=modules_info, inline=False)
        embed.set_author(name=guild.name, icon_url=guild.icon)

        await ctx.send(embed=embed)


        
    @commands.command()
    @commands.is_owner()
    async def deploy(self ,ctx):
        response = requests.get(deploy_URL)
        async with ctx.typing():
         if response.status_code == 200:
          print(response.text)
          await ctx.send(f"{tick} **{ctx.author.display_name},** I've succesfully deployed Astro Birb!")
         else:
             print(response.text)
        
    @commands.command()
    @commands.is_owner()
    async def reloadjsk(self ,ctx):
     await self.client.load_extension("jishaku")
     await ctx.send(f'{tick} **{ctx.author.display_name},** I\'ve succesfully reloaded Jishaku!')      
        

async def setup(client: commands.Bot) -> None:
    await client.add_cog(management(client))     
