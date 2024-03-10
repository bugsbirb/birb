import discord
import discord
from discord.ext import commands
import datetime
from datetime import timedelta
from discord import app_commands
from discord.ext import commands, tasks
from emojis import * 
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import re
load_dotenv()
from permissions import has_admin_role, has_staff_role
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
loa_collection = db['loa']
loachannel = db['LOA Channel']

arole = db['adminrole']
LOARole = db['LOA Role']
modules = db['Modules']
scollection = db['staffrole']
consent = db['consent']

class LOA(discord.ui.Modal, title='Create Leave Of Absence'):
    def __init__(self, user, guild, author):
        super().__init__()
        self.user = user
        self.guild = guild
        self.author = author

    Duration = discord.ui.TextInput(
        label='Duration',
        placeholder='e.g 1w (m/h/d/w)',
    )

    reason = discord.ui.TextInput(
        label='Reason',
        placeholder='Reason for their loa'
    )

    async def on_submit(self, interaction: discord.Interaction):
        duration = self.Duration.value
        reason = self.reason.value
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        duration_value = int(duration[:-1])
        duration_unit = duration[-1]
        duration_seconds = duration_value
        if duration_unit == 's':
            duration_seconds *= 1
        elif duration_unit == 'm':
            duration_seconds *= 60
        elif duration_unit == 'h':
            duration_seconds *= 3600
        elif duration_unit == 'd':
            duration_seconds *= 86400
        elif duration_unit == 'w':
            duration_seconds *= 604800

        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)

        data = await loachannel.find_one({'guild_id': interaction.guild.id})
        if data:
            channel_id = data['channel_id']
            channel = interaction.guild.get_channel(channel_id)

            if channel:
                embed = discord.Embed(title=f"LOA Created",
                                      description=f"* **User:** {self.user.mention}\n* **Start Date**: <t:{int(start_time.timestamp())}:f>\n* **End Date:** <t:{int(end_time.timestamp())}:f>\n* **Reason:** {self.reason}", color=discord.Color.dark_embed())
                embed.set_author(icon_url=self.user.display_avatar, name=self.user.display_name)
                embed.set_thumbnail(url=self.user.display_avatar)
                loadata = {'guild_id': interaction.guild.id,
                           'user': self.user.id,
                           'start_time': start_time,
                           'end_time': end_time,
                           'reason': reason,
                           'active': True}
                loarole_data = await LOARole.find_one({'guild_id': interaction.guild.id})
                if loarole_data:
                    loarole = loarole_data['staffrole']
                    if loarole:
                        role = discord.utils.get(interaction.guild.roles, id=loarole)
                        if role:
                            try:
                                await self.user.add_roles(role)
                            except discord.Forbidden:
                                await interaction.response.edit_message(content=f"{no} I don't have permission to add roles.")
                                return

                await interaction.response.edit_message(content=f"{tick} Created LOA for **@{self.user.display_name}**", embed=embed, view=None, allowed_mentions=discord.AllowedMentions.none())
                await loa_collection.insert_one(loadata)
                try:
                    await channel.send(f"<:Add:1163095623600447558> LOA was created by **@{interaction.user.display_name}**", embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False))
                except discord.Forbidden:
                    await interaction.response.edit_message(content=f"{no} I don't have permission to view that channel.")
                    return
                try:
                    await self.user.send(f"<:Add:1163095623600447558> A LOA was created for you **@{interaction.guild.name}**", embed=embed)
                except discord.Forbidden:
                    pass


