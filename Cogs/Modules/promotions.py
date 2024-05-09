import discord
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import commands
import os
from emojis import *
import datetime
import random
import string
import Paginator
from permissions import has_admin_role, has_staff_role
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
promotionroles = db['promotion roles']
promotions = db['promotions']
class promo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @staticmethod
    async def modulecheck(ctx: commands.Context): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Promotions'] is True:   
        return True



    @commands.hybrid_command(description="View a staff member's promotions")
    @app_commands.describe(staff="The staff member to view promotion for")
    async def promotions(self, ctx: commands.Context, staff: discord.User):
        await ctx.defer()

        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the infraction module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return

        if not await has_staff_role(ctx):
            return

        embeds = []
        print(f"Searching promotions for staff ID: {staff.id} in guild ID: {ctx.guild.id}")
        filter = {
                'guild_id': ctx.guild.id,
                'staff': staff.id,
            }
        promotion_list = await promotions.find(filter).to_list(750)
        if len(promotion_list) == 0:
            await ctx.send(f"{no} **{ctx.author.display_name}**, this staff member doesn't have any promotions.", allowed_mentions=discord.AllowedMentions.none())
            return   

        if not promotion_list:
            print(f"Found {len(promotion_list)} promotions for {staff.display_name}")

        embed = discord.Embed(
            title=f"{staff.name}'s Promotions",
            description=f"* **User:** {staff.mention}\n* **User ID:** {staff.id}",
            color=discord.Color.dark_embed()
        )

        embed.set_thumbnail(url=staff.display_avatar)
        embed.set_author(icon_url=staff.display_avatar, name=staff.display_name)

        for i, promotion in enumerate(promotion_list):
            if promotion.get('jump_url', 'N/A') == 'N/A':
                jump_url = ""
            else:
                jump_url = f"\n{arrow}**[Jump to Promotion]({promotion['jump_url']})**"

            management = f"<@{promotion['management']}>"
            value = f"{arrow}**Promoted By:** {management}\n{arrow}**New:** <@&{promotion['new']}>\n{arrow}**Reason:** {promotion['reason']}{jump_url}"
            if len(value) > 1024:
                value = value[:1021] + "..."
            embed.add_field(
                name=f"<:Document:1223063264322125844> Promotion | {promotion['random_string']}",
                value=value,
                inline=False
            )

            if (i + 1) % 9 == 0 or i == len(promotion_list) - 1:
                embeds.append(embed)
                embed = discord.Embed(
                    title=f"{staff.name}'s Promotions",
                    description=f"* **User:** {staff.mention}\n* **User ID:** {staff.id}",
                    color=discord.Color.dark_embed()
                )
                embed.set_thumbnail(url=staff.display_avatar)
                embed.set_author(icon_url=staff.display_avatar, name=staff.display_name)
        PreviousButton = discord.ui.Button(emoji="<:chevronleft:1220806425140531321>")
        NextButton = discord.ui.Button(emoji="<:chevronright:1220806430010118175>")
        FirstPageButton = discord.ui.Button(emoji="<:chevronsleft:1220806428726661130>")
        LastPageButton = discord.ui.Button(emoji="<:chevronsright:1220806426583371866>")
        InitialPage = 0
        timeout = 42069
        if len(embeds) <= 1:
            PreviousButton.disabled = True
            NextButton.disabled = True
            FirstPageButton.disabled = True
            LastPageButton.disabled = True   
        paginator = Paginator.Simple(
              PreviousButton=PreviousButton,
              NextButton=NextButton,
              FirstEmbedButton=FirstPageButton,
              LastEmbedButton=LastPageButton,
              InitialPage=InitialPage,
              timeout=timeout
          )
        await paginator.start(ctx, pages=embeds)

    @commands.hybrid_command(description="Promote a staff member")
    @app_commands.describe(
        staff='What staff member are you promoting?',
        new='What is the role you are awarding them with?',
        reason='What makes them deserve the promotion?'
    ) 
    async def promote(self, ctx: commands.Context, staff: discord.User, new: discord.Role, reason:  discord.ext.commands.Range[str, 1, 2000]):
        await ctx.defer()
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the promotion module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return            
        
        if not await has_admin_role(ctx):
            return             
        try:
         member = await ctx.guild.fetch_member(staff.id)
        except (discord.NotFound, discord.HTTPException):
            print('[CHUNKING ISSUE] FETCHING INSTEAD')
            return 
        if member is None:
            await ctx.send(f"{no} **{ctx.author.display_name}**, this user isn't in the server how are you gonna promote them?", allowed_mentions=discord.AllowedMentions.none())
            return       

        optionresult = await options.find_one({'guild_id': ctx.guild.id})
        if optionresult:
                if optionresult.get('promotionissuer', False) is True:
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
            await ctx.send(f"{no} **{ctx.author.display_name}**, you are below the role `{new.name}` and do not have authority to promote this member.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
            return
        if optionresult and optionresult.get('autorole', True):
            try:
                if await promotionroles.find_one({'guild_id': ctx.guild.id, 'rank': new.id}):
                    promotionroleresult = await promotionroles.find_one({'guild_id': ctx.guild.id, 'rank': new.id})
                    for role in promotionroleresult.get('promotionranks'):
                        role = staff.guild.get_role(role)
                        if role is None:
                            continue
                        await staff.add_roles(role)
                await staff.add_roles(new)
            except discord.Forbidden:
                await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, I don't have permission to add certain roles. Please ensure I'm above the role you're trying to add and that I have the necessary permissions.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                return
        elif optionresult and not optionresult.get('autorole', True):
            try:
                await staff.add_roles(new)
                if await promotionroles.find_one({'guild_id': ctx.guild.id, 'rank': new.id}):
                    promotionroleresult = await promotionroles.find_one({'guild_id': ctx.guild.id, 'rank': new.id})
                    for role in promotionroleresult.get('promotionranks'):
                        role = staff.guild.get_role(role)
                        if role is None:
                            continue
                        await staff.add_roles(role)                
            except discord.Forbidden:
                await ctx.send(f"<:Allonswarning:1123286604849631355> **{ctx.author.display_name}**, I don't have permission to add roles. Please ensure I'm above the new role or that I have the necessary permissions.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
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
            
            embed_thumbnail = staff.display_avatar if custom['thumbnail'] == "{staff.avatar}" else custom['thumbnail']
            authoricon = ctx.author.display_avatar if custom['author_icon'] == "{author.avatar}" else custom['author_icon']

            embed_thumbnail = None if embed_thumbnail == "None" else embed_thumbnail
            authoricon = None if authoricon == "None" else authoricon

            embed = discord.Embed(title=embed_title, description=embed_description, color=int(custom['color'], 16))
            embed.set_thumbnail(url=embed_thumbnail)
            embed.set_author(name=embed_author, icon_url=authoricon) if embed_author != "None" else embed.remove_author()
            
            if custom['image']:
                embed.set_image(url=custom['image'])
        else:
            embed = discord.Embed(title="Staff Promotion", color=0x2b2d31, description=f"* **User:** {staff.mention}\n* **Updated Rank:** {new.mention}\n* **Reason:** {reason}")
            embed.set_thumbnail(url=staff.display_avatar)
            
            if optionresult:
                if optionresult.get('pshowissuer', True) is False:
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
        random_string = ''.join(random.choices(string.digits, k=8))
        if data:
            channel_id = data['channel_id']
            channel = self.client.get_channel(channel_id)

            if channel:
                try:            
                    await ctx.send(f"{tick} **{ctx.author.display_name}**, I've promoted **@{staff.display_name}**", allowed_mentions=discord.AllowedMentions.none())
                    msg = await channel.send(f"{staff.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False), view=view)
                    await promotions.insert_one({
                            'management': ctx.author.id,
                            'staff': staff.id,
                            'reason': reason,
                            'new': new.id,
                            'random_string': random_string,
                            'guild_id': ctx.guild.id,
                            'jump_url': msg.jump_url,
                            'msg_id': msg.id,
                            'timestamp': datetime.datetime.now()
                    
                    })
                    if consent_data['PromotionAlerts'] == "Enabled":
                        try:
                            await staff.send(f"🎉 You were promoted **@{ctx.guild.name}!**", embed=embed)
                        except:
                            print(f"{staff.display_name} has DMs disabled")
                except discord.Forbidden: 
                    await ctx.send(f"{no} **{ctx.author.display_name},** I don't have permission to view that channel.", allowed_mentions=discord.AllowedMentions.none())       
            else:
                await ctx.send(f"{Warning} {ctx.author.display_name}, I don't have permission to view this channel.", allowed_mentions=discord.AllowedMentions.none())
        else:
            await ctx.send(f"{Warning} **{ctx.author.display_name}**, the channel is not setup please run `/config`", allowed_mentions=discord.AllowedMentions.none())

    @staticmethod
    async def replace_variables(message, replacements):
     for placeholder, value in replacements.items():
        if value is not None:
            message = str(message).replace(placeholder, str(value))
        else:
            message = str(message).replace(placeholder, "")  
     return message

class PromotionIssuer(discord.ui.View):
    def __init__(self):
        super().__init__()


    @discord.ui.button(label=f"", style=discord.ButtonStyle.grey, disabled=True, emoji="<:flag:1223062579346145402>")
    async def issuer(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass
async def setup(client: commands.Bot) -> None:
    await client.add_cog(promo(client))            