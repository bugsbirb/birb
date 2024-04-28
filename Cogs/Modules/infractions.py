
import discord
from discord.ext import commands
from typing import Literal
import random
import string
from typing import Optional
from discord.ext import commands
import typing
import os
import Paginator
from discord import app_commands
from emojis import *
from permissions import *
from datetime import datetime, timedelta
import re
import discord
from discord.ext import tasks
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
collection = db['infractions']
scollection = db['staffrole']
arole = db['adminrole']
infchannel = db['infraction channel']
consent = db['consent']
modules = db['Modules']
Customisation = db['Customisation']
infractiontypes = db['infractiontypes']
infractiontypeactions = db['infractiontypeactions']
options = db['module options']
class Infractions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        loop = self.check_infractions.start()
        if loop:
            print("[✅] Infractions loop started.")
        else:
            print("[❌] Infractions loop failed to start.")

    


    @staticmethod
    async def modulecheck(ctx: commands.Context): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['infractions'] is True:   
        return True

     

    async def infractiontypes(
        ctx: commands.Context,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
     filter = {
        'guild_id': interaction.guild_id 
    }

     try:
        tag_names = await infractiontypes.distinct("types", filter)
     except Exception as e:
        print(f"Error fetching distinct values: {e}")
        tag_names = None

     if tag_names is None or not tag_names:
        tag_names = ['Activity Notice', 'Verbal Warning', 'Warning', 'Strike', 'Demotion', 'Termination']

     filtered_names = [name for name in tag_names if current.lower() in name.lower()]
     try:
      choices = [app_commands.Choice(name=name, value=name) for name in filtered_names]
     except Exception as e:
      print(f"Error creating choices: {e}")
     return choices
 
    
    @commands.hybrid_group(description="Infract multiple staff members")
    async def infraction(self, ctx: commands.Context):
        pass

    @infraction.command(name="multiple", description="Infract multiple staff members")
    @app_commands.autocomplete(action=infractiontypes)
    @app_commands.describe(action="The action to take", reason="The reason for the action", notes="Additional notes", expiration="The expiration date of the infraction (m/h/d/w)", anonymous="Whether to send the infraction anonymously")
    async def infraction_multiple(self, ctx: commands.Context,  action: discord.ext.commands.Range[str, 1, 200], *, reason: discord.ext.commands.Range[str, 1, 2000], notes="", expiration: Optional[str] = None, anonymous: Optional[Literal['True']] = None):
       if not await premium(ctx):
          view = PRemium()
          return await ctx.send(f"<:Tip:1167083259444875264> **{ctx.author.display_name}**, you need to buy premium to use this feature!", allowed_mentions=discord.AllowedMentions.none(), view=view)
       if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the infraction module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())

            return       
       if not await has_admin_role(ctx):
            return       
       await ctx.defer(ephemeral=True)
       view = discord.ui.View()

       view.add_item(InfractionMultiple(action, reason, notes, expiration, anonymous))
       await ctx.send(f"<:List:1179470251860185159> **{ctx.author.display_name}**, select the users you want to infraction!", view=view)
       
       





    @commands.hybrid_command(description="Infract staff members")
    @app_commands.autocomplete(action=infractiontypes)
    @app_commands.describe(staff="The staff member to infract", action="The action to take", reason="The reason for the action", notes="Additional notes", expiration="The expiration date of the infraction (m/h/d/w)", anonymous="Whether to send the infraction anonymously")
    async def infract(self, ctx: commands.Context, staff: discord.User, action: discord.ext.commands.Range[str, 1, 200], *, reason: discord.ext.commands.Range[str, 1, 2000], notes="", expiration: Optional[str] = None, anonymous: Optional[Literal['True']] = None):
        optionresult = await options.find_one({'guild_id': ctx.guild.id})
        typeactions = await infractiontypeactions.find_one({'guild_id': ctx.guild.id, 'name': action})
        if staff is None:
          await ctx.send(f"{no} **{ctx.author.display_name}**, this user can not be found.", allowed_mentions=discord.AllowedMentions.none())
          return                   
        if optionresult:
            if optionresult.get('infractedbybutton', False) is True:
                view = InfractionIssuer()
                view.issuer.label = f"Issued By {ctx.author.display_name}"
            else:
                view = None    
        else:
            view = None        
        if anonymous == 'True':
         await ctx.defer(ephemeral=True)
        else:
          await ctx.defer() 
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the infraction module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())

            return

        if not await has_admin_role(ctx):
            return

        if ctx.author == staff:
            await ctx.send(f"{no} **{ctx.author.display_name}**, you can't infract yourself.", allowed_mentions=discord.AllowedMentions.none())
            return



        custom = await Customisation.find_one({'guild_id': ctx.guild.id, 'type': 'Infractions'})
        random_string = ''.join(random.choices(string.digits, k=8))
        if (
            expiration
            and not re.match(r'^\d+[mhdws]$', expiration)
        ):
            await ctx.send(f"{no} **{ctx.author.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.", allowed_mentions=discord.AllowedMentions.none())
            return

        if expiration:
            duration_value = int(expiration[:-1])
            duration_unit = expiration[-1]
            duration_seconds = duration_value
            if duration_unit == 'm':
                duration_seconds *= 60
            elif duration_unit == 's':
                duration_seconds *= 1
            elif duration_unit == 'h':
                duration_seconds *= 3600
            elif duration_unit == 'd':
                duration_seconds *= 86400
            elif duration_unit == 'w':
                duration_seconds *= 604800

            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=duration_seconds)
        if custom:
            if expiration:
                replacements = {
                    '{staff.mention}': staff.mention,
                    '{staff.name}': staff.display_name,
                    '{author.mention}': ctx.author.mention,
                    '{author.name}': ctx.author.display_name,
                    '{action}': action,
                    '{reason}': reason,
                    '{notes}': notes,
                    '{expiration}': end_time if expiration else None
                }
            else:
                replacements = {
                    '{staff.mention}': staff.mention,
                    '{staff.name}': staff.display_name,
                    '{author.mention}': ctx.author.mention,
                    '{author.name}': ctx.author.display_name,
                    '{action}': action,
                    '{reason}': reason,
                    '{notes}': notes
                }
            embed_title = await self.replace_variables(custom['title'], replacements)
            embed_description = await self.replace_variables(custom['description'], replacements)

            embed_author = await self.replace_variables(custom['author'], replacements)
            if custom['thumbnail'] == "{staff.avatar}":
                embed_thumbnail = staff.display_avatar
            else:
                embed_thumbnail = custom['thumbnail']

            if custom['author_icon'] == "{author.avatar}":
                if anonymous:
                    authoricon = ctx.guild.icon
                else:
                    authoricon = ctx.author.display_avatar
            else:
                authoricon = custom['author_icon']

            if embed_thumbnail == "None":
                embed_thumbnail = None

            if authoricon == "None":
                authoricon = None

            if embed_author is None:
                embed_author = ""
            embed = discord.Embed(title=embed_title, description=embed_description, color=int(custom['color'], 16))

            embed.set_thumbnail(url=embed_thumbnail)
            if optionresult:
             if optionresult.get('showissuer', True) is False or anonymous == 'True':
                embed.remove_author()
             else:
                embed.set_author(name=embed_author, icon_url=authoricon)
            else:
                if anonymous:
                 embed.remove_author()
                else: 
                 embed.set_author(name=embed_author, icon_url=authoricon)

            embed.set_footer(text=f"Infraction ID | {random_string}")
            if custom['image']:
                embed.set_image(url=custom['image'])
        else:
            if not notes == "" or None:
                embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Reason:** {reason}\n* **Notes:** {notes}", color=discord.Color.dark_embed())
            else:
                embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
            embed.set_thumbnail(url=staff.display_avatar)
            if optionresult:
             if optionresult.get('showissuer', True) is False or anonymous == 'True':
                embed.remove_author()
             else:
                embed.set_author(name=f"Signed, {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
            else:
                if anonymous:
                 embed.remove_author()
                else: 
                 embed.set_author(name=f"Signed, {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
            
            embed.set_footer(text=f"Infraction ID | {random_string}")
            if expiration:
                embed.description = f"{embed.description}\n* **Expiration:** <t:{int(end_time.timestamp())}:D>"

        guild_id = ctx.guild.id
        data = await infchannel.find_one({'guild_id': guild_id})
        consent_data = await consent.find_one({"user_id": staff.id})
        if consent_data is None:
            await consent.insert_one({"user_id": ctx.author.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled", "LOAAlerts": "Enabled"})
            consent_data = {"user_id": ctx.author.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled", "LOAAlerts": "Enabled"}
        if typeactions:
            if typeactions.get('givenroles'):
                roles = typeactions.get('givenroles')
                member = ctx.guild.get_member(staff.id)
                if member:
                 for role_id in roles:  
                    role = ctx.guild.get_role(role_id)
                    try:
                        await member.add_roles(role)  
                    except discord.Forbidden:
                        pass
                    except discord.HTTPException:
                        pass
            if typeactions.get('removedroles'):
                member = ctx.guild.get_member(staff.id)
                if member:                
                 roles = typeactions.get('removedroles')
                 for role_id in roles:  
                    role = ctx.guild.get_role(role_id)
                    try:
                        await member.remove_roles(role)  
                    except discord.Forbidden:
                        pass
                    except discord.HTTPException:
                        pass
 


              
            if typeactions.get('channel'):  
               channel_id = typeactions['channel']
               channel = self.client.get_channel(channel_id)
               if channel:
                try:
                    msg = await channel.send(f"{staff.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False), view=view)
                    await ctx.send(f"{tick} **{ctx.author.display_name}**, I've infracted **@{staff.display_name}**", allowed_mentions=discord.AllowedMentions.none())
                    if expiration:
                        infract_data = {
                            'management': ctx.author.id,
                            'staff': staff.id,
                            'action': action,
                            'reason': reason,
                            'notes': notes,
                            'random_string': random_string,
                            'guild_id': ctx.guild.id,
                            'jump_url': msg.jump_url,
                            'msg_id': msg.id,
                            'timestamp': datetime.now(),
                            'expiration': end_time
                        }
                    else:
                        infract_data = {
                            'management': ctx.author.id,
                            'staff': staff.id,
                            'action': action,
                            'reason': reason,
                            'notes': notes,
                            'random_string': random_string,
                            'guild_id': ctx.guild.id,
                            'jump_url': msg.jump_url,
                            'msg_id': msg.id,
                            'timestamp': datetime.now()
                        }
                    await collection.insert_one(infract_data)
                    if consent_data.get('infractionalert', "Enabled") == "Enabled":
                     try:
                        await staff.send(f"{smallarrow} From **{ctx.guild.name}**", embed=embed)
                     except:
                        print(f"[⚠️] Couldn't send infraction alert to {staff.display_name} in @{ctx.guild.name}")
                        pass
                    else:
                     pass
                    return                    
                except discord.Forbidden:
                     await ctx.send(f"{no} **{ctx.author.display_name}**, I don't have permission to view that channel.", allowed_mentions=discord.AllowedMentions.none())
                     return

               

        if data:
            channel_id = data['channel_id']
            channel = self.client.get_channel(channel_id)

            if channel:
                try:
                    msg = await channel.send(f"{staff.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False), view=view)
                    await ctx.send(f"{tick} **{ctx.author.display_name}**, I've infracted **@{staff.display_name}**", allowed_mentions=discord.AllowedMentions.none())
                    if expiration:
                        infract_data = {
                            'management': ctx.author.id,
                            'staff': staff.id,
                            'action': action,
                            'reason': reason,
                            'notes': notes,
                            'random_string': random_string,
                            'guild_id': ctx.guild.id,
                            'jump_url': msg.jump_url,
                            'msg_id': msg.id,
                            'timestamp': datetime.now(),
                            'expiration': end_time
                        }
                    else:
                        infract_data = {
                            'management': ctx.author.id,
                            'staff': staff.id,
                            'action': action,
                            'reason': reason,
                            'notes': notes,
                            'random_string': random_string,
                            'guild_id': ctx.guild.id,
                            'jump_url': msg.jump_url,
                            'msg_id': msg.id,
                            'timestamp': datetime.now()
                        }
                    await collection.insert_one(infract_data)
                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name}**, I don't have permission to view that channel.", allowed_mentions=discord.AllowedMentions.none())
                    return
                if consent_data.get('infractionalert', "Enabled") == "Enabled":
                    try:
                        await staff.send(f"{smallarrow} From **{ctx.guild.name}**", embed=embed)
                    except:
                        print(f"[⚠️] Couldn't send infraction alert to {staff.display_name} in @{ctx.guild.name}")
                        pass
                else:
                    pass
            else:
                await ctx.send(f"{Warning} **{ctx.author.display_name}**, I don't have permission to view that channel.", allowed_mentions=discord.AllowedMentions.none())
        else:
            await ctx.send(f"{Warning} **{ctx.author.display_name}**, the channel is not set up. Please run `/config`", allowed_mentions=discord.AllowedMentions.none())

    @staticmethod
    async def replace_variables(message, replacements):
        for placeholder, value in replacements.items():
            if value is not None:
                message = str(message).replace(placeholder, str(value))
            else:
                message = str(message).replace(placeholder, "")
        return message





    @commands.hybrid_command(description="View a staff member's infractions")
    @app_commands.describe(staff="The staff member to view infractions for", scope="The scope of infractions to view")
    async def infractions(self, ctx: commands.Context, staff: discord.User, scope: Literal['Voided', 'Expired', 'All'] = None):
        await ctx.defer()
        if staff is None:
          await ctx.send(f"{no} **{ctx.author.display_name}**, this user can not be found.", allowed_mentions=discord.AllowedMentions.none())
          return            
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the infraction module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return

        if not await has_staff_role(ctx):
            return
        embeds = []
        print(f"Searching infractions for staff ID: {staff.id} in guild ID: {ctx.guild.id}")
        if scope == 'Voided':
            filter = {
                'guild_id': ctx.guild.id,
                'staff': staff.id,
                'voided': True
            }
        elif scope == 'Expired':
            filter = {
                'guild_id': ctx.guild.id,
                'staff': staff.id,
                'expired': True
            }
        elif scope == 'All':
            filter = {
                'guild_id': ctx.guild.id,
                'staff': staff.id
            }
        else:
            filter = {
                'guild_id': ctx.guild.id,
                'staff': staff.id,
                'voided': {'$ne': True}
            }

        infractions = await collection.find(filter).to_list(750)

        if not infractions:
            if scope == 'Voided':
                await ctx.send(f"{no} **{ctx.author.display_name}**, there are no voided infractions found for **@{staff.display_name}**.", allowed_mentions=discord.AllowedMentions.none())
            elif scope == 'All':
                await ctx.send(f"{no} **{ctx.author.display_name}**, there are no infractions found for **@{staff.display_name}**.", allowed_mentions=discord.AllowedMentions.none())
            elif scope == 'Expired':
                await ctx.send(f"{no} **{ctx.author.display_name}**, there are no expired infractions found for **@{staff.display_name}**.", allowed_mentions=discord.AllowedMentions.none())
            else:
                await ctx.send(f"{no} **{ctx.author.display_name}**, there are no infractions found for **@{staff.display_name}**.", allowed_mentions=discord.AllowedMentions.none())
            return

        print(f"Found {len(infractions)} infractions for {staff.display_name}")

        embed = discord.Embed(
            title=f"{staff.name}'s Infractions",
            description=f"* **User:** {staff.mention}\n* **User ID:** {staff.id}",
            color=discord.Color.dark_embed()
        )
        if scope == 'Voided':
            embed.title = f"{staff.name}'s Voided Infractions"
        elif scope == 'Expired':
            embed.title = f"{staff.name}'s Expired Infractions"
        elif scope == 'All':
            embed.title = f"{staff.name}'s Infractions"
        embed.set_thumbnail(url=staff.display_avatar)
        embed.set_author(icon_url=staff.display_avatar, name=staff.display_name)
        for i, infraction in enumerate(infractions):
            if infraction.get('voided', 'N/A') == 'N/A':
                voided = ""
            else:
                voided = "**(Voided)**"

            if infraction.get('jump_url', 'N/A') == 'N/A':
                jump_url = ""
            else:
                jump_url = f"\n{arrow}**[Jump to Infraction]({infraction['jump_url']})**"

            if infraction.get('expiration', 'N/A') == 'N/A':
                expiration = ""
            else:
                expiration = f"\n{arrow}**Expiration:** <t:{int(infraction['expiration'].timestamp())}:D>"
                if infraction['expiration'] < datetime.now():
                    expiration = f"\n{arrow}**Expiration:** <t:{int(infraction['expiration'].timestamp())}:D> **(Infraction Expired)**"
            management = f"<@{infraction['management']}>"
            value = f"{arrow}**Infracted By:** {management}\n{arrow}**Action:** {infraction['action']}\n{arrow}**Reason:** {infraction['reason']}\n{arrow}**Notes:** {infraction['notes']}{expiration}{jump_url}"
            if len(value) > 1024:
             value = value[:1021] + "..."
            embed.add_field(
                name=f"<:Document:1166803559422107699> Infraction | {infraction['random_string']} {voided}",
                value=value,
                inline=False
            )
            if (i + 1) % 9 == 0 or i == len(infractions) - 1:
                embeds.append(embed)
                embed = discord.Embed(
                    title=f"{staff.name}'s Infractions",
                    description=f"* **User:** {staff.mention}\n* **User ID:** {staff.id}",
                    color=discord.Color.dark_embed()
                )
                if scope == 'Voided':
                    embed.title = f"{staff.name}'s Voided Infractions"
                elif scope == 'Expired':
                    embed.title = f"{staff.name}'s Expired Infractions"
                elif scope == 'All':
                    embed.title = f"{staff.name}'s Infractions"
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

    @commands.hybrid_group()
    async def infraction(self, ctx: commands.Context):
        return

    @infraction.command(description="Void a staff member's infraction")
    @app_commands.describe(id="The ID of the infraction to void .eg 12345678")
    async def void(self, ctx: commands.Context, id: str):
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the infraction module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return         
     if not await has_admin_role(ctx):
        return

     filter = {
        'guild_id': ctx.guild.id,
        'random_string': id,
        'voided': {'$ne': True}
    }

     infraction = await collection.find_one(filter)

     if infraction is None:
        await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find the infraction with ID `{id}` in this guild.", allowed_mentions=discord.AllowedMentions.none())
        return
     await collection.update_one(filter, {'$set': {'voided': True}})
     
     await ctx.send(f"{tick} **{ctx.author.display_name}**, I've voided the infraction with ID `{id}` in this guild.", allowed_mentions=discord.AllowedMentions.none())
     optionsresult = await options.find_one({'guild_id': ctx.guild.id})
     if (
            optionsresult
            and optionsresult.get('onvoid', False) is True
        ):
         user = self.client.get_user(infraction['staff'])
         if user:
             try:
              await user.send(f"<:CaseRemoved:1191901322723737600> Your infraction with ID `{id}` in {ctx.guild.name} has been voided.")
             except discord.Forbidden:
                 print('[⚠️] I couldn\'t dm the user about their infraction void.')

             return
             


         
    @infraction.command(description="Edit an existing infraction")
    @app_commands.autocomplete(action=infractiontypes)
    async def edit(self, ctx: commands.Context, id: str, action, reason: str, notes: Optional[str]):
      if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, the infraction module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
         return         
      if not await has_admin_role(ctx):
         return
      error = ""
      filter = {
         'guild_id': ctx.guild.id,
         'random_string': id
      }

      infraction = await collection.find_one(filter)

      if infraction is None:
         await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find the infraction with ID `{id}` in this guild.",allowed_mentions=discord.AllowedMentions.none())
         return
      infchannelresult = await infchannel.find_one({'guild_id': ctx.guild.id})
      if infchannelresult is None:
         await ctx.send(f"{no} **{ctx.author.display_name}**, the infraction channel is not setup please run `/config`", allowed_mentions=discord.AllowedMentions.none())
         return
      
      staff = await self.client.fetch_user(infraction['staff']) 
      manager = await self.client.fetch_user(infraction['management'])
      channel_id = infchannelresult['channel_id']
      channel = self.client.get_channel(channel_id)
      
      if infraction.get('msg_id') is None:
       await collection.update_one(filter, {'$set': {'action': action, 'reason': reason, 'notes': notes}})
       await ctx.send(f"{tick} **{ctx.author.display_name}**, I've successfully edited the infraction data with ID `{id}` in this guild. However, I couldn't edit the message.\n{dropdown} Please note that issued infractions before **02/02/2024** cannot have their embeds edited.")
       return
      custom = await Customisation.find_one({'guild_id': ctx.guild.id, 'type': 'Infractions'})
      if custom:
         if channel:
            msg = await channel.fetch_message(infraction['msg_id'])
            if msg is not None:
               staff = await self.client.fetch_user(infraction['staff'])
               replacements = {
            '{staff.mention}': staff.mention,
            '{staff.name}': staff.display_name,
            '{author.mention}': manager.mention,
            '{author.name}': manager.display_name,
            '{action}': action,
            '{reason}': reason,
            '{notes}': notes

           }
               embed_title = await self.replace_variables(custom['title'], replacements)
               embed_description = await self.replace_variables(custom['description'], replacements)
    
               embed_author = await self.replace_variables(custom['author'], replacements)
               if custom['thumbnail'] == "{staff.avatar}":
                 embed_thumbnail = staff.display_avatar
               else:
                 embed_thumbnail = custom['thumbnail']


               if custom['author_icon'] == "{author.avatar}":
                 authoricon = manager.display_avatar
               else:
                 authoricon = custom['author_icon']

               if embed_thumbnail == "None":
                 embed_thumbnail = None

               if authoricon == "None":
                 authoricon = None   
 
               if embed_author is None:
                 embed_author = ""
               embed = discord.Embed(title=embed_title, description=embed_description , color=int(custom['color'], 16))

               embed.set_thumbnail(url=embed_thumbnail)
               embed.set_author(name=embed_author, icon_url=authoricon)
               embed.set_footer(text=f"Infraction ID | {id}")
               if custom['image']:
                 embed.set_image(url=custom['image'])

               try:
                  await msg.edit(embed=embed)
               except (discord.HTTPException, discord.NotFound):
                  error = "<:Crisis:1223063318252748932> I couldn't edit the infraction embed."
            else:
               pass      
      else:
         msg = await channel.fetch_message(infraction['msg_id'])
         
         if msg is not None:  
            staff = await self.client.fetch_user(infraction['staff'])         
            if notes is None:
               notes = infraction['notes']
            if notes == 'None' or notes is None:   
               embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
            else:
               embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Reason:** {reason}\n* **Notes:** {notes}", color=discord.Color.dark_embed())
            manager = await self.client.fetch_user(infraction['management'])  
            embed.set_thumbnail(url=staff.display_avatar)
            embed.set_author(name=f"Signed, {manager.display_name}", icon_url=manager.display_avatar)
            embed.set_footer(text=f"Infraction ID | {id}")                
            try:
               await msg.edit(embed=embed)
               print(f"Edited the infraction embed for ID: {id}")
            except (discord.HTTPException, discord.NotFound):
                  error = "<:Crisis:1223063318252748932> I couldn't edit the infraction embed."      
         else:
            pass                   
      await collection.update_one(filter, {'$set': {'action': action, 'reason': reason, 'notes': notes}})

      await ctx.send(f"{tick} **{ctx.author.display_name}**, I've edited the infraction with ID `{id}` in this guild.\n{error}", allowed_mentions=discord.AllowedMentions.none())


    @tasks.loop(minutes=3)
    async def check_infractions(self):
        try:
            infractions = collection.find({
                'expiration': {'$exists': True},
                'expired': {'$ne': True}
            })
            infractions = await infractions.to_list(None)
            if infractions:
                for infraction in infractions:
                    guild = self.client.get_guild(infraction['guild_id'])
                    if guild is None:
                        await collection.update_one(
                            {'random_string': infraction['random_string']},
                            {'$set': {'expired': True}}
                        )
                        print('[🛈 INFO] Guild was None so I expired the infraction.')
                        continue

                    if infraction['expiration'] < datetime.now():
                        await collection.update_one(
                            {'random_string': infraction['random_string']},
                            {'$set': {'expired': True}}
                        )
                        print(f"[✅] Updated expired infraction with ID: {infraction['random_string']}")

                        if infraction.get('msg_id') is not None:
                            infchannelresult = await infchannel.find_one({'guild_id': guild.id})
                            if infchannelresult is None:
                                continue

                            channel_id = infchannelresult['channel_id']
                            channel = self.client.get_channel(channel_id)

                            if channel:
                                msg = await channel.fetch_message(infraction['msg_id'])
                                if msg:
                                    await msg.reply("<:CaseRemoved:1191901322723737600> Infraction has **expired**.")
                                    await msg.edit(content=f"{msg.content} • **Infraction Expired.**")
                                    print(f"[✅] Updated expired infraction message with ID: {infraction['random_string']}")

        except Exception as e:
            print(f"Error checking infractions: {e}")


class InfractionMultiple(discord.ui.UserSelect):
    def __init__(self, action, reason, notes, expiration, anonymous):


        super().__init__(placeholder='Members', max_values=10, min_values=1) 
        self.action = action
        self.reason = reason
        self.notes = notes
        self.expiration = expiration
        self.anonymous = anonymous

    async def callback(self, interaction: discord.Interaction):      
            await interaction.response.defer(ephemeral=True)
            action = self.action
            reason = self.reason
            notes = self.notes
            expiration = self.expiration
            anonymous = self.anonymous
            optionresult = await options.find_one({'guild_id': interaction.guild_id})
            typeactions = await infractiontypeactions.find_one({'guild_id': interaction.guild.id, 'name': action})
            if optionresult:
                if optionresult.get('infractedbybutton', False) is True:
                    view = InfractionIssuer()
                    view.issuer.label = f"Issued By {interaction.user.display_name}"
                else:
                    view = None    
            else:
                view = None               


            for user in self.values:
                if user is None:
                  await interaction.followup.send(f"{no} **{interaction.user.display_name}**, this user can not be found.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                  return                   


                if interaction.user == user:
                    await interaction.followup.send(f"{no} **{interaction.user.display_name}**, you can't infract yourself.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                    return



                custom = await Customisation.find_one({'guild_id': interaction.guild_id, 'type': 'Infractions'})
                random_string = ''.join(random.choices(string.digits, k=8))
                if (
                    expiration
                    and not re.match(r'^\d+[mhdws]$', expiration)
                ):
                    await interaction.followup.send(f"{no} **{interaction.user.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                    return

                if expiration:
                    duration_value = int(expiration[:-1])
                    duration_unit = expiration[-1]
                    duration_seconds = duration_value
                    if duration_unit == 'm':
                        duration_seconds *= 60
                    elif duration_unit == 's':
                        duration_seconds *= 1
                    elif duration_unit == 'h':
                        duration_seconds *= 3600
                    elif duration_unit == 'd':
                        duration_seconds *= 86400
                    elif duration_unit == 'w':
                        duration_seconds *= 604800

                    start_time = datetime.now()
                    end_time = start_time + timedelta(seconds=duration_seconds)
                if custom:
                    if expiration:
                        replacements = {
                            '{staff.mention}': user.mention,
                            '{staff.name}': user.display_name,
                            '{author.mention}': interaction.user.mention,
                            '{author.name}': interaction.user.display_name,
                            '{action}': action,
                            '{reason}': reason,
                            '{notes}': notes,
                            '{expiration}': end_time if expiration else None
                        }
                    else:
                        replacements = {
                            '{staff.mention}': user.mention,
                            '{staff.name}': user.display_name,
                            '{author.mention}': interaction.user.mention,
                            '{author.name}': interaction.user.display_name,
                            '{action}': action,
                            '{reason}': reason,
                            '{notes}': notes
                        }
                    embed_title = await self.replace_variables(custom['title'], replacements)
                    embed_description = await self.replace_variables(custom['description'], replacements)

                    embed_author = await self.replace_variables(custom['author'], replacements)
                    if custom['thumbnail'] == "{staff.avatar}":
                        embed_thumbnail = user.display_avatar
                    else:
                        embed_thumbnail = custom['thumbnail']

                    if custom['author_icon'] == "{author.avatar}":
                        if anonymous == 'True':
                            authoricon = interaction.guild.icon
                        else:
                            authoricon = interaction.user.display_avatar
                    else:
                        authoricon = custom['author_icon']

                    if embed_thumbnail == "None":
                        embed_thumbnail = None

                    if authoricon == "None":
                        authoricon = None

                    if embed_author is None:
                        embed_author = ""
                    embed = discord.Embed(title=embed_title, description=embed_description, color=int(custom['color'], 16))

                    embed.set_thumbnail(url=embed_thumbnail)
                    if optionresult:
                     if optionresult.get('showissuer', True) is False or anonymous == 'True':
                        embed.remove_author()
                     else:
                        embed.set_author(name=embed_author, icon_url=authoricon)
                    else:
                        if anonymous:
                         embed.remove_author()
                        else: 
                         embed.set_author(name=embed_author, icon_url=authoricon)

                    embed.set_footer(text=f"Infraction ID | {random_string}")
                    if custom['image']:
                        embed.set_image(url=custom['image'])
                else:
                    if not notes == "" or None:
                        embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {user.mention}\n* **Action:** {action}\n* **Reason:** {reason}\n* **Notes:** {notes}", color=discord.Color.dark_embed())
                    else:
                        embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {user.mention}\n* **Action:** {action}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
                    embed.set_thumbnail(url=user.display_avatar)
                    if optionresult:
                     if optionresult.get('showissuer', True) is False or anonymous == 'True':
                        embed.remove_author()
                     else:
                        embed.set_author(name=f"Signed, {interaction.user.display_name}", icon_url=interaction.user.display_avatar)
                    else:
                        if anonymous:
                         embed.remove_author()
                        else: 
                         embed.set_author(name=f"Signed, {interaction.user.display_name}", icon_url=interaction.user.display_avatar)
            
                    embed.set_footer(text=f"Infraction ID | {random_string}")
                    if expiration:
                        embed.description = f"{embed.description}\n* **Expiration:** <t:{int(end_time.timestamp())}:D>"

                guild_id = interaction.guild.id
                data = await infchannel.find_one({'guild_id': guild_id})
                consent_data = await consent.find_one({"user_id": user.id})
                
                if consent_data is None:
                    await consent.insert_one({"user_id": interaction.user.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled", "LOAAlerts": "Enabled"})
                    consent_data = {"user_id": interaction.user.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled", "LOAAlerts": "Enabled"}
                if typeactions:
                    if typeactions.get('givenroles'):
                        roles = typeactions.get('givenroles')
                        member = interaction.guild.get_member(user.id)
                        if member:
                         for role_id in roles:  
                            role = interaction.guild.get_role(role_id)
                            try:
                                await member.add_roles(role)  
                            except discord.Forbidden:
                                pass
                            except discord.HTTPException:
                                pass
                    if typeactions.get('removedroles'):
                        member = interaction.guild.get_member(user.id)
                        if member:                
                         roles = typeactions.get('removedroles')
                         for role_id in roles:  
                            role = interaction.guild.get_role(role_id)
                            try:
                                await member.remove_roles(role)  
                            except discord.Forbidden:
                                pass
                            except discord.HTTPException:
                                pass
 


              
                    if typeactions.get('channel'):  
                       channel_id = typeactions['channel']
                       channel = interaction.guild.get_channel(channel_id)
                       if channel:
                        try:
                            msg = await channel.send(f"{user.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False), view=view)
                            await interaction.edit_original_response(content=f"{tick} **{interaction.user.display_name}**, I've infracted **@{user.display_name}**", allowed_mentions=discord.AllowedMentions.none(), view=None)
                            if expiration:
                                infract_data = {
                                    'management': interaction.user.id,
                                    'staff': user.id,
                                    'action': action,
                                    'reason': reason,
                                    'notes': notes,
                                    'random_string': random_string,
                                    'guild_id': interaction.guild.id,
                                    'jump_url': msg.jump_url,
                                    'msg_id': msg.id,
                                    'timestamp': datetime.now(),
                                    'expiration': end_time
                                }
                            else:
                                infract_data = {
                                    'management': interaction.user.id,
                                    'staff': user.id,
                                    'action': action,
                                    'reason': reason,
                                    'notes': notes,
                                    'random_string': random_string,
                                    'guild_id': interaction.guild.id,
                                    'jump_url': msg.jump_url,
                                    'msg_id': msg.id,
                                    'timestamp': datetime.now()
                                }
                            await collection.insert_one(infract_data)
                            if consent_data.get('infractionalert', "Enabled") == "Enabled":
                             try:
                                await user.send(f"{smallarrow} From **{interaction.guild.name}**", embed=embed)
                             except:
                                print(f"[⚠️] Couldn't send infraction alert to {user.display_name} in @{interaction.guild.name}")
                                pass
                            else:
                             pass
                            return                    
                        except discord.Forbidden:
                             await interaction.edit_original_response(f"{no} **{interaction.user.display_name}**, I don't have permission to view that channel.", allowed_mentions=discord.AllowedMentions.none(), view=None)
                             return

               

                if data:
                    channel_id = data['channel_id']
                    channel = interaction.guild.get_channel(channel_id)

                    if channel:
                        try:
                            msg = await channel.send(f"{user.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False), view=view)
                            if expiration:
                                infract_data = {
                                    'management': interaction.user.id,
                                    'staff': user.id,
                                    'action': action,
                                    'reason': reason,
                                    'notes': notes,
                                    'random_string': random_string,
                                    'guild_id': interaction.guild.id,
                                    'jump_url': msg.jump_url,
                                    'msg_id': msg.id,
                                    'timestamp': datetime.now(),
                                    'expiration': end_time
                                }
                            else:
                                infract_data = {
                                    'management': interaction.user.id,
                                    'staff': user.id,
                                    'action': action,
                                    'reason': reason,
                                    'notes': notes,
                                    'random_string': random_string,
                                    'guild_id': interaction.guild.id,
                                    'jump_url': msg.jump_url,
                                    'msg_id': msg.id,
                                    'timestamp': datetime.now()
                                }
                            await collection.insert_one(infract_data)
                        except discord.Forbidden:
                            await interaction.edit_original_response(f"{no} **{interaction.user.display_name}**, I don't have permission to view that channel.", allowed_mentions=discord.AllowedMentions.none(), view=None)
                            return
                        if consent_data.get('infractionalert', "Enabled") == "Enabled":
                            try:
                                await user.send(f"{smallarrow} From **{interaction.guild.name}**", embed=embed)
                            except:
                                print(f"[⚠️] Couldn't send infraction alert to {user.display_name} in @{interaction.guild.name}")
                                pass
                        else:
                            pass
                    else:
                        await interaction.edit_original_response(f"{Warning} **{interaction.user.display_name}**, the channel is not set up. Please run `/config`", allowed_mentions=discord.AllowedMentions.none(), view=None)
                        return
                else:
                    await interaction.edit_original_response(f"{Warning} **{interaction.user.display_name}**, the channel is not set up. Please run `/config`", allowed_mentions=discord.AllowedMentions.none(), view=None)
                    return
            await interaction.edit_original_response(content=f"{tick} **{interaction.user.display_name}**, I've infracted the staff members.", allowed_mentions=discord.AllowedMentions.none(), view=None)

class PRemium(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="Premium", emoji="<:Tip:1167083259444875264>",style=discord.ButtonStyle.link, url="https://patreon.com/astrobirb/membership"))


       
class InfractionIssuer(discord.ui.View):
    def __init__(self):
        super().__init__()


    @discord.ui.button(label=f"", style=discord.ButtonStyle.grey, disabled=True, emoji="<:flag:1166508151290462239>")
    async def issuer(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass
           


async def setup(client: commands.Bot) -> None:
   await client.add_cog(Infractions(client))       
