import discord
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from emojis import *
from typing import Literal, Optional
from permissions import has_admin_role, has_staff_role
MONGO_URL = os.getenv('MONGO_URL')

client = MongoClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
promochannel = db['promo channel']
consent = db['consent']
modules = db['Modules']
Customisation = db['Customisation']
class promo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Promotions'] == True:   
        return True



    @commands.hybrid_command(description="Promote a staff member")
    @app_commands.describe(
    staff='What staff member are you promoting?',
    new='What the role you are awarding them with?',
    reason='What makes them deserve the promotion?',
    autorole='Do you want to give them the role automatically?'
    ) 
    async def promote(self, ctx, staff: discord.Member, new: discord.Role, reason: str, autorole: Optional[Literal['False']]):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return            
        if not await has_admin_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`")
         return             
         
        if ctx.author == staff:
         await ctx.send(f"{no} You can't promote yourself.")
         return

        if ctx.author.top_role <= new:
            await ctx.send(f"{no} **{ctx.author.display_name}**, your below the role `{new.name}` you do not have authority to promote this member.", ephemeral=True)
            return
        if autorole == "False":

         pass
        else:
         try:
            await staff.add_roles(new)
         except discord.Forbidden:
            await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, I don't have permission to add roles.", ephemeral=True)
            return


        custom = Customisation.find_one({'guild_id': ctx.guild.id, 'type': 'Promotions'})
        if custom:
            replacements = {
            '{staff.mention}': staff.mention,
            '{staff.name}': staff.display_name,
            '{author.mention}': ctx.author.mention,
            '{author.name}': ctx.author.display_name,
            '{reason}': reason,
            '{newrank}': new.mention

           }
            embed_title = await self.replace_variables(custom['title'], replacements)
            embed_description = await self.replace_variables(custom['description'], replacements)

            embed_author = await self.replace_variables(custom['author'], replacements)
            if custom['thumbnail'] == "{staff.avatar}":
              embed_thumbnail = staff.display_avatar
            else:
              embed_thumbnail = custom['thumbnail']


            if custom['author_icon'] == "{author.avatar}":
              authoricon = ctx.author.display_avatar
            else:
              authoricon = custom['author_icon']     

            if embed_thumbnail == "None":
              embed_thumbnail = None

            if authoricon == "None":
              authoricon = None   

            embed = discord.Embed(title=embed_title,  description=embed_description, color=int(custom['color'], 16))

            embed.set_thumbnail(url=embed_thumbnail)
            print(str(embed_author))

            if str(embed_author) == "None":
              embed.set_author(name="", icon_url="")   
            else:
               embed.set_author(name=embed_author, icon_url=authoricon)  
            if custom['image']:
              embed.set_image(url=custom['image'])
             

        else:
              
         embed = discord.Embed(title=f"Staff Promotion", color=0x2b2d31, description=f"* **User:** {staff.mention}\n* **Updated Rank:** {new.mention}\n* **Reason:** {reason}")
         embed.set_thumbnail(url=staff.display_avatar)
         embed.set_author(name=f"Signed, {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)


        guild_id = ctx.guild.id
        data = promochannel.find_one({'guild_id': guild_id})
        consent_data = consent.find_one({"user_id": staff.id})
        if consent_data is None:
            consent.insert_one({"user_id": staff.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled"})     
            consent_data = {"user_id": staff.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled"}            
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
            try:            
             await ctx.send(f"{tick} **{ctx.author.display_name}**, I've promoted **@{staff.display_name}**")
             await channel.send(f"{staff.mention}", embed=embed)
            except discord.Forbidden: 
             await ctx.send(f"{no} **{ctx.author.display_name},** I don't have permission to view that channel.")        
             return       
            if consent_data['PromotionAlerts'] == "Enabled":
                await staff.send(f"🎉 You were promoted **@{ctx.guild.name}!**", embed=embed)
            else:    
                pass
         else:
            await ctx.send(f"{Warning} {ctx.author.display_name}, I don't have permission to view this channel.")
        else:
          await ctx.send(f"{Warning} **{ctx.author.display_name}**, the channel is not setup please run `/config`")

    async def replace_variables(self, message, replacements):
     for placeholder, value in replacements.items():
        if value is not None:
            message = str(message).replace(placeholder, str(value))
        else:
            message = str(message).replace(placeholder, "")  
     return message


async def setup(client: commands.Bot) -> None:
    await client.add_cog(promo(client))            