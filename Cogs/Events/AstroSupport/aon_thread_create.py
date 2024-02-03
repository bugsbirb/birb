import discord
from discord.ext import commands
import asyncio
from emojis import *
from dotenv import load_dotenv


class AForumCreaton(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener('on_thread_create')
    async def on_created_thread(self, thread: discord.Thread):
        if thread.guild.id != 1092976553752789054:
            return
        if thread.parent_id != 1101807246079442944:
            return

        await asyncio.sleep(2)
        banner = discord.Embed(title="", color=discord.Color.dark_embed())
        banner.set_image(url="https://cdn.discordapp.com/attachments/1104358043598200882/1169328494044528710/006_2.png?ex=65550106&is=65428c06&hm=392ce6de8fa7f60763c87ac8f2ee9cbad49ed5603ea6555d6be6da36fc8ce6ea&")
        embed = discord.Embed(title=f"<:forum:1162134180218556497> Astro Support", description="> Welcome to Astro Support please wait for a support representative to respond!", color=discord.Color.dark_embed())
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")
        embed.set_thumbnail(url="https://cdn.discordapp.com/icons/1092976553752789054/bf1e0138243c734664bbf9fbf8d5ae20.png?size=512")
        msg = await thread.send(content='<@&1092977110412439583>', embeds=(banner, embed), allowed_mentions=discord.AllowedMentions(roles=True)) 

async def setup(client: commands.Bot) -> None:
    await client.add_cog(AForumCreaton(client))   