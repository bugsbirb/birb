import discord
from discord import ui
import time
import platform
import sys
import discord.ext
from discord.ext import commands
from datetime import UTC
from urllib.parse import quote_plus
from discord import app_commands
import discord
import datetime
from discord.ext import commands, tasks
from jishaku import Jishaku
from typing import Optional
import Paginator
from cogs.infractions import *
from cogs.tickets import *
client = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = client['astro']
scollection = db['staffrole']
ticketconfig = db['Tickets Configuration']
tickets = db['Tickets']

def user(self, channel_id):
        ticket_data = tickets.find_one({'channel_id': channel_id})
        if ticket_data:
            user = ticket_data['user_id']
            return user
        return None, None



class client(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents().all()
        super().__init__(command_prefix=commands.when_mentioned_or("-"), intents=intents, shard_count=2)
        self.client = client
        self.cogslist = ["cogs.tickets","cogs.astro-management", "cogs.halloween","cogs.modmail", "cogs.forumutils", "cogs.tags" ,"cogs.botinfo", "cogs.Partnership","cogs.infractions", "cogs.configuration", "cogs.utility", "cogs.reports", "cogs.loa", "cogs.promotions", "cogs.ratings"]

    async def load_jishaku(self):
        await self.wait_until_ready()
        await self.load_extension('jishaku')

    async def setup_hook(self):
        self.loop.create_task(self.load_jishaku()) 
        self.add_view(TicketOpen())
        self.add_view(TicketHelp())



        for ext in self.cogslist:
            await self.load_extension(ext)

    async def on_ready(self):
        prfx = (time.strftime("%H:%M:%S GMT", time.gmtime()))
        print(prfx + " Logged in as " + self.user.name)
        print(prfx + " Bot ID " + str(self.user.id))
        print(prfx + " Discord Version " +  discord.__version__)
        print(prfx + " Python Version " + str(platform.python_version()))
        synced = await self.tree.sync()
        print(prfx + " Slash CMDs Synced " + str(len(synced)) + " Commands")
        print(prfx + " Bot is in " + str(len(self.guilds)) + " servers")

        



    
    async def on_connect(self):
        activity2 = discord.CustomActivity(emoji="<:pending:1140623442962546699>", name = f"V2.30 | {len(client.guilds)} guilds")

        print("Connected to Discord Gateway!")
        await self.change_presence(activity=activity2)
        update_channel_name.start()

    async def on_disconnect(self):
        print("Disconnected from Discord Gateway!")

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
        await channel.edit(name=f'| Astro Birb: {guild_count}')
    else:
        print(f'Channel with ID {channel_id} not found.')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return 

        embed = discord.Embed(title='Command Error', description=f"Command Usage: {ctx.command.name}\n Guild:{ctx.guild.name}", color=discord.Color.red())
        embed.add_field(name='Error', value=f"```py\n {str(error)}\n```", inline=False)

        logging_channel = client.get_channel(1139907646963597423)
        if logging_channel:
            await logging_channel.send(embed=embed)
        else:
            print("Logging channel not found.")

        import traceback
        traceback_str = ''.join(traceback.format_tb(error.__traceback__))
        print(f'Traceback:\n{traceback_str}')


#main MTExMzI0NTU2OTQ5MDYxNjQwMA.GV8KM5.6mdY5QBSJjXrNylBvM32mtvl-aiLmshNODo-vs
#beta MTExNzkxMDM0Mjc1MjgwMDc5OA.G63j3t.xHu-FfHNAAVSreeQlZqGYJZdwCyswxeoLi9e5g 

client.run("MTExMzI0NTU2OTQ5MDYxNjQwMA.GV8KM5.6mdY5QBSJjXrNylBvM32mtvl-aiLmshNODo-vs")    