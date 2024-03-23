import discord
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import commands
import os
from emojis import *
from typing import Literal, Optional
from permissions import has_admin_role
MONGO_URL = os.getenv('MONGO_URL')

from motor.motor_asyncio import AsyncIOMotorClient
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
promochannel = db['promo channel']
consent = db['consent']
modules = db['Modules']
Customisation = db['Customisation']
options = db['module options']
class promo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def modulecheck(self, ctx): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
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
    async def promote(self, ctx, staff: discord.Member, new: discord.Role, reason: app_commands.Range[str, 1, 2000], autorole: Optional[Literal['False']]):
        await ctx.defer()
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the promotion module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return            
        if not await has_admin_role(ctx):
         return             
        optionresult = await options.find_one({'guild_id': ctx.guild.id})
        if optionresult:
            if optionresult.get('promotionissuer', False) == True:
                view = PromotionIssuer()
                view.issuer.label = f"Issued By {ctx.author.display_name}"
            else:
                view = None    
        else:
            view = None             
   
        if ctx.author == staff:
         await ctx.send(f"{no} You can't promote yourself.", allowed_mentions=discord.AllowedMentions.none())
         return

        if ctx.author.top_role <= new:
            await ctx.send(f"{no} **{ctx.author.display_name}**, your below the role `{new.name}` you do not have authority to promote this member.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
            return
        
        if optionresult:
         if optionresult.get('autorole', True) == False:
          pass
         else:
          try:
            await staff.add_roles(new)
          except discord.Forbidden:
            await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, I don't have permission to add roles.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
            return
        else:
          if autorole == 'False':
              pass
          else:

           try:
            await staff.add_roles(new)
           except discord.Forbidden:
            await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, I don't have permission to add roles.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
            return           


        custom = await Customisation.find_one({'guild_id': ctx.guild.id, 'type': 'Promotions'})
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
         if optionresult:
          if optionresult.get('pshowissuer', True) == False:
                embed.remove_author()
          else:
                embed.set_author(name=f"Signed, {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
         else:
                embed.set_author(name=f"Signed, {ctx.author.display_name}", icon_url=ctx.author.display_avatar)  


        guild_id = ctx.guild.id
        data = await promochannel.find_one({'guild_id': guild_id})
        consent_data = await consent.find_one({"user_id": staff.id})
        if consent_data is None:
            await consent.insert_one({"user_id": ctx.author.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled", "LOAAlerts": "Enabled"})
            consent_data = {"user_id": ctx.author.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled", "LOAAlerts": "Enabled"}          
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:
            try:            
             await ctx.send(f"{tick} **{ctx.author.display_name}**, I've promoted **@{staff.display_name}**", allowed_mentions=discord.AllowedMentions.none())
             await channel.send(f"{staff.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False), view=view)
            except discord.Forbidden: 
             await ctx.send(f"{no} **{ctx.author.display_name},** I don't have permission to view that channel.", allowed_mentions=discord.AllowedMentions.none())        
             return       
            if consent_data['PromotionAlerts'] == "Enabled":
                try:
                 await staff.send(f"🎉 You were promoted **@{ctx.guild.name}!**", embed=embed)
                except:
                 print(f"{staff.display_name} has DMs disabled")
                 pass 

            else:    
                pass
         else:
            await ctx.send(f"{Warning} {ctx.author.display_name}, I don't have permission to view this channel.", allowed_mentions=discord.AllowedMentions.none())
        else:
          await ctx.send(f"{Warning} **{ctx.author.display_name}**, the channel is not setup please run `/config`", allowed_mentions=discord.AllowedMentions.none())

    async def replace_variables(self, message, replacements):
     for placeholder, value in replacements.items():
        if value is not None:
            message = str(message).replace(placeholder, str(value))
        else:
            message = str(message).replace(placeholder, "")  
     return message

class PromotionIssuer(discord.ui.View):
    def __init__(self):
        super().__init__()


    @discord.ui.button(label=f"", style=discord.ButtonStyle.grey, disabled=True, emoji="<:flag:1166508151290462239>")
    async def issuer(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass
async def setup(client: commands.Bot) -> None:
    await client.add_cog(promo(client))            