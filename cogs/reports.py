
import discord
from discord.ext import commands, tasks
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import pytz
from discord import app_commands
from pymongo import MongoClient
mongo = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = mongo['astro']
repchannel = db['report channel']

class Reports(commands.Cog):
    def __init__(self, bot):
        self.client = bot

        reported_at = datetime.utcnow().timestamp()
        reported_at_format = f"<t:{int(reported_at)}:F>"

 


    @commands.hybrid_command(description="Report users breaking server rules.")
    @app_commands.describe(
        member='Who are you reporting?',
        reason='What is the reason for reporting this user',
        message_link='Do you have proof of this person doing this?')
    async def report(self, ctx, member: discord.User, *, reason: str, message_link: Optional[str] = None, proof: discord.Attachment, proof2: discord.Attachment = None, proof3: discord.Attachment = None, proof4: discord.Attachment = None, proof5: discord.Attachment = None, proof6: discord.Attachment = None, proof7: discord.Attachment = None, proof8: discord.Attachment = None, proof9: discord.Attachment = None):


        proof_urls = [proof.url]

        if proof2:
         proof_urls.append(proof2.url)
        if proof3:
         proof_urls.append(proof3.url)
        if proof4:
         proof_urls.append(proof4.url)
        if proof5:
         proof_urls.append(proof5.url)
        if proof6:
         proof_urls.append(proof6.url)
        if proof7:
         proof_urls.append(proof7.url)
        if proof8:
         proof_urls.append(proof8.url)
        if proof9:
         proof_urls.append(proof9.url)

    
        proof_message = "\n".join(proof_urls)
        timezone = pytz.timezone('Europe/Paris')
        reported_at = datetime.now(timezone)
        reported_at_format = f"<t:{int(reported_at.timestamp())}:t>"


        embed = discord.Embed(title="Report", color=0x2b2d31)
        embed.add_field(name="Reported User", value=f"* **User:** {member.mention}\n* **ID:** {member.id}", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        if message_link:
            embed.add_field(name=f"Report Information", value=f"* **Reported By:** {ctx.author.mention}\n* **Reason:** {reason}\n* **Message Link:** {message_link}\n* **Reported At:** {reported_at_format}", inline=False)            
        else:
            embed.add_field(name=f"Report Information", value=f"* **Reported By:** {ctx.author.mention}\n* **Reason:** {reason}\n* **Reported At:** {reported_at_format}", inline=False)

          


        view = Confirm()
        await ctx.send(embed=embed, view=view, ephemeral=True)            

            
        await view.wait()
        if view.value:
            guild_id = ctx.guild.id
            data = repchannel.find_one({'guild_id': guild_id})

            if data:
                channel_id = data['channel_id']
                channel = self.client.get_channel(channel_id)

                if channel:
                    await channel.send(embed=embed)
                    for url in proof_urls:
                        await channel.send(url)
                else:
                    await ctx.send(f"**{ctx.author.display_name}**, I don't have permission to view this channel.")
            else:
                await ctx.send(f"**{ctx.author.display_name}**, the channel is not setup please run `/config`")
        elif view.cancel:
            await ctx.send("Report cancelled.")     
         


        elif view.cancel: 
         await channel.send(None)             




                


class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @discord.ui.button(label='Send', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        self.value = True
        await interaction.response.edit_message(content=f"<:Tick:1140286044114268242> **{interaction.user.display_name}**, I've logged the report.", view=None)
        self.stop()


    @discord.ui.button(label='Discard', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"<:Tick:1140286044114268242> **Cancelled.**", view=None, embed=None)    
        self.value = False
        self.stop()                       

              

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Reports(client))        