class loamodule(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.check_loa_status.start()

    async def modulecheck(self, ctx):
        modulesdata = await modules.find_one({"guild_id": ctx.guild.id})
        if modulesdata is None:
            return False
        elif modulesdata['LOA'] == True:
            return True

    @commands.hybrid_group()
    async def loa(self, ctx):
        pass

    @tasks.loop(minutes=10)
    async def check_loa_status(self):
        print("Checking LOA Status")
        try:
            current_time = datetime.now()

            filter = {'end_time': {'$lte': current_time}, 'active': True}

            loa_requests = await loa_collection.find(filter).to_list(length=None)

            for request in loa_requests:
                end_time = request['end_time']
                user_id = request['user']
                guild_id = request['guild_id']
                guild = self.client.get_guild(guild_id)
                user = await self.client.fetch_user(user_id)
                active = request['active']

                if guild is None or user is None:
                    await loa_collection.delete_one({'guild_id': guild_id, 'user': user_id, 'end_time': end_time})
                    continue

                if active and current_time >= end_time:
                    try:
                        loanotification = await consent.find_one({'user_id': user.id})
                        if loanotification:
                            if loanotification.get('LOAAlerts', "Enabled") == "Enabled":                        
                             await user.send(f"{tick} Your LOA **@{guild.name}** has ended.")
                    except discord.Forbidden:
                        print(f"Failed to send a DM to user {user_id}. Continuing...")
                    
                    print(f"End Time: {end_time}")
                    print(f"Current Time: {current_time}")
                    await loa_collection.update_many({'guild_id': guild_id, 'user': user_id}, {'$set': {'active': False}})
                    
                    loarole_data = await LOARole.find_one({'guild_id': guild.id})
                    loachannelresult = await loachannel.find_one({'guild_id': guild.id})
                    if loachannelresult:
                        channel_id = loachannelresult['channel_id']
                        try:
                         channel = guild.get_channel(channel_id)
                        except discord.Forbidden:
                            print(f"Failed to get channel {channel_id}. Continuing...")
                            continue 
                        if channel:
                            embed = discord.Embed(title=f"LOA Ended",
                                                  description=f"* **User:** {user.mention}\n* **Start Date**: <t:{int(request['start_time'].timestamp())}:f>\n* **End Date:** <t:{int(request['end_time'].timestamp())}:f>\n* **Reason:** {request['reason']}",
                                                  color=discord.Color.dark_embed())
                            embed.set_author(icon_url=user.display_avatar, name=user.display_name)
                            embed.set_thumbnail(url=user.display_avatar)
                            try:
                             await channel.send(embed=embed)
                            except discord.Forbidden:
                                print(f"Failed to send message to channel {channel_id}. Continuing...")
                                continue 
                        else:
                            print(f"Failed to get channel {channel_id}. Continuing...")
                            continue    
                    if loarole_data:
                            loarole = loarole_data['staffrole']
                            if loarole:
                                try:
                                 role = discord.utils.get(guild.roles, id=loarole)
                                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                                    print(f"Failed to get role {loarole}. Continuing..."
                                          )
                                    continue 
                                 
                                if role:
                                    try:
                                     member = await guild.fetch_member(user.id)
                                    except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                                        print(f"Failed to get member {user_id}. Continuing...")
                                        continue 
                                    try:
                                     await member.remove_roles(role)
                                    except discord.Forbidden:
                                        print(f"Failed to remove role from {user_id}. Continuing...")
                                        continue 
                                else:
                                    print(f"Failed to get role {loarole}. Continuing...")
                                    continue    
            else:
                pass
        except Exception as e:
            print(e)


    @loa.command(description="Manage someone leave of Absence")
    async def manage(self, ctx, user: discord.Member):
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.", allowed_mentions=discord.AllowedMentions.none())
            return
        if not await has_admin_role(ctx):
            return

        loas = await loa_collection.find_one({"user": user.id, "guild_id": ctx.guild.id, 'active': True, 'request': {'$ne': True}})
        loainactive = await loa_collection.find({"user": user.id, "guild_id": ctx.guild.id, 'active': False,  'request': {'$ne': True}}).to_list(length=None)
        view = None

        if loas is None:
            description = []
            for request in loainactive:
                start_time = request['start_time']
                end_time = request['end_time']
                reason = request['reason']
                description.append(
                    f"{loa} **Previous LOA**\n{arrow}<t:{int(start_time.timestamp())}:f> - <t:{int(end_time.timestamp())}:f> • {reason}")

            embed = discord.Embed(title="Leave Of Absense",
                                  description=f"\n".join(description), color=discord.Color.dark_embed())
            embed.set_thumbnail(url=user.display_avatar)
            embed.set_author(icon_url=user.display_avatar, name=user.display_name)
            view = LOACreate(user, ctx.guild, ctx.author)

        else:
            start_time = loas['start_time']
            end_time = loas['end_time']
            reason = loas['reason']

            embed = discord.Embed(
                title=f"Leave Of Absence",
                color=discord.Color.dark_embed(),
                description=f"{loa} **Active LOA**\n{arrow}**Start Date:** <t:{int(start_time.timestamp())}:f>\n{arrow}**End Date:** <t:{int(end_time.timestamp())}:f>\n{arrow}**Reason:** {reason}"
            )
            embed.set_thumbnail(url=user.display_avatar)
            embed.set_author(icon_url=user.display_avatar, name=user.display_name)

            view = LOAPanel(user, ctx.guild, ctx.author)

        await ctx.send(embed=embed, view=view)

    @loa.command(description="View all Leave Of Absence")
    async def active(self, ctx):
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.", allowed_mentions=discord.AllowedMentions.none())
            return

        if not await has_admin_role(ctx):
            return

        current_time = datetime.now()
        filter = {'guild_id': ctx.guild.id, 'end_time': {'$gte': current_time}, 'active': True, 'request': {'$ne': True}}

        loa_requests = await loa_collection.find(filter).to_list(length=None)

        if len(loa_requests) == 0:
            await ctx.send(f"{no} **{ctx.author.display_name}**, there aren't any active LOAs in this server.", allowed_mentions=discord.AllowedMentions.none())
        else:
            embed = discord.Embed(
                title="Active LOAs",
                color=discord.Color.dark_embed()
            )
            embed.set_thumbnail(url=ctx.guild.icon)
            embed.set_author(icon_url=ctx.guild.icon, name=ctx.guild.name)
            for request in loa_requests:
                user = await self.client.fetch_user(request['user'])
                start_time = request['start_time']
                end_time = request['end_time']
                reason = request['reason']

                embed.add_field(
                    name=f"{loa}{user.name.capitalize()}",
                    value=f"{arrow}**Start Date:** <t:{int(start_time.timestamp())}:f>\n{arrow}**End Date:** <t:{int(end_time.timestamp())}:f>\n{arrow}**Reason:** {reason}",
                    inline=False
                )

            await ctx.send(embed=embed)

    @loa.command(description="Request a Leave Of Absence")
    @app_commands.describe(duration="How long do you want the LOA for? (m/h/d/w)", reason="What is the reason for this LOA?")
    async def request(self, ctx, duration: str, reason: str):
        await ctx.defer(ephemeral=True)
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
            return
        if not await has_staff_role(ctx):
            return
        if not re.match(r'^\d+[smhdw]$', duration):
            await ctx.send(
                f"{no} **{ctx.author.display_name}**, invalid duration format. Please use a valid format like '1d' (1 day), '2h' (2 hours), etc.", allowed_mentions=discord.AllowedMentions.none())
            return
        loa_data = await loa_collection.find_one(
            {'guild_id': ctx.guild.id, 'user': ctx.author.id, 'active': True})
        if loa_data:
            await ctx.send(f"{no} **{ctx.author.display_name}**, you already have an active LOA.", allowed_mentions=discord.AllowedMentions.none())
            return

        duration_value = int(duration[:-1])
        duration_unit = duration[-1]
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
        embed = discord.Embed(title=f"LOA Request - Pending",
                              description=f"* **User:** {ctx.author.mention}\n* **Start Date**: <t:{int(start_time.timestamp())}:f>\n* **End Date:** <t:{int(end_time.timestamp())}:f>\n* **Reason:** {reason}",
                              color=discord.Color.dark_embed())
        embed.set_author(icon_url=ctx.author.display_avatar, name=ctx.author.display_name)
        embed.set_thumbnail(url=ctx.author.display_avatar)
        data = await loachannel.find_one({'guild_id': ctx.guild.id})
        if data:
            channel_id = data['channel_id']
            channel = self.client.get_channel(channel_id)

            if channel:
                past_loas = await loa_collection.count_documents({'guild_id': ctx.guild.id, 'user': ctx.author.id, 'request': {'$ne': True}, 'active': False, })
                view = Confirm()
                if past_loas == 0:
                    view.loacount.disabled = True

                
                view.loacount.label = f"Past LOAs  |  {past_loas}"
                try:
                    msg = await channel.send(embed=embed, view=view)
                    loadata = {'guild_id': ctx.guild.id,
                               'user': ctx.author.id,
                               'start_time': start_time,
                               'end_time': end_time,
                               'reason': reason,
                               'messageid': msg.id,
                               'request': True,
                               'active': False}
                    await loa_collection.insert_one(loadata)
                    await ctx.send(f"{tick} LOA Request sent", ephemeral=True)
                    print(f"LOA Request @{ctx.guild.name} pending")
                except discord.Forbidden:
                    await ctx.send(f"{no} Please contact server admins I can't see the LOA Channel.")

            else:
                await ctx.send(f"{no} {ctx.author.display_name}, I don't have permission to view this channel.", allowed_mentions=discord.AllowedMentions.none())
        else:
            await ctx.send(f"{no} **{ctx.author.display_name}**, the channel is not set up. Please run `/config`", allowed_mentions=discord.AllowedMentions.none())


class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def has_admin_role(self, interaction):
        filter = {
            'guild_id': interaction.guild.id
        }
        staff_data = await arole.find_one(filter)

        if staff_data and 'staffrole' in staff_data:
            staff_role_ids = staff_data['staffrole']
            staff_role = discord.utils.get(interaction.guild.roles, id=staff_role_ids)
            if not isinstance(staff_role_ids, list):
                staff_role_ids = [staff_role_ids]
            if any(role.id in staff_role_ids for role in interaction.user.roles):
                return True

        return False

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green, custom_id='persistent_view:confirm', row=0,
                       emoji=f"{tick}")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not await self.has_admin_role(interaction):
            await interaction.followup.send(
                content=f"{no} **{interaction.user.display_name}**, you don't have permission to accept this LOA.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`", allowed_mentions=discord.AllowedMentions.none(),
                ephemeral=True)
            return
        loa_data = await loa_collection.find_one({'messageid': interaction.message.id})
        if loa_data:
            try:
             self.user = await interaction.guild.fetch_member(loa_data['user'])
            except discord.HTTPException or discord.NotFound:
                    await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, I can't find this user.", ephemeral=True)
             
                    return          

        else:
                await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, I can't find this LOA.", ephemeral=True)
                return           
        user = self.user

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_green()
        embed.title = f"{greencheck} LOA Request - Accepted"
        embed.set_footer(text=f"Accepted by {interaction.user.display_name}", icon_url=interaction.user.display_avatar)
        await interaction.message.edit(embed=embed, view=None)
        print(f"LOA Request @{interaction.guild.name} accepted")
        loarole_data = await LOARole.find_one({'guild_id': interaction.guild.id})
        await loa_collection.update_one({'guild_id': interaction.guild.id, 'messageid': interaction.message.id ,'user': user.id}, {'$set': {'active': True, 'request': False} })
        if loarole_data:
            loarole = loarole_data['staffrole']
            if loarole:
                role = discord.utils.get(interaction.guild.roles, id=loarole)
                if role:
                    await user.add_roles(role)
        loanotification = await consent.find_one({'user_id': self.user.id})
        if loanotification:
            if loanotification.get('LOAAlerts', "Enabled") == "Enabled":
                
  
             try:
              embed.remove_footer()
              embed.remove_author()
              await self.user.send(embed=embed)
             except discord.Forbidden:
              print(f"Failed to send a DM to user {self.user.id}. Continuing...")
              pass



    @discord.ui.button(label='Deny', style=discord.ButtonStyle.red, custom_id='persistent_view:cancel',row=0,
                       emoji=f"{no}")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not await self.has_admin_role(interaction):
            await interaction.followup.send(
                content=f"{no} **{interaction.user.display_name}**, you don't have permission to accept this LOA.\n<:Arrow:1115743130461933599>**Required:** `Admin Role`", allowed_mentions=discord.AllowedMentions.none()
                ,ephemeral=True)
            return
        loa_data = await loa_collection.find_one({'messageid': interaction.message.id})
        if loa_data:
            try:
             self.user = await interaction.guild.fetch_member(loa_data['user'])
            except discord.HTTPException or discord.NotFound:
                    await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, I can't find this user.", ephemeral=True)
                    return   
        else:

                await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, I can't find this LOA.", ephemeral=True)
                return    

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.brand_red()
        embed.title = f"{redx} LOA Request - Denied"
        embed.set_footer(text=f"Denied by {interaction.user.display_name}", icon_url=interaction.user.display_avatar)
        await interaction.message.edit(embed=embed, view=None)
        await loa_collection.delete_one({'guild_id': interaction.guild.id, 'user': self.user.id, 'messageid': interaction.message.id})
        print(f"LOA Request @{interaction.guild.name} denied")
        loanotification = await consent.find_one({'user_id': self.user.id})
        if loanotification:
            if loanotification.get('LOAAlerts', "Enabled") == "Enabled":        
             try:

              await self.user.send(
                f"{no} **{self.user.display_name}**, your LOA **@{interaction.guild.name}** has been denied.")
             except discord.Forbidden:
              print(f"Failed to send a DM to user {self.user.id}. Continuing...")
              pass

    @discord.ui.button(label="Past LOAs | 0", style=discord.ButtonStyle.grey, custom_id='persistent_view:loacount',row=0,
                       emoji=f"<:case:1214629776606887946>")
    async def loacount(self, interaction: discord.Interaction, button: discord.ui.Button):
            loa_data = await loa_collection.find_one({'messageid': interaction.message.id})
            if loa_data:

                try:
                 self.user = await interaction.guild.fetch_member(loa_data['user'])
                except discord.HTTPException or discord.NotFound:
                    await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, I can't find this user.", ephemeral=True)
                    return
            else:
                await interaction.response.send_message(content=f"{no} **{interaction.user.display_name}**, I can't find this LOA.", ephemeral=True)
                return    
            user = self.user            
            loainactive = await loa_collection.find({'guild_id': interaction.guild.id, 'request': {'$ne': True}, 'user': user.id, 'active': False}).sort('start_time', -1).to_list(length=None)
            description = []
            for request in loainactive:
                start_time = request['start_time']
                end_time = request['end_time']
                reason = request['reason']
                description.append(
                    f"<t:{int(start_time.timestamp())}:f> - <t:{int(end_time.timestamp())}:f> • {reason}")
            embed = discord.Embed(title="Past LOAs", description="\n".join(description), color=discord.Color.dark_embed())
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            
class LOAPanel(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(label='Void LOA', style=discord.ButtonStyle.grey, custom_id='persistent_view:cancel',
                       emoji="<:Exterminate:1164970632262451231>")
    async def End(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.user
        author = self.author.id
        if interaction.user.id != author:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        loa = await loa_collection.find_one({"user": self.user.id, "guild_id": interaction.guild.id, 'active': True})
        loarole_data = await LOARole.find_one({'guild_id': interaction.guild.id})
        if loarole_data:
            loarole = loarole_data['staffrole']
            if loarole:
                role = discord.utils.get(interaction.guild.roles, id=loarole)
                if role:
                    try:
                        await user.remove_roles(role)
                    except discord.Forbidden:
                        await interaction.response.edit_message(
                            content=f"{no} I don't have permission to remove roles.")
                        return

        await loa_collection.update_many({'guild_id': interaction.guild.id, 'user': user.id}, {'$set': {'active': False}})
        await interaction.response.edit_message(embed=None,
                                               content=f"{tick} Succesfully ended **@{user.display_name}'s** LOA",
                                               view=None, allowed_mentions=discord.AllowedMentions.none())                                           
        try:
            loanotification = await consent.find_one({'user_id': self.user.id})
            if loanotification:
                if loanotification.get('LOAAlerts', "Enabled") == "Enabled":            
                 await user.send(f"<:bin:1160543529542635520> Your LOA **@{self.guild.name}** has been voided.")
        except discord.Forbidden:
            print('Failed to send a DM to user. Continuing... (LOA Manage)')
            return


class LOACreate(discord.ui.View):
    def __init__(self, user, guild, author):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.author = author

    @discord.ui.button(label='Create Leave Of Absence', style=discord.ButtonStyle.grey,
                       custom_id='persistent_view:cancel', emoji="<:Add:1163095623600447558>")
    async def CreateLOA(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.send_modal(LOA(self.user, self.guild, self.author))

async def setup(client: commands.Bot) -> None:
    await client.add_cog(loamodule(client))             