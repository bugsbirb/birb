import discord
import platform
import sys
import discord.ext
from discord.ext import commands
from urllib.parse import quote_plus
from discord import app_commands
import discord
import datetime
from discord.ext import commands, tasks

from typing import Optional
import Paginator
from cogs.infractions import *
import sentry_sdk
import asyncio
from cogs.loa import *
import os
from dotenv import load_dotenv
from jishaku import Jishaku
import jishaku
from cogs.astro import * 

load_dotenv()
PREFIX = os.getenv('PREFIX')
TOKEN = os.getenv('TOKEN')
MONGO_URL = os.getenv('MONGO_URL')
SENTRY_URL = os.getenv('SENTRY_URL')
#quota
mongo = MongoClient('mongodb://bugsbirt:deezbird2768@172.93.103.8:55199/?authMechanism=SCRAM-SHA-256&authSource=admin')


db2 = mongo['quotab']
scollection2 = db2['staffrole']
mccollection = db2["messages"]

MONGO_URL = os.getenv('MONGO_URL')
astro = MongoClient(MONGO_URL)
db = astro['astro']
modules = db['Modules']

sentry_sdk.init(
    dsn=SENTRY_URL,

    traces_sample_rate=1.0,

    profiles_sample_rate=1.0,
)







class client(commands.Bot):
    def __init__(self):
        intents = discord.Intents().all()
        super().__init__(command_prefix=commands.when_mentioned_or(PREFIX), intents=intents)
        self.client = client
        self.cogslist = ["cogs.stafflist", "cogs.applicationresults", "cogs.ConfigurationFolder.Configuration2", "cogs.quota", "cogs.consent", "cogs.suspension", "cogs.adminpanel","cogs.partnerships","cogs.stafffeedback","cogs.loa", "cogs.astro", "cogs.modmail", "cogs.forumutils", "cogs.tags" ,"cogs.botinfo", "cogs.infractions", "cogs.utility", "cogs.reports",  "cogs.promotions"]




    async def load_jishaku(self):
        await self.wait_until_ready()
        await self.load_extension('jishaku')        
        print("Jishaku Loaded")






    async def setup_hook(self):
        self.loop.create_task(self.load_jishaku()) 
        self.add_view(Helpdesk())



        for ext in self.cogslist:
            await self.load_extension(ext)
            print(f"Cog {ext} loaded")


    async def on_ready(self):
        prfx = (time.strftime("%H:%M:%S GMT", time.gmtime()))
        print(prfx + " Logged in as " + self.user.name)
        print(prfx + " Bot ID " + str(self.user.id))
        print(prfx + " Discord Version " +  discord.__version__)
        print(prfx + " Python Version " + str(platform.python_version()))
        synced = await self.tree.sync()
        print(prfx + " Slash CMDs Synced " + str(len(synced)) + " Commands")
        print(prfx + " Bot is in " + str(len(self.guilds)) + " servers")
        update_channel_name.start()
        
        



    
    async def on_connect(self):
        activity2 = discord.CustomActivity(name=f"✨ 20k+ users!")

        print("Connected to Discord Gateway!")
        await self.change_presence(activity=activity2)

    async def on_disconnect(self):
        print("Disconnected from Discord Gateway!")



    async def is_owner(self, user: discord.User):
        if user.id in [
            795743076520820776



        ]:
            return True

        return await super().is_owner(user)


client = client()


@client.event
async def on_guild_join(guild):
    embed = discord.Embed(title=f"Astro Birb - {guild.name}",description=f"<:Arrow:1115743130461933599>**Owner:** {guild.owner.mention}\n<:Arrow:1115743130461933599>**Guild:** {guild.name}\n<:Arrow:1115743130461933599>**Guild ID** {guild.id}\n <:Arrow:1115743130461933599>**Members:** {guild.member_count}\n<:Arrow:1115743130461933599>**Created:** <t:{guild.created_at.timestamp():.0f}:F>", color=discord.Color.blurple())
    embed.set_thumbnail(url=guild.icon)
    channel = client.get_channel(1118944466980581376)
    await channel.send(embed=embed)

@client.event
async def on_guild_remove(guild):
    embed = discord.Embed(title=f"Astro Birb - {guild.name}",description=f"<:Arrow:1115743130461933599>**Owner:** {guild.owner.mention}\n<:Arrow:1115743130461933599>**Guild:** {guild.name}\n<:Arrow:1115743130461933599>**Guild ID** {guild.id}\n <:Arrow:1115743130461933599>**Members:** {guild.member_count}\n<:Arrow:1115743130461933599>**Created:** <t:{guild.created_at.timestamp():.0f}:F>", color=discord.Color.blurple())
    embed.set_thumbnail(url=guild.icon)
    channel = client.get_channel(1150816700489535508)

    await channel.send(embed=embed)

      


