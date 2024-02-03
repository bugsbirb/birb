
import discord
from discord.ext import commands
from typing import Literal
import random
import string
from typing import Optional
import sqlite3
from discord.ext import commands
import typing
from pymongo import MongoClient
import os
from dotenv import load_dotenv

from emojis import *
from permissions import *
from datetime import datetime, timedelta
import discord
from discord.ext import tasks
MONGO_URL = os.getenv('MONGO_URL')
client = MongoClient(MONGO_URL)
db = client['astro']
collection = db['infractions']
scollection = db['staffrole']
arole = db['adminrole']
infchannel = db['infraction channel']
appealable = db['Appeal Toggle']
appealschannel = db['Appeals Channel']
consent = db['consent']
modules = db['Modules']
Customisation = db['Customisation']
infractiontypes = db['infractiontypes']


class Infractions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        loop = self.check_infractions.start()
        if loop:
            print("Infractions loop started.")




    async def modulecheck(self, ctx): 
     modulesdata = modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['infractions'] == True:   
        return True

     
    async def infractiontypes(
    self,
    interaction: discord.Interaction,
    current: str
) -> typing.List[app_commands.Choice[str]]:
     filter = {
        'guild_id': interaction.guild_id 
    }

     try:
        tag_names = infractiontypes.distinct("types", filter)
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
 

    @commands.hybrid_command(description="Infract staff members")
    @app_commands.autocomplete(action=infractiontypes)
    @app_commands.describe(staff="The staff member to infract", action="The action to take", reason="The reason for the action", notes="Additional notes", expiration="The expiration date of the infraction (m/h/d/w)", annoymous="Whether to send the infraction anonymously")
    async def infract(self, ctx, staff: discord.Member,  action, reason: str, notes: Optional[str], expiration: Optional[str] = None, annoymous = False):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return    

        if not await has_admin_role(ctx):
   
         return           

        if ctx.author == staff:
         await ctx.send(f"{no} **{ctx.author.display_name}**, you can't infract yourself.")
         return


        custom = Customisation.find_one({'guild_id': ctx.guild.id, 'type': 'Infractions'})
        random_string = ''.join(random.choices(string.digits, k=8))
        if expiration:
          if not re.match(r'^\d+[mhdws]$', expiration):
           await ctx.send(f"{no} **{ctx.author.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.")
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
              if annoymous:
                 authoricon = ctx.guild.icon
              else:  
                authoricon = ctx.author.display_avatar
           else:
              authoricon = custom['author_icon']

           if embed_thumbnail == "None":
              embed_thumbnail = None

           if authoricon == "None":
              authoricon = None   
 
           if embed_author == None:
              embed_author = ""
           embed = discord.Embed(title=embed_title, description=embed_description , color=int(custom['color'], 16))

           embed.set_thumbnail(url=embed_thumbnail)
           if annoymous == True:
              embed.remove_author()
           else:
            embed.set_author(name=embed_author, icon_url=authoricon)
           embed.set_footer(text=f"Infraction ID | {random_string}")
           if custom['image']:
              embed.set_image(url=custom['image'])
       

        else:
              
         if notes:
          embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Reason:** {reason}\n* **Notes:** {notes}", color=discord.Color.dark_embed())
         else:
          embed = discord.Embed(title="Staff Consequences & Discipline", description=f"* **Staff Member:** {staff.mention}\n* **Action:** {action}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
         embed.set_thumbnail(url=staff.display_avatar)
         if annoymous == True:
          embed.remove_author()
         else:
          embed.set_author(name=f"Signed, {staff.display_name}", icon_url=staff.display_avatar)
         
         embed.set_footer(text=f"Infraction ID | {random_string}")
         if expiration:
           embed.description = f"{embed.description}\n* **Expiration:** <t:{int(end_time.timestamp())}:D>"

        guild_id = ctx.guild.id
        data = infchannel.find_one({'guild_id': guild_id})
        consent_data = consent.find_one({"user_id": staff.id})
        if consent_data is None:
            consent.insert_one({"user_id": staff.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled"})            
            consent_data = {"user_id": staff.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled"}


        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)

         if channel:      

            try:
             msg = await channel.send(f"{staff.mention}", embed=embed)
             await ctx.send(f"{tick} **{ctx.author.display_name}**, I've infracted **@{staff.display_name}**")
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
             collection.insert_one(infract_data)
            except discord.Forbidden: 
             await ctx.send(f"{no} **{ctx.author.display_name}**, I don't have permission to view that channel.")             
             return
            if consent_data['infractionalert'] == "Enabled":
             try:
                await staff.send(f"<:SmallArrow:1140288951861649418> From **{ctx.guild.name}**", embed=embed)
             except discord.Forbidden:
                pass
            else:
                pass
         else:
            await ctx.send(f"{Warning} **{ctx.author.display_name}**, I don't have permission to view that channel.")
        else:
          await ctx.send(f"{Warning} **{ctx.author.display_name}**, the channel is not setup please run `/config`")

    async def replace_variables(self, message, replacements):
     for placeholder, value in replacements.items():
        if value is not None:
            message = str(message).replace(placeholder, str(value))
        else:
            message = str(message).replace(placeholder, "")  
     return message


    @commands.hybrid_command(description="View a staff members infractions")
    @app_commands.describe(staff="The staff member to view infractions for", scope="The scope of infractions to view")
    async def infractions(self, ctx, staff: discord.Member, scope: Literal['Voided', 'Expired', 'All'] = None):
     await ctx.defer()
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return    

     if not await has_staff_role(ctx):
         return               

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

     infractions = collection.find(filter)

     infraction_list = []

     for infraction in infractions:
        infraction_info = {
            'id': infraction['random_string'],
            'action': infraction['action'],
            'reason': infraction['reason'],
            'notes': infraction['notes'],
            'management': infraction['management'],
            'jump_url': infraction['jump_url'] if 'jump_url' in infraction else 'N/A',
            'expiration': infraction['expiration'] if 'expiration' in infraction else 'N/A',
            'expired': infraction['expired'] if 'expired' in infraction else 'N/A',
            'voided': infraction['voided'] if 'voided' in infraction else 'N/A'
        }
        infraction_list.append(infraction_info)

     if not infraction_list:
        await ctx.send(f"{no} **{ctx.author.display_name}**, there is no infractions found for **@{staff.display_name}**.")
        return
     
     print(f"Found {len(infraction_list)} infractions for {staff.display_name}")

     
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
     for infraction_info in infraction_list:
        if infraction_info.get('voided', 'N/A') == 'N/A':
         voided = ""
        else:
         voided = "**(Voided)**" 


        if infraction_info['jump_url'] == 'N/A':
         jump_url = ""
        else:
         jump_url = f"<:arrow:1166529434493386823>**[Jump to Infraction]({infraction_info['jump_url']})**"
         
        if infraction_info['expiration'] == 'N/A':
         expiration = ""
        else:
         expiration = f"<:arrow:1166529434493386823>**Expiration:** <t:{int(infraction_info['expiration'].timestamp())}:D>"
         if infraction_info['expiration'] < datetime.now():
            expiration = f"<:arrow:1166529434493386823>**Expiration:** <t:{int(infraction_info['expiration'].timestamp())}:D> **(Infraction Expired)**"
        management = await self.client.fetch_user(infraction_info['management'])        
        embed.add_field(
            name=f"<:Document:1166803559422107699> Infraction | {infraction_info['id']} {voided}",
            value=f"<:arrow:1166529434493386823>**Infracted By:** {management.mention}\n<:arrow:1166529434493386823>**Action:** {infraction_info['action']}\n<:arrow:1166529434493386823>**Reason:** {infraction_info['reason']}\n<:arrow:1166529434493386823>**Notes:** {infraction_info['notes']}\n{expiration}\n{jump_url}",
            inline=False
        )

     await ctx.send(embed=embed)

    @commands.hybrid_group()
    async def infraction(self, ctx):
        return

    @infraction.command(description="Void a staff member's infraction")
    @app_commands.describe(id="The ID of the infraction to void .eg 12345678")
    async def void(self, ctx, id: str):
     if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return         
     if not await has_admin_role(ctx):
        return

     filter = {
        'guild_id': ctx.guild.id,
        'random_string': id
    }

     infraction = collection.find_one(filter)

     if infraction is None:
        await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find the infraction with ID `{id}` in this guild.")
        return
     collection.update_one(filter, {'$set': {'voided': True}})
 
     await ctx.send(f"{tick} **{ctx.author.display_name}**, I've voided the infraction with ID `{id}` in this guild.")
     
    @infraction.command(description="Edit an existing infraction")
    @app_commands.autocomplete(action=infractiontypes)
    async def edit(self, ctx, id: str, action, reason: str, notes: Optional[str]):
      if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return         
      if not await has_admin_role(ctx):
         return
      error = ""
      filter = {
         'guild_id': ctx.guild.id,
         'random_string': id
      }

      infraction = collection.find_one(filter)

      if infraction is None:
         await ctx.send(f"{no} **{ctx.author.display_name}**, I couldn't find the infraction with ID `{id}` in this guild.")
         return
      infchannelresult = infchannel.find_one({'guild_id': ctx.guild.id})
      if infchannelresult is None:
         await ctx.send(f"{no} **{ctx.author.display_name}**, the infraction channel is not setup please run `/config`")
         return
      
      staff = await self.client.fetch_user(infraction['staff']) 
      manager = await self.client.fetch_user(infraction['management'])
      channel_id = infchannelresult['channel_id']
      channel = self.client.get_channel(channel_id)
      
      if infraction.get('msg_id')is None:
       collection.update_one(filter, {'$set': {'action': action, 'reason': reason, 'notes': notes}})
       await ctx.send(f"{tick} **{ctx.author.display_name}**, I've successfully edited the infraction data with ID `{id}` in this guild. However, I couldn't edit the message.\n{dropdown} Please note that issued infractions before **02/02/2024** cannot have their embeds edited.")
       return
      custom = Customisation.find_one({'guild_id': ctx.guild.id, 'type': 'Infractions'})
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
 
               if embed_author == None:
                 embed_author = ""
               embed = discord.Embed(title=embed_title, description=embed_description , color=int(custom['color'], 16))

               embed.set_thumbnail(url=embed_thumbnail)
               embed.set_author(name=embed_author, icon_url=authoricon)
               embed.set_footer(text=f"Infraction ID | {id}")
               if custom['image']:
                 embed.set_image(url=custom['image'])

               try:
                  await msg.edit(embed=embed)
               except discord.HTTPException or discord.NotFound:
                  error = f"<:Crisis:1190412318648062113> I couldn't edit the infraction embed."
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
            except discord.HTTPException or discord.NotFound:
                  error = f"<:Crisis:1190412318648062113> I couldn't edit the infraction embed."      
         else:
            pass                   
      collection.update_one(filter, {'$set': {'action': action, 'reason': reason, 'notes': notes}})

      await ctx.send(f"{tick} **{ctx.author.display_name}**, I've edited the infraction with ID `{id}` in this guild.\n{error}")


    @tasks.loop(seconds=10)
    async def check_infractions(self):

      try:
         infractions = collection.find({'expiration': {'$exists': True}, 'expired': {'$ne': True}})

         if infractions:
            for infraction in infractions:

               guild = self.client.get_guild(infraction['guild_id'])
               if guild is None:
                  print('no guild')
                  return 

               if infraction['expiration'] < datetime.now():

                  collection.update_one({'random_string': infraction['random_string']}, {'$set': {'expired': True}})
                  print(f"Updated expired infraction with ID: {infraction['random_string']}")
                  if infraction.get('msg_id') is not None:
                     infchannelresult = infchannel.find_one({'guild_id': guild.id})
                     if infchannelresult is None:
                        return
                     channel_id = infchannelresult['channel_id']
                     channel = self.client.get_channel(channel_id)
                     if channel:

                        msg = await channel.fetch_message(infraction['msg_id'])
                        if msg is not None:
                           
                           
                           await msg.reply(f"<:CaseRemoved:1191901322723737600> Infraction has **expired**.")
                           await msg.edit(content=f"{msg.content} • **Infraction Expired.**")
                           print(f"Updated expired infraction message with ID: {infraction['random_string']}")
      except Exception as e:
         print(f"Error checking infractions: {e}")
         self.check_infractions.restart()
         return

async def setup(client: commands.Bot) -> None:
   await client.add_cog(Infractions(client))       
