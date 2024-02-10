
import discord
from discord.ext import commands
from typing import Optional
import datetime
import pytz
from discord import app_commands
import os
from emojis import *
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URL = os.getenv('MONGO_URL')
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo['astro']
repchannel = db['report channel']
modules = db['Modules']
reports = db['Reports']
ReportModeratorRole = db['Report Moderator Role']
scollection = db['staffrole']
arole = db['adminrole']

class MuteReason(discord.ui.Modal, title='Reason'):
    def __init__(self, embed, messageid, message):
        super().__init__()
        self.embed = embed
        self.messageid = messageid
        self.message = message

    Reason = discord.ui.TextInput(
        label='Reason?',
        placeholder='Whats the reason for the mute?',
    )

    Duration = discord.ui.TextInput(
        label='Duration?',
        placeholder='For example 1d = 1 day (m/d/h)',
    )

    async def on_submit(self, interaction: discord.Interaction):
        duration_value = int(self.Duration.value[:-1])
        duration_unit = self.Duration.value[-1]

        if duration_unit == 'm':
            duration = timedelta(minutes=duration_value)
        elif duration_unit == 'h':
            duration = timedelta(hours=duration_value)
        elif duration_unit == 'd':
            duration = timedelta(days=duration_value)
        elif duration_unit == 'w':
            duration = timedelta(weeks=duration_value)
        else:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, Invalid duration unit. Use 'm' for minutes, 'h' for hours, 'd' for days, and 'w' for weeks.", ephemeral=True)
            return

        reportsresult = await reports.find_one({'message_id': self.messageid})
        reporteduserid = reportsresult['reporteduser']

        reporteduser = interaction.guild.get_member(reporteduserid)
        if reporteduser is None:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, I could not find this user!", ephemeral=True)
            return

        try:
            await reporteduser.timeout(duration, reason=f"Muted By {interaction.user.display_name} | {self.Reason.value}")
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, I do not have permission to mute this user!", ephemeral=True)
            return

        self.embed.title = f"{greencheck} Report Resolved"
        self.embed.color = discord.Colour.brand_green()
        self.embed.set_footer(text=f"Muted By {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        self.embed.add_field(name="Mute Reason", value=self.Reason.value, inline=True)
        self.embed.add_field(name="Mute Duration", value=self.Duration.value, inline=True)
        message = self.message
        try:
            await reporteduser.send(f"<:Infraction:1162134605885870180> You have been muted from **{interaction.guild.name}** for `{self.Duration.value}`| {self.Reason.value}")
        except discord.Forbidden:
            pass
        try:
            await message.edit(embed=self.embed, view=None)
            await interaction.response.send_message(f"{tick} **{interaction.user.display_name}**, Successfully muted **@{reporteduser}** for `{self.Duration.value}`.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, I can't edit this message", ephemeral=True)
            return


class KickReason(discord.ui.Modal, title='Reason'):
    def __init__(self, embed, messageid, message):
        super().__init__()
        self.embed = embed
        self.messageid = messageid
        self.message = message

    Reason = discord.ui.TextInput(
        label='Reason?',
        placeholder='Whats the reason for the kick?',
    )

    async def on_submit(self, interaction: discord.Interaction):
        reportsresult = await reports.find_one({'message_id': self.messageid})
        reporteduserid = reportsresult['reporteduser']

        reporteduser = interaction.guild.get_member(reporteduserid)
        if reporteduser is None:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, I could not find this user!", ephemeral=True)
            return
        try:
            await reporteduser.kick(reason=f"Kicked By {interaction.user.display_name} | {self.Reason.value}")
        except discord.Forbidden:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, I do not have permission to kick this user!", ephemeral=True)
            return
        self.embed.title = f"{greencheck} Report Resolved"
        self.embed.color = discord.Colour.brand_green()
        self.embed.set_footer(text=f"Kicked By {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        self.embed.add_field(name="Kick Reason", value=self.Reason.value, inline=False)
        message = self.message
        try:
            await reporteduser.send(f"<:Infraction:1162134605885870180> You have been kicked from **{interaction.guild.name}** | {self.Reason.value}")
        except discord.Forbidden:
            pass
        try:
            await message.edit(embed=self.embed, view=None)
            await interaction.response.send_message(f"{tick} **{interaction.user.display_name}**, Successfully kicked **@{reporteduser}**.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, I can't to edit this message", ephemeral=True)
            return


class BanReason(discord.ui.Modal, title='Reason'):
    def __init__(self, embed, messageid, message):
        super().__init__()
        self.embed = embed
        self.messageid = messageid
        self.message = message

    Reason = discord.ui.TextInput(
        label='Reason?',
        placeholder='Whats the reason for the ban?',
    )

    async def on_submit(self, interaction: discord.Interaction):
        reportsresult = await reports.find_one({'message_id': self.messageid})
        reporteduserid = reportsresult['reporteduser']

        reporteduser = interaction.guild.get_member(reporteduserid)
        if reporteduser is None:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, I could not find this user!", ephemeral=True)
            return
        try:
            await reporteduser.guild.ban(reason=f"Banned By {interaction.user.display_name} | {self.Reason.value}")
        except discord.Forbidden:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, I do not have permission to ban this user!", ephemeral=True)
            return
        self.embed.title = f"{greencheck} Report Resolved"
        self.embed.color = discord.Colour.brand_green()
        self.embed.set_footer(text=f"Banned By {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        self.embed.add_field(name="Ban Reason", value=self.Reason.value, inline=False)
        message = self.message
        try:
            await reporteduser.send(f"<:Infraction:1162134605885870180> You have been banned from **{interaction.guild.name}** | {self.Reason.value}")
        except discord.Forbidden:
            pass
        try:
            await message.edit(embed=self.embed, view=None)
            await interaction.response.send_message(f"{tick} **{interaction.user.display_name}**, Successfully kicked **@{reporteduser}**.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, I can't to edit this message", ephemeral=True)
            return


        


class Reports(commands.Cog):
    def __init__(self, bot):
        self.client = bot

        reported_at = datetime.utcnow().timestamp()
        reported_at_format = f"<t:{int(reported_at)}:F>"

    async def modulecheck(self, ctx): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Reports'] == True:   
        return True 


    

    @commands.hybrid_command(description="Report users breaking server rules.")
    @app_commands.describe(
        member='Who are you reporting?',
        reason='What is the reason for reporting this user',
        message_link='Do you have proof of this person doing this?')
    async def report(self, ctx, member: discord.User, *, reason: str, message_link: Optional[str] = None, proof: discord.Attachment, proof2: discord.Attachment = None, proof3: discord.Attachment = None, proof4: discord.Attachment = None, proof5: discord.Attachment = None, proof6: discord.Attachment = None, proof7: discord.Attachment = None, proof8: discord.Attachment = None, proof9: discord.Attachment = None):
        await ctx.defer()
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
         return         

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


        embed = discord.Embed(title=f"{cpending} Pending Report", color=discord.Color.orange())
        embed.add_field(name="Reported User", value=f"* **User:** {member.mention}\n* **ID:** {member.id}", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        if message_link:
            embed.add_field(name=f"Report Information", value=f"* **Reported By:** {ctx.author.mention}\n* **Reason:** {reason}\n* **Message Link:** {message_link}\n* **Reported At:** {reported_at_format}", inline=False)    
            embed.add_field(name="Proof", value=f"{proof_message}", inline=False)        
        else:
            embed.add_field(name=f"Report Information", value=f"* **Reported By:** {ctx.author.mention}\n* **Reason:** {reason}\n* **Reported At:** {reported_at_format}", inline=False)
            embed.add_field(name="Proof", value=f"{proof_message}", inline=False) 
                   

        
        guild_id = ctx.guild.id
        data = await repchannel.find_one({'guild_id': guild_id})

        if data:
                channel_id = data['channel_id']
                channel = self.client.get_channel(channel_id)

                if channel:
                    
                    try:
                     view = ReportPanel()
                     msg = await channel.send(embed=embed, view=view)
                     await ctx.send(f"{tick} **{ctx.author.display_name}**, your report has been submitted.", ephemeral=True)

                     await reports.insert_one({'guild_id': ctx.guild.id, 'channel_id': channel_id, 'reportedby': ctx.author.id, 'reporteduser': member.id, 'reason': reason, 'message_link': message_link, 'proof': proof_message, 'reported_at': reported_at_format, 'message_id': msg.id})
                    except discord.Forbidden:
                       await ctx.send(f"{no} **{ctx.author.display_name}**, I don't have permission to view the channel please contact **administrators**.")
                       return
                else:
                    await ctx.send(f"**{ctx.author.display_name}**, I don't have permission to view this channel.")
        else:
                await ctx.send(f"**{ctx.author.display_name}**, the channel is not setup please run `/config`")
 
         




class ActionsPanel(discord.ui.View):
    def __init__(self, embed, messageid, message):
        super().__init__(timeout=None)
        self.embed = embed
        self.messageid = messageid
        self.message = message


    @discord.ui.button(label='Kick', style=discord.ButtonStyle.grey, custom_id='Kick', emoji="<:kick:1188186854214864956>")
    async def Kick(self, interaction: discord.Interaction, button: discord.ui.Button):

      await interaction.response.send_modal(KickReason(self.embed, self.messageid, self.message))

    @discord.ui.button(label='Mute', style=discord.ButtonStyle.grey, custom_id='Mute', emoji="<:mute:1188186757750079499>")
    async def Mute(self, interaction: discord.Interaction, button: discord.ui.Button):
    
     await interaction.response.send_modal(MuteReason(self.embed, self.messageid, self.message))

    @discord.ui.button(label='Ban', style=discord.ButtonStyle.grey, custom_id='Ban', emoji="<:ban:1188186221592195224>")
    async def Ban(self, interaction: discord.Interaction, button: discord.ui.Button):

     await interaction.response.send_modal(BanReason(self.embed, self.messageid, self.message))



             


class ReportPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def has_moderator_role(self, interaction):


     filter = {
        'guild_id': interaction.guild.id
    }
     staff_data = await ReportModeratorRole.find_one(filter)

     if staff_data and 'staffrole' in staff_data:
        staff_role_ids = staff_data['staffrole']
        if not isinstance(staff_role_ids, list):
            staff_role_ids = [staff_role_ids]


        admin_data = await arole.find_one(filter)

        if not admin_data:
            pass
        else:
            if 'staffrole' in admin_data:
                admin_role_ids = admin_data['staffrole']
                admin_role_ids = admin_role_ids if isinstance(admin_role_ids, list) else [admin_role_ids]

                if any(role.id in staff_role_ids + admin_role_ids for role in interaction.user.roles):
                    return True

        if any(role.id in staff_role_ids for role in interaction.author.roles):
            return True

     else:
        if interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, the reports moderator role isn't set. Please run </config:1140463441136586784>", ephemeral=True)
        else:
            await interaction.response.send_message(f"{no} **{self.user .display_name}**, the reports moderator role isn't set up. Please tell an admin to run </config:1140463441136586784> to fix it.", ephemeral=True)
        return False

     return False

    @discord.ui.button(label='Actions', style=discord.ButtonStyle.blurple, custom_id='Actions', emoji="<:Setting:1154092651193323661>")
    async def Actions(self, interaction: discord.Interaction, button: discord.ui.Button):
       if not await self.has_moderator_role(interaction):
         await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, you don't have permission to use this panel.\n<:Arrow:1115743130461933599>**Required:** `Reports Moderator Role`", ephemeral=True)
         return   
       
       reportsresult = await reports.find_one({'message_id': interaction.message.id})
       if reportsresult is None:
              await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, there was no report data found.", ephemeral=True)
              return
          
       if reportsresult:
        reporteduser = interaction.guild.get_member(reportsresult['reporteduser'])   
        if reporteduser is None:
           await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, I can't find this user.", ephemeral=True)
           return
        embed = interaction.message.embeds[0]
        message = interaction.message
        view = ActionsPanel(embed, interaction.message.id, message)
        await interaction.response.send_message(view=view, ephemeral=True)
                        
    @discord.ui.button(label='Ignore', style=discord.ButtonStyle.grey, custom_id='ignore:button', emoji=f"{redx}")
    async def Ignore(self, interaction: discord.Interaction, button: discord.ui.Button):
       if not await self.has_moderator_role(interaction):
         await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, you don't have permission to use this panel.\n<:Arrow:1115743130461933599>**Required:** `Reports Moderator Role`", ephemeral=True)
         return 
       reportsresult = await reports.find_one({'message_id': interaction.message.id})
       if reportsresult is None:
              await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, there was no report data found.", ephemeral=True)
              return   
       embed = interaction.message.embeds[0]
       
       embed.title = f"{redx} Report Ignored"
       embed.color = discord.Color.brand_red()
       embed.set_footer(text=f"Ignored by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
       await interaction.response.edit_message(embed=embed, view=None)





              

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Reports(client))        