import discord
from discord import ui
import time
import platform
import sys
import discord.ext
from discord.ext import commands
from urllib.parse import quote_plus
from discord import app_commands
import discord
import datetime
from discord.ext import commands, tasks
from jishaku import Jishaku
from pymongo import MongoClient
from typing import Optional
import asyncio
from emojis import *
import random
import pymongo
from typing import Literal
client = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = client['astro']
candy = db['Hallowen Event']
inventory = db['Halloween Inventory']

 

class HalloweenShop(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Jester Outfit', value='jester', description='Costs 500 candies'),
            discord.SelectOption(label='Chicken Outfit', value='chicken', description='Costs 1000 candies')
        ]
        super().__init__(placeholder='Select an outfit', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_outfit = self.values[0]
    
        valid_outfits = ['jester', 'chicken']
        if selected_outfit in valid_outfits:
            user_id = interaction.user.id

            user_has_outfit = inventory.find_one({"user_id": user_id, "outfit": selected_outfit})
            if user_has_outfit:
                await interaction.response.send_message(f"{no} You already have the {selected_outfit} outfit.", ephemeral=True)
            else:
                user_document = candy.find_one({"user_id": user_id})
                if user_document:
                    user_candy = user_document.get("candy", 0)
                    outfit_cost = 500 if selected_outfit == 'jester' else 1000  
                    if user_candy >= outfit_cost:

                        updated_candy = user_candy - outfit_cost
                        candy.update_one(
                            {"user_id": user_id},
                            {"$set": {"candy": updated_candy}}
                        )


                        inventory_data = {
                            "user_id": user_id,
                            "outfit": selected_outfit
                        }
                        inventory.insert_one(inventory_data)

                        await interaction.response.send_message(f"{tick} **{interaction.user}**, you have purchased the {selected_outfit} outfit!")
                    else:
                        await interaction.response.send_message(f"{no} You don't have enough candy to purchase this outfit.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"{no} You need to have some candy to purchase outfits.", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid selection.", ephemeral=True)
 
class Shop(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HalloweenShop())

class Halloween(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.group()
    async def candy(self, ctx):
        pass

    @commands.command(description="Go trick or treating for candy (Limited Time Event)")
    @commands.cooldown(1, 10, commands.BucketType.user) 
    async def trickortreat(self, ctx):    
        msg = await ctx.reply(f"🚪*Creeeeaak* ... Who's there?")
        await asyncio.sleep(2)
        chance_of_trick = random.randint(1, 100)

        message = ""
        
        jester_document = inventory.find_one({"user_id": ctx.author.id, "outfit": "jester"})
        chicken_document = inventory.find_one({"user_id": ctx.author.id, "outfit": "chicken"})
        if jester_document and chicken_document:
            messages = [
    "Enjoy your treat...?! Are you not hot wearing 2 costumes?",
    "Oh, a chicken Jester how unique!",
    "You're a double threat with both the Jester and Chicken outfits!",
    "It's a costume mashup! Jester by day, Chicken by night!",
    "You're like a Jester rooster! Cluck-tastic!",
    "You've got a double dose of candy power with those costumes!",
    "Two costumes are better than one! Enjoy your treats!",
    "You're the candy king in your Jester and Chicken outfits!",
]
            message = random.choice(messages)             
            randomcandy = random.randint(30, 50)            
        elif jester_document:
            messages = ["Enjoy your treat!", "Here's a spooky surprise!", 'Here you go!', 'Love your costume, have some sweets.', 'Looking sexy in that costume!', 'Are you 18 🤩?']
            message = random.choice(messages)             
            randomcandy = random.randint(15, 35)
        elif chicken_document:
            messages = ["Enjoy your treat!", "Here's a spooky surprise!", 'Here you go!', 'Love your costume, have some sweets.']
            message = random.choice(messages)            
            randomcandy = random.randint(20, 40)
        else:
            if chance_of_trick <= 20:
                message = "Tricked! No candy for you!"
                randomcandy = 0
            else:
                randomcandy = random.randint(10, 30)
                messages = ["Enjoy your treat!", "Here's a spooky surprise!", 'Here you go!', 'Love your costume, have some sweets.']
                message = random.choice(messages)

        user_document = candy.find_one({"user_id": ctx.author.id})        
        if user_document:
            updated_candy_received = user_document.get("candy", 0) + randomcandy
            candy.update_one(
                {"user_id": ctx.author.id},
                {"$set": {"candy": int(updated_candy_received)}}
            )
        else:
            document = {
                "user_id": ctx.author.id,
                "Name": ctx.author.name,
                "candy": randomcandy
            }
            candy.insert_one(document)
        
        await msg.edit(content=f"<:Star:1133346299668873216> {message} You were given <:candysweet:1160591383158071376> {randomcandy}")



    @candy.command(description="View your candy (Limited Time Event)")
    async def bucket(self, ctx):
        user_document = candy.find_one({"user_id": ctx.author.id})
        
        if user_document:
            candy_count = user_document.get("candy", 0)
            await ctx.reply(f"🎃 **{ctx.author.display_name}**, you have <:candysweet:1160591383158071376> **{candy_count}** candies in your candy bucket.")
        else:
            await ctx.reply(f"🎃 **{ctx.author.display_name}**, it looks like your candy bucket is empty. Go trick or treating to collect some candies!")

    @trickortreat.error
    async def trickortreat_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"{no} **{ctx.author.display_name}**, you must wait **`{error.retry_after:.0f} seconds`** before trick or treating again.", delete_after=error.retry_after)
            pass

    @candy.command(description="Candy global leaderboard (Limited Time Event)", aliases=['lb'])
    async def leaderboard(self, ctx):
        leaderboard = list(candy.find().sort("candy", pymongo.DESCENDING).limit(10))

        leaderboard_message = "\n\n"
        for idx, user_data in enumerate(leaderboard, start=1):
            user = ctx.guild.get_member(user_data["user_id"])
            if user:
                leaderboard_message += f"{idx}. **{user.display_name}** `{user_data['candy']}` candies\n"
            else:
                leaderboard_message += f"{idx}. **{user_data['Name']}** `{user_data['candy']}` candies\n"

        embed = discord.Embed(
            title="🍬 Candy Leaderboard 🍬",
            description=leaderboard_message,
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url="https://images.emojiterra.com/google/android-12l/512px/1f383.png")
        await ctx.send(embed=embed)

    @commands.group()
    async def halloween(self, ctx):
        pass

    @halloween.command(description="Buy outfits for a candy boost! (Limited Time Event)")
    async def shop(self, ctx):
        embed = discord.Embed(title="🍬 Halloween Store 🍬", color=discord.Color.dark_embed())
        embed.add_field(name="Jester Outfit", value="**Prices:** `500` \n**Abilities:** `20% More Candy`, `You won't ever get tricked`")
        embed.add_field(name="Chicken Outfit", value="**Prices:** `1000` \n**Abilities:** `40% More Candy`, `You won't ever get tricked`, `Get all the ladies.`")
        embed.set_thumbnail(url="https://images.emojiterra.com/google/android-12l/512px/1f383.png")
        view = Shop()
        await ctx.send(embed=embed, view=view)

    @candy.command(description="Steal candy from others (Limited Time Event)")    
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def steal(self, ctx, victim: discord.Member):

        user_id = ctx.author.id
        target_id = victim.id

        if user_id == target_id:
            await ctx.send(f"{no} You can't steal candy from yourself!")
            return

        target_document = candy.find_one({"user_id": target_id})
        if not target_document or target_document.get("candy", 0) <= 0:
            await ctx.send(f"{no} {victim.display_name} doesn't have any candy to steal.")
            return


        failure_chance = 0.60  
        user_document = candy.find_one({"user_id": user_id})        
        user_updated_candy = user_document.get("candy", 0)

        if random.random() <= failure_chance:
            fine_amount = 100
            user_updated_candy -= fine_amount 


            candy.update_one({"user_id": user_id}, {"$set": {"candy": int(user_updated_candy)}})            
            await ctx.reply(f"{no} **{ctx.author.display_name}** attempted to steal candy from **@{victim.display_name}** but got caught by the police and paid a fine of 🍬 `100`.")
        else:

            target_candy = target_document["candy"]
            amount_to_steal = round(target_candy * 0.10, target_candy)

            user_document = candy.find_one({"user_id": user_id})
            if user_document:
                user_candy = user_document.get("candy", 0)
                user_updated_candy = user_candy + amount_to_steal
                candy.update_one({"user_id": user_id}, {"$set": {"candy": int(user_updated_candy)}})
            
            target_updated_candy = target_candy - amount_to_steal
            candy.update_one({"user_id": target_id}, {"$set": {"candy": int(target_updated_candy)}})
        
            await ctx.reply(f"{tick} **{ctx.author.display_name}** successfully stole {amount_to_steal:.0f} candy from **@{victim.display_name}**!")

    @steal.error
    async def stealcoomand(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"{no} **{ctx.author.display_name}**, you must wait **`{error.retry_after:.0f} seconds`** before stealing candy.", delete_after=error.retry_after)
            pass

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Halloween(client))       