@client.event
async def on_member_join(member):
    target_guild_id = 1092976553752789054  
    guild_on_join = client.get_guild(target_guild_id)

    if guild_on_join:
        if member.guild.id == target_guild_id:  
            channel_id = 1092976554541326372  
            channel = guild_on_join.get_channel(channel_id)  

            if channel:
                member_count = guild_on_join.member_count
                message = f"Welcome {member.mention} to **Astro Systems**! 👋"
                view = Welcome(member_count, member)
                await channel.send(message, view=view)

@client.command()
@commands.is_owner()
async def servers(ctx):
    """Displays the name and invite of every server the bot is in"""

    embeds = []

    chunk_size = 20
    guild_chunks = [client.guilds[i:i + chunk_size] for i in range(0, len(client.guilds), chunk_size)]

    for chunk_index, guild_chunk in enumerate(guild_chunks):
        embed = discord.Embed(
            title=f"Servers List - Page {chunk_index + 1}/{len(guild_chunks)}",
            description=f"<:Arrow:1115743130461933599>**Global Users:** {len(client.users)}\n<:Arrow:1115743130461933599>**Server Count:** {len(client.guilds)}",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url="https://media.discordapp.net/ephemeral-attachments/1116038076020563988/1118955032537219194/904101097189281892.png")

        for guild in guild_chunk:
            embed.add_field(
                name=guild.name,
                value=f"<:Arrow:1115743130461933599>**Owner:** {guild.owner.mention}\n<:Arrow:1115743130461933599>**Membercount:** {guild.member_count}",
                inline=False
            )

        embeds.append(embed)

    PreviousButton = discord.ui.Button(label="<")
    NextButton = discord.ui.Button(label=">")
    FirstPageButton = discord.ui.Button(label="<<")
    LastPageButton = discord.ui.Button(label=">>")
    InitialPage = 0
    timeout = 42069

    paginator = Paginator.Simple(
        PreviousButton=PreviousButton,
        NextButton=NextButton,
        FirstEmbedButton=FirstPageButton,
        LastEmbedButton=LastPageButton,
        InitialPage=InitialPage,
        timeout=timeout
    )


    await paginator.start(ctx, pages=embeds)


@tasks.loop(seconds=300)  
async def update_channel_name():
    guild_count = len(client.guilds)
    channel_id = 1131245978704420964 
    channel = client.get_channel(channel_id)
    if channel:
        await channel.edit(name=f'{guild_count} Guilds | {len(client.users)} Users')
    else:
        print(f'Channel with ID {channel_id} not found.')


class Welcome(discord.ui.View):
    def __init__(self, member_count, member):
        super().__init__(timeout=None)
        self.gray_button.label = member_count
        self.member = member

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:logMembershipJoin:1172854752346918942>")
    async def gray_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.member
        user_badges = badges.find({'user_id': user.id})            
        badge_values = ""
        for badge_data in user_badges:
         badge = badge_data['badge']
         badge_values += f"{badge}\n"
      
        embed = discord.Embed(title=f"@{user.display_name}", description=f"{badge_values}", color=0x2b2d31)
        embed.set_thumbnail(url=user.display_avatar.url)    
        embed.add_field(name='**Profile**', value=f"* **User:** {user.mention}\n* **Display:** {user.display_name}\n* **ID:** {user.id}\n* **Join:** <t:{int(user.joined_at.timestamp())}:F>\n* **Created:** <t:{int(user.created_at.timestamp())}:F>", inline=False)
        user_roles = " ".join([role.mention for role in reversed(user.roles) if role != interaction.guild.default_role][:20])
        embed.add_field(name="**Roles**", value=user_roles, inline=False)  
        await interaction.response.send_message(embed=embed, ephemeral=True)




@client.event
async def on_message(message):
    if message.author.bot:
        return
    staff_data = scollection.find_one({'guild_id': message.guild.id})
    if staff_data is None:
        return

    if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        if not isinstance(staff_role_ids, list):
         staff_role_ids = [staff_role_ids]
        if any(role_id in staff_role_ids for role_id in [role.id for role in message.author.roles]):
            guild_id = message.guild.id
            author_id = message.author.id

            mccollection.update_one(
                {'guild_id': guild_id, 'user_id': author_id},
                {'$inc': {'message_count': 1}},
                upsert=True
            )
    await client.process_commands(message)            

#main MTExMzI0NTU2OTQ5MDYxNjQwMA.GV8KM5.6mdY5QBSJjXrNylBvM32mtvl-aiLmshNODo-vs
#beta MTExNzkxMDM0Mjc1MjgwMDc5OA.G63j3t.xHu-FfHNAAVSreeQlZqGYJZdwCyswxeoLi9e5g 

client.run(TOKEN)    
