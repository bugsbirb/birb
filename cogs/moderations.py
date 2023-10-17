import discord
from discord.ext import commands
import random
from datetime import datetime
from typing import Union, Optional
from typing import Literal
from pymongo import MongoClient
import typing
from discord import ui
from emojis import *
import string
import Paginator
import datetime
import time
from datetime import timedelta
import pytz
from datetime import datetime, timedelta
client = MongoClient('mongodb+srv://deezbird2768:JsVErbxMhh3MlDV2@cluster0.oi5ddvf.mongodb.net/')
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
moderations = db['Moderations']
ModerationPoints = db['Moderations Points']
warningrole = db['WarnRole']
kickrole = db['KickRole']
banrole = db['BanRole']
muterole = db['MuteRole']
ModerationChannel = db['Moderations Channel']
WarningPointValue = db['Warning Value']
MutePointValue = db['Mute Value']
KickPointValue = db['Kick Value']
SoftBanPointValue = db['Softban Value']
BanPointValue = db['Ban Value']
MaxPointValue = db['Max Point Value']

AutoBanValue = db['Points Autoban Config']
class ModerationModule(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def has_warning_role(self, ctx):
        filter = {
            'guild_id': ctx.guild.id
        }
        staff_data = warningrole.find_one(filter)

        if staff_data and 'staffrole' in staff_data:
            staff_role_id = staff_data['staffrole']
            staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_id)

            if staff_role and staff_role in ctx.author.roles:
                return True

        return False

    async def has_kick_role(self, ctx):
        filter = {
            'guild_id': ctx.guild.id
        }
        staff_data = kickrole.find_one(filter)

        if staff_data and 'staffrole' in staff_data:
            staff_role_id = staff_data['staffrole']
            staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_id)

            if staff_role and staff_role in ctx.author.roles:
                return True

        return False

    async def has_mute_role(self, ctx):
        filter = {
            'guild_id': ctx.guild.id
        }
        staff_data = muterole.find_one(filter)

        if staff_data and 'staffrole' in staff_data:
            staff_role_id = staff_data['staffrole']
            staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_id)

            if staff_role and staff_role in ctx.author.roles:
                return True

        return False


    async def has_ban_role(self, ctx):
        filter = {
            'guild_id': ctx.guild.id
        }
        staff_data = banrole.find_one(filter)

        if staff_data and 'staffrole' in staff_data:
            staff_role_id = staff_data['staffrole']
            staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_id)

            if staff_role and staff_role in ctx.author.roles:
                return True

        return False        

    async def has_moderation_role(self, ctx):
     filter = {
        'guild_id': ctx.guild.id
    }

     warning_role_data = warningrole.find_one(filter)
     kick_role_data = kickrole.find_one(filter)
     ban_role_data = banrole.find_one(filter)

     roles_data = [warning_role_data, kick_role_data, ban_role_data]

     for role_data in roles_data:
        if role_data and 'staffrole' in role_data:
            staff_role_id = role_data['staffrole']
            staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_id)

            if staff_role and staff_role in ctx.author.roles:
                return True

     return False

    @commands.hybrid_command(description="Sends a warning to the user.")
    async def warn(self, ctx, user: discord.Member,*, reason: str):
        if not await self.has_warning_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return                
        if user.top_role >= ctx.author.top_role:
         await ctx.send(f"{no} You can't warn someone with a higher or equal role.")
         return
        timezone = pytz.timezone('Europe/Paris')
        moderated = datetime.now(timezone)
        moderatedform = f"<t:{int(moderated.timestamp())}:t>"
        random_string = ''.join(random.choices(string.digits, k=8))
        filter = {
        'guild_id': ctx.guild.id,
        'user_id': user.id,
    }
        points = ModerationPoints.find(filter)
        
        pointvalue = WarningPointValue.find_one({'guild_id': ctx.guild.id})
 
        if pointvalue:
         pointsv = pointvalue['pointvalue']
        else:
         pointsv = 2  
        pointsv = int(pointsv)
        ModerationPoints.update_one({'guild_id': ctx.guild.id, 'user_id': user.id}, {'$inc': {'points': pointsv}}, upsert=True)
        points_value = 0
        for document in points: 
            points_value = document['points']

        max_point_value_data = MaxPointValue.find_one({'guild_id': ctx.guild.id})
        if max_point_value_data:
         max_points = max_point_value_data['pointvalue']
        else:
         max_points = 10            
        if points_value >= max_points:         
         msg = await ctx.send(f"{tick} **@{user.display_name}**, has been warned.\n<:ArrowDropDown:1163171628050563153> they have reached the max points `{points_value}/{max_points}` **points**")
         try:
          msg2 = await user.send(f"<:Infraction:1162134605885870180> You've been warned **@{ctx.guild.name}** for **{reason}**\n <:ArrowDropDown:1163171628050563153> you have reach the max points `{points_value}/{max_points}` **points**")
         except discord.Forbidden:
                pass               
         autoban = AutoBanValue.find_one({'guild_id': ctx.guild.id})

         if autoban:
            appeal_enabled = autoban.get('toggle', False)
         else:
            appeal_enabled = False

         if appeal_enabled:
            await msg.reply(f"{tick} **Autobanned**, reached max points.")
            await msg2.reply(f"<:Infraction:1162134605885870180> **Autobanned**, you've reached the max points.")
            await user.ban(reason="Hit maxed amount of points")
            random_string = ''.join(random.choices(string.digits, k=8))
            moderation_data = {
            'guild_id': ctx.guild.id,
            'user': user.id,
            'reason': 'User hit max points',
            'type': 'Autoban',            
            'id': random_string,
            'moderator': '@Astro Birb',            
            'timestamp': moderatedform
        }
            moderations.insert_one(moderation_data)
            data = ModerationChannel.find_one({'guild_id': ctx.guild.id})
            if data:
             channel_id = data['channel_id']
             channel = self.client.get_channel(channel_id)             
             if channel:
                
                embed = discord.Embed(title=f"Auto Banned", description=f"* **User:** {user.mention}(`{user.id}`)\n* **Moderator:** **@{ctx.author.display_name}**\n* **Reason:** `Hit Max Points`\n* **Occured:** {moderatedform}\n* **User Points:** {points_value}",color=discord.Color.dark_embed())
                embed.set_author(name=user.display_name, icon_url=user.display_avatar)
                embed.set_footer(text=f"Moderation ID | {random_string}")
                embed.set_thumbnail(url=user.display_avatar)
                await channel.send(embed=embed)
             else:   
                pass            
        else: 
            try:

             await user.send(f"<:Infraction:1162134605885870180> You've been warned **@{ctx.guild.name}** for **{reason}**\n <:ArrowDropDown:1163171628050563153> you now have `{points_value}/{max_points}` **points**")
            except discord.Forbidden:
                pass             
            await ctx.send(f"{tick} **@{user.display_name}**, has been warned.\n<:ArrowDropDown:1163171628050563153> they now have `{points_value}/{max_points}` **points**")        

        moderation_data = {
            'guild_id': ctx.guild.id,
            'user': user.id,
            'reason': reason,
            'type': 'warn',             
            'id': random_string,
            'moderator': ctx.author.id,
            'timestamp': moderatedform
        }
        moderations.insert_one(moderation_data)
        data = ModerationChannel.find_one({'guild_id': ctx.guild.id})
        if data:
          channel_id = data['channel_id']
          channel = self.client.get_channel(channel_id)            
          if channel:
            embed = discord.Embed(title=f"Warning", description=f"* **User:** {user.mention}(`{user.id}`)\n* **Moderator:** **@{ctx.author.display_name}**\n* **Reason:** {reason}\n* **Occured:** {moderatedform}\n* **User Points:** {points_value}", color=discord.Color.dark_embed())
            embed.set_author(name=user.display_name, icon_url=user.display_avatar)
            embed.set_footer(text=f"Moderation ID | {random_string}")
            embed.set_thumbnail(url=user.display_avatar)
            await channel.send(embed=embed)

    @commands.hybrid_command(description="Mutes a user for a period of time.")
    async def mute(self, ctx, user: discord.Member,duration: str ,*, reason: str):
        if not await self.has_mute_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return                
        if user.top_role >= ctx.author.top_role:
         await ctx.send(f"{no} You can't warn someone with a higher or equal role.")
         return         
        random_string = ''.join(random.choices(string.digits, k=8))
        filter = {
        'guild_id': ctx.guild.id,
        'user_id': user.id,
    }
        points = ModerationPoints.find(filter)
        pointvalue = MutePointValue.find_one({'guild_id': ctx.guild.id})
        timezone = pytz.timezone('Europe/Paris')
        moderated = datetime.now(timezone)
        moderatedform = f"<t:{int(moderated.timestamp())}:t>"
        if pointvalue:
         pointsv = pointvalue['pointvalue']
        else:
         pointsv = 3  
        pointsv = int(pointsv)
        ModerationPoints.update_one({'guild_id': ctx.guild.id, 'user_id': user.id}, {'$inc': {'points': pointsv}}, upsert=True)
        points_value = 0        
        for document in points: 
            points_value = document['points']
        max_point_value_data = MaxPointValue.find_one({'guild_id': ctx.guild.id})
        if max_point_value_data:
         max_points = max_point_value_data['pointvalue']
        else:
         max_points = 10            
        if points_value >= max_points:         
         msg = await ctx.send(f"{tick} **@{user.display_name}**, has been muted.\n<:ArrowDropDown:1163171628050563153> they have reached the max points `{points_value}/{max_points}` **points**")
         try:
          msg2 = await user.send(f"<:Infraction:1162134605885870180> You've been muted **@{ctx.guild.name}** for **{reason}**\n <:ArrowDropDown:1163171628050563153> you have reach the max points `{points_value}/{max_points}` **points**")
         except discord.Forbidden:
                pass     
         autoban = AutoBanValue.find_one({'guild_id': ctx.guild.id})

         if autoban:
            appeal_enabled = autoban.get('toggle', False)
         else:
            appeal_enabled = False

         if appeal_enabled:
            await msg.reply(f"{tick} **Autobanned**, reached max points.")
            await msg2.reply(f"<:Infraction:1162134605885870180> **Autobanned**, you've reached the max points.")
            await user.ban(reason="Hit maxed amount of points")
                
            random_string = ''.join(random.choices(string.digits, k=8))
            moderation_data = {
            'guild_id': ctx.guild.id,
            'user': user.id,
            'reason': 'User hit max points',
            'type': 'Autoban',            
            'id': random_string,
            'moderator': '@Astro Birb',            
            'timestamp': moderatedform
        }
            moderations.insert_one(moderation_data)
            data = ModerationChannel.find_one({'guild_id': ctx.guild.id})
            if data:
             channel_id = data['channel_id']
             channel = self.client.get_channel(channel_id)             
             if channel:
                
                embed = discord.Embed(title=f"Auto Banned", description=f"* **User:** {user.mention}(`{user.id}`)\n* **Moderator:** **@{ctx.author.display_name}**\n* **Reason:** `Hit Max Points`\n* **Occured:** {moderatedform}\n* **User Points:** {points_value}",color=discord.Color.dark_embed())
                embed.set_author(name=user.display_name, icon_url=user.display_avatar)
                embed.set_footer(text=f"Moderation ID | {random_string}")
                embed.set_thumbnail(url=user.display_avatar)
                await channel.send(embed=embed)
             else:   
                pass            
            
         else: 
            pass
        else: 
            try:
             await user.send(f"<:Infraction:1162134605885870180> You've been muted **@{ctx.guild.name}** for **{reason}**\n <:ArrowDropDown:1163171628050563153> you now have `{points_value}/{max_points}` **points**")
            except discord.Forbidden:
                pass                  
            await ctx.send(f"{tick} **@{user.display_name}**, has been muted.\n<:ArrowDropDown:1163171628050563153> they now have `{points_value}/{max_points}` **points**")
        duration_value = int(duration[:-1])
        duration_unit = duration[-1]
        duration_seconds = duration_value

        if duration_unit == 'm':
            duration_seconds *= 60
        elif duration_unit == 'h':
            duration_seconds *= 3600
        elif duration_unit == 'd':
            duration_seconds *= 86400


        mute_duration = datetime.timedelta(seconds=duration_seconds)
        try:
            await user.timeout(mute_duration, reason=reason)
        except discord.Forbidden:
            await ctx.send(f"{no} I don't have the necessary permissions to timeout users.")
        moderation_data = {
            'guild_id': ctx.guild.id,
            'user': user.id,
            'reason': reason,
            'type': 'mute',             
            'id': random_string,
            'moderator': ctx.author.id,
            'timestamp': moderatedform
        }
        moderations.insert_one(moderation_data)
        data = ModerationChannel.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)            
        if channel:
            embed = discord.Embed(title=f"Mute", description=f"* **User:** {user.mention}(`{user.id}`)\n* **Moderator:** **@{ctx.author.display_name}**\n* **Reason:** {reason}\n* **Occured:** {moderatedform}\n* **Duration:** {duration}\n* **User Points:** {points_value}", color=discord.Color.dark_embed())
            embed.set_author(name=user.display_name, icon_url=user.display_avatar)
            embed.set_footer(text=f"Moderation ID | {random_string}")
            embed.set_thumbnail(url=user.display_avatar)
            await channel.send(embed=embed)

    @commands.hybrid_command(description="Unmutes a user")
    async def unmute(self, ctx, user: discord.Member, reason: str):
        if not await self.has_mute_role(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
            return
        if user.top_role >= ctx.author.top_role:
         await ctx.send(f"{no} You can't unmute someone with a higher or equal role.")
         return
        timezone = pytz.timezone('Europe/Paris')
        moderated = datetime.now(timezone)
        moderatedform = f"<t:{int(moderated.timestamp())}:t>"         
        random_string = ''.join(random.choices(string.digits, k=8))
        filter = {
            'guild_id': ctx.guild.id,
            'user_id': user.id,
        }

        try:
            await user.timeout(datetime.timedelta(seconds=0), reason=reason)
        except discord.Forbidden:
            await ctx.send(f"{no} I don't have the necessary permissions to timeout users.")

        await ctx.send(f"{tick} **@{user.display_name}**, has been unmuted.")
        try:
         await user.send(f"<:Infraction:1162134605885870180> You've been unmuted **@{ctx.guild.name}** for **{reason}**")
        except discord.Forbidden:
                pass              

        moderation_data = {
            'guild_id': ctx.guild.id,
            'user': user.id,
            'reason': reason,
            'type': 'unmute',             
            'id': random_string,
            'moderator': ctx.author.id,
            'timestamp': moderatedform
        }
        moderations.insert_one(moderation_data)

        data = ModerationChannel.find_one({'guild_id': ctx.guild.id})
        if data:
            channel_id = data['channel_id']
            channel = self.client.get_channel(channel_id)
            
            if channel:
                embed = discord.Embed(title=f"Unmute", description=f"* **User:** {user.mention}(`{user.id}`)\n* **Moderator:** **@{ctx.author.display_name}**\n* **Occured:** {moderatedform}\n* **Reason:** {reason}", color=discord.Color.dark_embed())
                embed.set_author(name=user.display_name, icon_url=user.display_avatar)
                embed.set_footer(text=f"Moderation ID | {random_string}")
                embed.set_thumbnail(url=user.display_avatar)
                await channel.send(embed=embed)
            else:
                pass

    @commands.hybrid_command(description="Kicks a user from the guild")
    async def kick(self, ctx, user: discord.Member, *, reason):
        if not await self.has_kick_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return           
        if not ctx.guild.me.guild_permissions.kick_members:
         await ctx.send(f"{no} I don't have permission to kick users.")
         return           
        if user.top_role >= ctx.author.top_role:
         await ctx.send(f"{no} You can't kick someone with a higher or equal role.")
         return         
        random_string = ''.join(random.choices(string.digits, k=8))
        filter = {
        'guild_id': ctx.guild.id,
        'user_id': user.id,
    }
        points = ModerationPoints.find(filter)

        pointvalue = KickPointValue.find_one({'guild_id': ctx.guild.id})
        timezone = pytz.timezone('Europe/Paris')
        moderated = datetime.now(timezone)
        moderatedform = f"<t:{int(moderated.timestamp())}:t>"
        if pointvalue:
         pointsv = pointvalue['pointvalue']
        else:
         pointsv = 4 
        pointsv = int(pointsv)
        ModerationPoints.update_one({'guild_id': ctx.guild.id, 'user_id': user.id}, {'$inc': {'points': pointsv}}, upsert=True)        
        points_value = 0        
        for document in points: 
            points_value = document['points']
        max_point_value_data = MaxPointValue.find_one({'guild_id': ctx.guild.id})
        if max_point_value_data:
         max_points = max_point_value_data['pointvalue']
        else:
         max_points = 10            
        if points_value >= max_points:         
         msg = await ctx.send(f"{tick} **@{user.display_name}**, has been banned.\n<:ArrowDropDown:1163171628050563153> they have reached the max points `{points_value}/{max_points}` **points**")
         msg2 = await user.send(f"<:Infraction:1162134605885870180> You've been banned **@{ctx.guild.name}** for **{reason}**\n <:ArrowDropDown:1163171628050563153> you have reach the max points `{points_value}/{max_points}` **points**")
         autoban = AutoBanValue.find_one({'guild_id': ctx.guild.id})

         if autoban:
            appeal_enabled = autoban.get('toggle', False)
         else:
            appeal_enabled = False

         if appeal_enabled:
            await msg.reply(f"{tick} **Autobanned**, reached max points.")
            await msg2.reply(f"<:Infraction:1162134605885870180> **Autobanned**, you've reached the max points.")
            await user.ban(reason="Hit maxed amount of points")
            random_string = ''.join(random.choices(string.digits, k=8))
            moderation_data = {
            'guild_id': ctx.guild.id,
            'user': user.id,
            'reason': 'User hit max points',
            'type': 'Autoban',            
            'id': random_string,
            'moderator': '@Astro Birb',            
            'timestamp': moderatedform
        }
            moderations.insert_one(moderation_data)
            data = ModerationChannel.find_one({'guild_id': ctx.guild.id})
            if data:
             channel_id = data['channel_id']
             channel = self.client.get_channel(channel_id)             
             if channel:
                
                embed = discord.Embed(title=f"Auto Banned", description=f"* **User:** {user.mention}(`{user.id}`)\n* **Moderator:** **@{ctx.author.display_name}**\n* **Reason:** `Hit Max Points`\n* **Occured:** {moderatedform}\n* **User Points:** {points_value}",color=discord.Color.dark_embed())
                embed.set_author(name=user.display_name, icon_url=user.display_avatar)
                embed.set_footer(text=f"Moderation ID | {random_string}")
                embed.set_thumbnail(url=user.display_avatar)
                await channel.send(embed=embed)
             else:   
                pass
         else: 
            pass
        else: 
            try:
             await user.send(f"<:Infraction:1162134605885870180> You've been kicked **@{ctx.guild.name}** for **{reason}**\n <:ArrowDropDown:1163171628050563153> you now have `{points_value}/{max_points}` **points**")
            except discord.Forbidden:
                pass             
            await user.kick(reason=f"{ctx.author}: {reason}")
            await ctx.send(f"{tick} **@{user.display_name}**, has been kicked.\n<:ArrowDropDown:1163171628050563153> they now have `{points_value}/{max_points}` **points**")
        moderation_data = {
            'guild_id': ctx.guild.id,
            'user': user.id,
            'reason': reason,
            'type': 'kick',            
            'id': random_string,
            'moderator': ctx.author.id,            
            'timestamp': moderatedform
        }
        moderations.insert_one(moderation_data)
        data = ModerationChannel.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)            
        if channel:
            embed = discord.Embed(title=f"Kicked", description=f"* **User:** {user.mention}(`{user.id}`)\n* **Moderator:** **@{ctx.author.display_name}**\n* **Reason:** {reason}\n* **Occured:** {moderatedform}\n* **User Points:** {points_value}",color=discord.Color.dark_embed())
            embed.set_author(name=user.display_name, icon_url=user.display_avatar)
            embed.set_footer(text=f"Moderation ID | {random_string}")
            embed.set_thumbnail(url=user.display_avatar)
            await channel.send(embed=embed)

    @commands.hybrid_command(description="Bans a user from the guild")
    async def ban(self, ctx, user: discord.Member, *,reason):
        if not await self.has_ban_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return             
        if not ctx.guild.me.guild_permissions.ban_members:
         await ctx.send(f"{no} I don't have permission to ban users.")
         return             
        if user.top_role >= ctx.author.top_role:
         await ctx.send(f"{no} You can't ban someone with a higher or equal role.")
         return          
        filter = {
        'guild_id': ctx.guild.id,
        'user_id': user.id,
    }
        random_string = ''.join(random.choices(string.digits, k=8))
        points = ModerationPoints.find(filter)
        pointvalue = SoftBanPointValue.find_one({'guild_id': ctx.guild.id})
        timezone = pytz.timezone('Europe/Paris')
        moderated = datetime.now(timezone)
        moderatedform = f"<t:{int(moderated.timestamp())}:t>"

        if pointvalue:
         pointsv = pointvalue['pointvalue']
        else:
         pointsv = 8 
        pointsv = int(pointsv)
        ModerationPoints.update_one({'guild_id': ctx.guild.id, 'user_id': user.id}, {'$inc': {'points': pointsv}}, upsert=True)
        points_value = 0        
        for document in points: 
            points_value = document['points']
        max_point_value_data = MaxPointValue.find_one({'guild_id': ctx.guild.id})
        if max_point_value_data:
         max_points = max_point_value_data['pointvalue']
        else:
         max_points = 10            
        if points_value >= max_points:         
         msg = await ctx.send(f"{tick} **@{user.display_name}**, has been banned.\n<:ArrowDropDown:1163171628050563153> they have reached the max points `{points_value}/{max_points}` **points**")
         try:
          msg2 = await user.send(f"<:Infraction:1162134605885870180> You've been banned **@{ctx.guild.name}** for **{reason}**\n <:ArrowDropDown:1163171628050563153> you have reach the max points `{points_value}/{max_points}` **points**")
         except discord.Forbidden:
                pass            
         autoban = AutoBanValue.find_one({'guild_id': ctx.guild.id})

         if autoban:
            appeal_enabled = autoban.get('toggle', False)
         else:
            appeal_enabled = False

         if appeal_enabled:
            await msg.reply(f"{tick} **Autobanned**, reached max points.")
            await msg2.reply(f"<:Infraction:1162134605885870180> **Autobanned**, you've reached the max points.")
            await user.ban(reason="Hit maxed amount of points")
            random_string = ''.join(random.choices(string.digits, k=8))
            moderation_data = {
            'guild_id': ctx.guild.id,
            'user': user.id,
            'reason': 'User hit max points',
            'type': 'Autoban',            
            'id': random_string,
            'moderator': '@Astro Birb',            
            'timestamp': moderatedform
        }
            moderations.insert_one(moderation_data)
            data = ModerationChannel.find_one({'guild_id': ctx.guild.id})
            if data:
             channel_id = data['channel_id']
             channel = self.client.get_channel(channel_id)             
             if channel:
                
                embed = discord.Embed(title=f"Auto Banned", description=f"* **User:** {user.mention}(`{user.id}`)\n* **Moderator:** **@{ctx.author.display_name}**\n* **Reason:** `Hit Max Points`\n* **Occured:** {moderatedform}\n* **User Points:** {points_value}",color=discord.Color.dark_embed())
                embed.set_author(name=user.display_name, icon_url=user.display_avatar)
                embed.set_footer(text=f"Moderation ID | {random_string}")
                embed.set_thumbnail(url=user.display_avatar)
                await channel.send(embed=embed)
             else:   
                pass            
         else: 
            pass
        else: 
            await user.send(f"<:Infraction:1162134605885870180> You've been banned **@{ctx.guild.name}** for **{reason}**\n <:ArrowDropDown:1163171628050563153> you now have `{points_value}/{max_points}` **points**")
            await ctx.send(f"{tick} **@{user.display_name}**, has been banned.\n<:ArrowDropDown:1163171628050563153> they now have `{points_value}/{max_points}` **points**")

            await user.ban(reason=f"Banned by: {ctx.author.display_name}. Reason: {reason}")    
        moderation_data = {
            'guild_id': ctx.guild.id,
            'user': user.id,
            'reason': reason,
            'type': 'ban',
            'id': random_string,
            'moderator': ctx.author.id,            
            'timestamp': moderatedform
        }
        moderations.insert_one(moderation_data)
        data = ModerationChannel.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)            
        if channel:
            embed = discord.Embed(title=f"Banned", description=f"* **User:** {user.mention}(`{user.id}`)\n* **Moderator:** **@{ctx.author.display_name}**\n* **Reason:** {reason}\n* **Occured:** {moderatedform}\n* **User Points:** {points_value}", color=discord.Color.dark_embed())
            embed.set_author(name=user.display_name, icon_url=user.display_avatar)
            embed.set_footer(text=f"Moderation ID | {random_string}")
            embed.set_thumbnail(url=user.display_avatar)            
            await channel.send(embed=embed)

    @commands.hybrid_command(description="Unbans a user from the guild")
    async def unban(self, ctx, id: int, *,reason):
        user = await self.client.fetch_user(id)
        if not await self.has_ban_role(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
         return             
        if not ctx.guild.me.guild_permissions.ban_members:
         await ctx.send(f"{no} I don't have permission to unban users.")
         return                     
        filter = {
        'guild_id': ctx.guild.id,
        'user_id': user.id,
    }

        timezone = pytz.timezone('Europe/Paris')
        moderated = datetime.now(timezone)
        moderatedform = f"<t:{int(moderated.timestamp())}:t>"

        random_string = ''.join(random.choices(string.digits, k=8))
        try:
         await user.send(f"<:Infraction:1162134605885870180> You've been unbanned **@{ctx.guild.name}** for **{reason}**")
        except discord.Forbidden:
                pass         
        await ctx.send(f"{tick} **@{user.display_name}**, has been unbanned.")
        await ctx.guild.unban(user)
 

        moderation_data = {
            'guild_id': ctx.guild.id,
            'user': user.id,
            'reason': reason,
            'type': 'unban',
            'id': random_string,
            'moderator': ctx.author.id,            
            'timestamp': moderatedform
        }
        moderations.insert_one(moderation_data)
        data = ModerationChannel.find_one({'guild_id': ctx.guild.id})
        if data:
         channel_id = data['channel_id']
         channel = self.client.get_channel(channel_id)            
        if channel:
            embed = discord.Embed(title=f"Unbanned", description=f"* **User:** {user.mention}(`{user.id}`)\n* **Moderator:** **@{ctx.author.display_name}**\n* **Reason:** {reason}\n* **Occured:** {moderatedform}", color=discord.Color.dark_embed())
            embed.set_author(name=user.display_name, icon_url=user.display_avatar)
            embed.set_footer(text=f"Moderation ID | {random_string}")
            embed.set_thumbnail(url=user.display_avatar)            
            await channel.send(embed=embed)

    @commands.hybrid_command(description="View a user's moderations")
    async def moderations(self, ctx, user: discord.Member):
     if not (await self.has_warning_role(ctx) or await self.has_kick_role(ctx) or await self.has_ban_role(ctx) or await self.has_mute_role(ctx)):
        await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
        return

     filter = {
        'guild_id': ctx.guild.id,
        'user': user.id,
    }
     moderation_records = moderations.find(filter)

     if moderation_records:
        embed = discord.Embed(title=f"{user.display_name}", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=user.display_avatar)
        embed.set_author(name=user, icon_url=user.display_avatar)
        for record in moderation_records:
            mod_type = record['type']
            mod_id = record['id']
            mod_reason = record['reason']
            mod_moderator_id = record['moderator']
            occured = record['timestamp']
            mod_moderator = ctx.guild.get_member(mod_moderator_id)

            if mod_moderator:
                mod_moderator_mention = mod_moderator.mention
            else:
                mod_moderator_mention = f"N/A"

            embed.add_field(
                name=f"{mod_id}",
                value=f"* **Punishment:** {mod_type}\n* **Moderator:** {mod_moderator_mention}\n* **Reason:** {mod_reason}\n* **Occured:** {occured}",
                inline=False
            )

        await ctx.send(embed=embed)
     else:
        await ctx.send(f"{no} No moderation records found for {user.display_name}.")

    @commands.hybrid_group()    
    async def moderation(self, ctx):
        pass

    @moderation.command(description="View a moderation case")
    async def case(self, ctx, id: str):
     if not (await self.has_warning_role(ctx) or await self.has_kick_role(ctx) or await self.has_ban_role(ctx) or await self.has_mute_role(ctx)):
      await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
      return      
     filter = {
        'guild_id': ctx.guild.id,
        'id': id,
    }
     moderation_record = moderations.find_one(filter)

     if moderation_record:
        mod_type = moderation_record['type']
        mod_id = moderation_record['id']
        mod_reason = moderation_record['reason']
        mod_moderator_id = moderation_record['moderator']
        occured = moderation_record['timestamp']
        mod_moderator = ctx.guild.get_member(mod_moderator_id)
        user_id = moderation_record['user']
        user = ctx.guild.get_member(user_id)

        if mod_moderator:
            mod_moderator_mention = mod_moderator.mention
        else:
            mod_moderator_mention = f"N/A"

        description = (
            f"* **Punishment:** {mod_type}\n"
            f"* **User:** {user.mention} (`{user.id}`)\n"
            f"* **Moderator:** {mod_moderator_mention}\n"
            f"* **Reason:** {mod_reason}\n"
            f"* **Occured:** {occured}\n"
        )

        embed = discord.Embed(
            title=f"Moderation Case `#{id}`",
            description=description,
            color=discord.Color.dark_embed()
        )
        embed.set_author(name=user.display_name, icon_url=user.display_avatar)

        await ctx.send(embed=embed)
     else:
        await ctx.send(f"{no} Moderation case with ID `{id}` not found.")
 
    @moderation.command(description="Removes a moderation from the database.")    
    async def void(self, ctx, id: str):
     if not (await self.has_warning_role(ctx) or await self.has_kick_role(ctx) or await self.has_ban_role(ctx) or await self.has_mute_role(ctx)):
      await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.")
      return        
     filter = {
        'guild_id': ctx.guild.id,
        'id': id,
    }
     moderation_record = moderations.find_one(filter)

     if moderation_record:
        mod_type = moderation_record['type']
        mod_reason = moderation_record['reason']
        user_id = moderation_record['user']
        user = ctx.guild.get_member(user_id)
        mod_moderator_id = moderation_record['moderator']
        occured = moderation_record['timestamp']
        mod_moderator = ctx.guild.get_member(mod_moderator_id)



        description = (
            f"**Punishment Type:** {mod_type}\n"
            f"**User:** {user.mention} (`{user.id}`)\n"
            f"**Moderator:** {mod_moderator.mention}\n"
            f"**Reason:** {mod_reason}\n"
            f"**Occured:** {occured}\n"            
        )

        embed = discord.Embed(
            title=f"Moderation Case `#{id}` (Revoked)",
            description=description,
            color=discord.Color.dark_embed()
        )
        embed.set_author(name=mod_moderator.display_name, icon_url=mod_moderator.display_avatar)
        moderations.delete_one(filter)

        await ctx.send(f"{tick} Moderation **Revoked**", embed=embed)
     else:
        await ctx.send(f"{no} Moderation case with ID `{id}` not found.")   

async def setup(client: commands.Bot) -> None:
    await client.add_cog(ModerationModule(client))        
