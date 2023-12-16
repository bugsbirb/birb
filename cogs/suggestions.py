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
from discord.ui import View, button
import platform
import os
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
modules = db['Modules']
suggestions_collection = db["suggestions"]
from emojis import *
suggestschannel = db["suggestion channel"]
class suggestions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata.get('Suggestions', False) == True: 
        return True
     else:   
        return False


    @commands.hybrid_command(description="Submit a suggestion for improvement")
    async def suggest(self, ctx, suggestion: str):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return    

        suggestion_data = {
            "author_id": ctx.author.id,
            "suggestion": suggestion,
            "upvotes": 0,
            "downvotes": 0,
            "upvoters": [],
            "downvoters": [],
        }
        result = suggestions_collection.insert_one(suggestion_data)
        suggestion_id = result.inserted_id

        embed = discord.Embed(title="", description=f"**Submitter**\n {ctx.author.mention} \n\n**Suggestion**\n{suggestion}", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")
        embed.set_author(icon_url=ctx.guild.icon, name=ctx.guild.name)
        embed.set_footer(text=f"0 Upvotes | 0 Downvotes")
        view = SuggestionView()
        channeldata = suggestschannel.find_one({"guild_id": ctx.guild.id})
        if channeldata:
         channel_id = channeldata['channel_id']
         channel = self.client.get_channel(channel_id)
         if channel:
          try:  
           msg = await channel.send(embed=embed, view=view)
          except discord.Forbidden: 
             await ctx.send(f"{no} I don't have permission to view that channel.")              
             return
          await ctx.send(f"{tick} **{ctx.author.display_name}**, succesfully sent the suggestion.")
          suggestions_collection.update_one({"_id": suggestion_id}, {"$set": {"message_id": msg.id}})
        else: 
            await ctx.send(f"{no} {ctx.author.display_name}, this channel isn't configured. Please do `/config`.")







    async def on_timeout(self):
        self.clear_items()
    async def update_embed(self, interaction: discord.Interaction):
        suggestion_data = suggestions_collection.find_one({"_id": self.suggestion_id})
        embed = interaction.message.embeds[0]
        upvotes, downvotes = suggestion_data["upvotes"], suggestion_data["downvotes"]
        embed.set_footer(text=f"{upvotes} Upvotes | {downvotes} Downvotes")
        await interaction.message.edit(embed=embed)
    async def update_embed(self, interaction: discord.Interaction):
        suggestion_data = suggestions_collection.find_one({"_id": self.suggestion_id})
        embed = interaction.message.embeds[0]
        upvotes, downvotes = suggestion_data["upvotes"], suggestion_data["downvotes"]
        embed.set_footer(text=f"{upvotes} Upvotes | {downvotes} Downvotes")
        await interaction.message.edit(embed=embed)

class SuggestionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def on_timeout(self):
        self.clear_items()

    @button(label='Upvote', style=discord.ButtonStyle.green, custom_id="upvote_button", emoji="<:UpVote:1183063056834646066>")
    async def Yes(self, interaction, button):
        message_id = interaction.message.id
        suggestion_data = suggestions_collection.find_one({"message_id": message_id})
        upvoters = suggestion_data.get("upvoters", [])
        downvoters = suggestion_data.get("downvoters", [])

        if interaction.user.id in upvoters:
            suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"upvotes": -1},
                    "$pull": {"upvoters": interaction.user.id},
                },
            )
            suggestion_data = suggestions_collection.find_one({"message_id": message_id})  
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Unvoted.", ephemeral=True)
        elif interaction.user.id in downvoters:
            suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"upvotes": 1, "downvotes": -1},
                    "$pull": {"downvoters": interaction.user.id},
                    "$push": {"upvoters": interaction.user.id},
                },
            )
            suggestion_data = suggestions_collection.find_one({"message_id": message_id})  
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Switched to upvote.", ephemeral=True)
        else:
            suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"upvotes": 1},
                    "$push": {"upvoters": interaction.user.id},
                },
            )
            suggestion_data = suggestions_collection.find_one({"message_id": message_id})  
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Upvoted.", ephemeral=True)

    @button(label='Downvote', style=discord.ButtonStyle.red, custom_id="downvote_button", emoji="<:DownVote:1183063097477451797>")
    async def No(self, interaction, button):
        message_id = interaction.message.id
        suggestion_data = suggestions_collection.find_one({"message_id": message_id})
        upvoters = suggestion_data.get("upvoters", [])
        downvoters = suggestion_data.get("downvoters", [])

        if interaction.user.id in downvoters:
            suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"downvotes": -1},
                    "$pull": {"downvoters": interaction.user.id},
                },
            )
            suggestion_data = suggestions_collection.find_one({"message_id": message_id})  
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Unvoted.", ephemeral=True)
        elif interaction.user.id in upvoters:
            suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"upvotes": -1, "downvotes": 1},
                    "$pull": {"upvoters": interaction.user.id},
                    "$push": {"downvoters": interaction.user.id},
                },
            )
            suggestion_data = suggestions_collection.find_one({"message_id": message_id}) 
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Switched to downvote.", ephemeral=True)
        else:
            suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"downvotes": 1},
                    "$push": {"downvoters": interaction.user.id},
                },
            )
            suggestion_data = suggestions_collection.find_one({"message_id": message_id})  
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Downvoted.", ephemeral=True)

    async def update_embed(self, interaction, suggestion_data):
        if interaction.message:
            print(f"Editing message with ID {interaction.message.id}")
            embed = interaction.message.embeds[0]
            upvotes, downvotes = suggestion_data["upvotes"], suggestion_data["downvotes"]
            embed.set_footer(text=f"{upvotes} Upvotes | {downvotes} Downvotes")
            await interaction.message.edit(embed=embed)
        else:
            print("Interaction message is None!")

    @button(label='Voters List', style=discord.ButtonStyle.gray, custom_id="view_voters_button", emoji="<:List:1179470251860185159>")
    async def view_voters(self, interaction, button):
        message_id = interaction.message.id
        suggestion_data = suggestions_collection.find_one({"message_id": message_id})

        upvoters = suggestion_data.get("upvoters", [])
        downvoters = suggestion_data.get("downvoters", [])

        upvoters_mentions = [f"<@{upvoter}>" for upvoter in upvoters]
        downvoters_mentions = [f"<@{downvoter}>" for downvoter in downvoters]

        embed = discord.Embed(title="Voters List", color=discord.Color.dark_embed())
        embed.add_field(name="Upvoters", value="\n".join(upvoters_mentions) or "No upvoters")
        embed.add_field(name="Downvoters", value="\n".join(downvoters_mentions) or "No downvoters")

        await interaction.response.send_message(embed=embed, ephemeral=True)



async def setup(client: commands.Bot) -> None:
    await client.add_cog(suggestions(client))     
