import discord
from discord import app_commands
from discord.ext import commands
from emojis import *
from discord.ui import TextInput, Modal
from typing import Literal
import typing
import os
from permissions import has_admin_role, has_staff_role
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)

db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
tags = db['tags']
modules = db['Modules']
ApplicationsChannel = db['Applications Channel']
ApplicationsRolesDB = db['Applications Roles']
applicationn = db['applications']
ApplicationsSubChannel = db['Applications Submissions']
applicationmsglogs = db['Application Message Logs']
options = db['module options']
class ApplicationResults(commands.Cog):
    def __init__(self, client):
        self.client = client
 
    async def applications(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        filter = {
            'guild_id': interaction.guild_id,
            'saved': {'$ne': False}
            
        }

        tag_names = await applicationn.distinct("name", filter)

        filtered_names = [name for name in tag_names if current.lower() in name.lower()]

        choices = [app_commands.Choice(name=name, value=name) for name in filtered_names]

        return choices

    async def modulecheck(self, ctx: commands.Context): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Applications'] == True:   
        return True
    
    @commands.hybrid_command(description="Apply for a position.")
    @app_commands.autocomplete(application=applications)
    async def apply(self, ctx: commands.Context, application: str):
        if not await self.has_required_role(ctx, application):
            return
        
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the applications module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return

        await ctx.defer(ephemeral=True)
        result = await applicationn.find_one({'guild_id': ctx.guild.id, 'name': application, 'saved': {'$ne': False}})

        if result is None:
            await ctx.send(f"{no} **{ctx.author.display_name}**, I could not find this application", allowed_mentions=discord.AllowedMentions.none())
            return
        else:
            blacklists = result.get('blacklists', [])
            if blacklists:
                if ctx.author.id in blacklists:
                    await ctx.send(f"{no} **{ctx.author.display_name}**, you are blacklisted from applying for **{application}**", allowed_mentions=discord.AllowedMentions.none())
                    return
            view = StartApplication(ctx.guild, ctx.author, application)
            await ctx.send(view=view, ephemeral=True)

    async def has_required_role(self, ctx: commands.Context, name):
        filter = {
            'guild_id': ctx.guild.id,
            'name': name
        }
        role_data = await applicationn.find_one(filter)

        if role_data and 'required' in role_data:
            role_ids = role_data['required']
            if not isinstance(role_ids, list):
                role_ids = [role_ids]

            if any(role.id in role_ids for role in ctx.author.roles):
                return True
            else:
                await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to apply for this application.", allowed_mentions=discord.AllowedMentions.none())
                
                return False
        else:
            return True
            

            


    @commands.hybrid_group(description="Application results commands.")
    async def application(self, ctx: commands.Context):
        return
    
    @application.command(description="Blacklist a user from applying from an application.")
    @app_commands.autocomplete(application=applications)
    async def blacklist(self, ctx: commands.Context, user: discord.Member, application: str):
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the applications module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return

        if not await has_admin_role(ctx):
            return
        result = await applicationn.find_one({'guild_id': ctx.guild.id, 'name': application})
        if result is None:
            await ctx.send(f"{no} **{ctx.author.display_name}**, I could not find this application", allowed_mentions=discord.AllowedMentions.none())
            return
        else:
            blacklists = result.get('blacklists', [])
            if user.id in blacklists:
                await ctx.send(f"{no} **{ctx.author.display_name}**, this user is already blacklisted.", allowed_mentions=discord.AllowedMentions.none())
                return
            else:
                await applicationn.update_one({'guild_id': ctx.guild.id, 'name': application}, {'$push': {'blacklists': user.id}})
                await ctx.send(f"{tick} **{ctx.author.display_name}**, this user has been blacklisted from applying for {application}.", allowed_mentions=discord.AllowedMentions.none())



    @application.command(description="Unblacklist a user from applying from an application.")
    @app_commands.autocomplete(application=applications)
    async def unblacklist(self, ctx: commands.Context, user: discord.Member, application: str):
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the applications module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return

        if not await has_admin_role(ctx):
            return
        result = await applicationn.find_one({'guild_id': ctx.guild.id, 'name': application})
        if result is None:
            await ctx.send(f"{no} **{ctx.author.display_name}**, I could not find this application", allowed_mentions=discord.AllowedMentions.none())
            return
        else:
            blacklists = result.get('blacklists', [])
            if user.id not in blacklists:
                await ctx.send(f"{no} **{ctx.author.display_name}**, this user is not blacklisted.", allowed_mentions=discord.AllowedMentions.none())
                return
            else:
                await applicationn.update_one({'guild_id': ctx.guild.id, 'name': application}, {'$pull': {'blacklists': user.id}})
                await ctx.send(f"{tick} **{ctx.author.display_name}**, this user has been unblacklisted from applying for {application}.", allowed_mentions=discord.AllowedMentions.none())        
        


    @application.command(description="Log Application results")
    @app_commands.describe(applicant="The applicant to log the results for", result="The result of the application", feedback="The feedback to give the applicant")
    async def results(
        self, 
        ctx,
        applicant: discord.Member,
        result: Literal["Passed", "Failed"],
        *,
        feedback,
    ):  
        await ctx.defer(ephemeral=True)
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, the applications module isn't enabled.", allowed_mentions=discord.AllowedMentions.none())
            return

        if not await has_admin_role(ctx):
            return

        if result == "Passed":
            if not feedback:
                feedback = "None Given"
            embed = discord.Embed(
                title=f"{greencheck} Application Passed",
                description=f"**Applicant:** {applicant.mention}\n**Feedback:** {feedback}",
                color=discord.Color.brand_green(),
            )
        elif result == "Failed":
            if not feedback:
                feedback = "None Given"
            embed = discord.Embed(
                title=f"{redx} Application Failed",
                description=f"**Applicant:** {applicant.mention}\n**Feedback:** {feedback}",
                color=discord.Color.brand_red(),
            )
        embed.set_thumbnail(url=applicant.display_avatar)
        embed.set_author(
            name=f"Reviewed by {ctx.author.display_name.capitalize()}",
            icon_url=ctx.author.display_avatar,
        )
        
        channeldata = await ApplicationsChannel.find_one({"guild_id": ctx.guild.id})
        if channeldata:
            channelid = channeldata["channel_id"]
            channel = self.client.get_channel(channelid)
            if channel:
                try:
                    msg = await channel.send(f"{applicant.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False, replied_user=False))
                    await ctx.send(f"{tick} **{ctx.author.display_name}**, submitted application results for **@{applicant.display_name}**", allowed_mentions=discord.AllowedMentions.none())
                except discord.Forbidden:
                    await ctx.send(
                        f"{no} **{ctx.author.display_name}**, I don't have permission to send messages in {channel.mention}.", allowed_mentions=discord.AllowedMentions.none()
                    )
                    return

                if result == 'Passed':
                    roles_data = await ApplicationsRolesDB.find_one({"guild_id": ctx.guild.id})
                    if roles_data:
                        application_roles = roles_data.get("applicationroles", [])
                        
                        roles_to_add = [discord.utils.get(ctx.guild.roles, id=role_id) for role_id in application_roles]
                        if roles_to_add and None not in roles_to_add:
                            try:
                                await applicant.add_roles(*roles_to_add)
                            except (discord.Forbidden) as e:
                                await ctx.send(f"{no} **{ctx.author.display_name},** Please check if I have permission to add roles and if I'm higher than the role.", allowed_mentions=discord.AllowedMentions.none())
                                return
                            except Exception(Exception):
                                await ctx.send(f"{crisis} An error has occured if this continues please contact support.")
                                return
                else:
                    await ctx.send(
                        f"{no} **{ctx.author.display_name}**, the specified channel doesn't exist.", allowed_mentions=discord.AllowedMentions.none()
                    )
        else:
            await ctx.send(
                f"{no} **{ctx.author.display_name}**, this channel isn't configured. Please do `/config`.", allowed_mentions=discord.AllowedMentions.none()
            )



class StartApplication(discord.ui.View):
    def __init__(self, guild, author, name):
        super().__init__(timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await ApplicationsSubChannel.find_one({'guild_id': int(self.guild.id)})
        if result is None:
            await interaction.response.edit_message(content=f"{crisis} There is no application submission channel set!", view=None)
            return        
        result = await applicationn.find_one({'guild_id': int(self.guild.id), 'name': self.name})
        if result:
            questions  = result.get('section1', {})
            await interaction.response.send_modal(Section1(self.guild, self.author, self.name, questions))

        


class Section1(discord.ui.Modal):
    def __init__(self, guild, author, name, section_data):
        super().__init__(title="Section 1", timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

        if isinstance(section_data, dict):
            input_counter = 0
            

            for question_name, question_value in list(section_data.items())[:5]:
                if isinstance(question_name, str):
                    input_counter += 1
                    
                    question = self.add_item(discord.ui.TextInput(label=question_value, max_length=1500, style=discord.TextStyle.long))
                    
                    

                    if input_counter >= 5:
                        break

    async def on_submit(self, interaction: discord.Interaction) -> None:
        result = await applicationn.find_one({'guild_id': int(self.guild.id), 'name': self.name})
        input_responses = {}

        for question in self.children:
            if isinstance(question, discord.ui.TextInput):
                input_responses[question.label] = question.value
        embed = discord.Embed(title="Section 1", description="", color=discord.Color.dark_embed())
        embed.set_author(name=f"{self.author.display_name}s Application", icon_url=self.author.display_avatar)
        embed.set_thumbnail(url=self.author.display_avatar)
        embed.set_image(url="https://astrobirb.dev/assets/img/logos/invisible.png")
        embed.set_footer(text=f"{(self.name).capitalize()} Application")
        for question_label, response in input_responses.items():
            embed.description += f"### **{question_label}**\n{response}\n"



        if result:
            questions  = result.get('section2', {})
            if questions:
              view = Continue(self.guild, self.author, self.name)
              await interaction.response.edit_message(embed=embed, view=view)                     
            else:
                view = Finish(self.guild, self.author, self.name)      
                await interaction.response.edit_message(embed=embed, view=view)   
class Section2(discord.ui.Modal):
    def __init__(self, guild, author, name, section_data):
        super().__init__(title="Section 2", timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

        if isinstance(section_data, dict):
            input_counter = 0
            

            for question_name, question_value in list(section_data.items())[:5]:
                if isinstance(question_name, str):
                    input_counter += 1
                    
                    question = self.add_item(discord.ui.TextInput(label=question_value, max_length=1500, style=discord.TextStyle.long))
                    
                    

                    if input_counter >= 5:
                        break

    async def on_submit(self, interaction: discord.Interaction) -> None:
        result = await applicationn.find_one({'guild_id': int(self.guild.id), 'name': self.name})
        input_responses = {}

        for question in self.children:
            if isinstance(question, discord.ui.TextInput):
                input_responses[question.label] = question.value
        embed = discord.Embed(title="Section 2", description="", color=discord.Color.dark_embed())
        embed.set_image(url="https://astrobirb.dev/assets/img/logos/invisible.png")

        for question_label, response in input_responses.items():
            embed.description += f"### **{question_label}**\n{response}\n"

        embeds = interaction.message.embeds
        embeds.append(embed)

        if result:
            questions = result.get('section3', {})
            if questions:
                view = Continue2(self.guild, self.author, self.name) 
                await interaction.response.edit_message(embeds=embeds, view=view)
            else:
                view = Finish(self.guild, self.author, self.name)      
                await interaction.response.edit_message(embeds=embeds, view=view)

class Section3(discord.ui.Modal):
    def __init__(self, guild, author, name, section_data):
        super().__init__(title="Section 3", timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

        if isinstance(section_data, dict):
            input_counter = 0
            

            for question_name, question_value in list(section_data.items())[:5]:
                if isinstance(question_name, str):
                    input_counter += 1
                    
                    question = self.add_item(discord.ui.TextInput(label=question_value, max_length=1500, style=discord.TextStyle.long))
                    
                    

                    if input_counter >= 5:
                        break

    async def on_submit(self, interaction: discord.Interaction) -> None:
        result = await applicationn.find_one({'guild_id': int(self.guild.id), 'name': self.name})
        input_responses = {}

        for question in self.children:
            if isinstance(question, discord.ui.TextInput):
                input_responses[question.label] = question.value
        embed = discord.Embed(title="Section 3", description="", color=discord.Color.dark_embed())
        embed.set_image(url="https://astrobirb.dev/assets/img/logos/invisible.png")

        for question_label, response in input_responses.items():
            embed.description += f"### **{question_label}**\n{response}\n"

        embeds = interaction.message.embeds
        embeds.append(embed)

        if result:
            questions = result.get('section4', {})
            view = Continue3(self.guild, self.author, self.name)
            if questions:
                await interaction.response.edit_message(embeds=embeds, view=view)       
            else:
                view = Finish(self.guild, self.author, self.name)      
                await interaction.response.edit_message(embeds=embeds, view=view)
class Section4(discord.ui.Modal):
    def __init__(self, guild, author, name, section_data):
        super().__init__(title="Section 4", timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

        if isinstance(section_data, dict):
            input_counter = 0
            

            for question_name, question_value in list(section_data.items())[:5]:
                print(question_value)
                if isinstance(question_name, str):
                    input_counter += 1
                    
                    question = self.add_item(discord.ui.TextInput(label=question_value, max_length=1500, style=discord.TextStyle.long))
                    
                    

                    if input_counter >= 5:
                        break

    async def on_submit(self, interaction: discord.Interaction) -> None:
        result = await applicationn.find_one({'guild_id': int(self.guild.id), 'name': self.name})
        input_responses = {}

        for question in self.children:
            if isinstance(question, discord.ui.TextInput):
                input_responses[question.label] = question.value
        embed = discord.Embed(title="Section 4", description="", color=discord.Color.dark_embed())
        embed.set_image(url="https://astrobirb.dev/assets/img/logos/invisible.png")

        for question_label, response in input_responses.items():
            embed.description += f"### **{question_label}**\n{response}\n"

        embeds = interaction.message.embeds
        embeds.append(embed)

        if result:
            questions = result.get('section5', {})
            view = Continue4(self.guild, self.author, self.name)
            if questions:
                await interaction.response.edit_message(embeds=embeds, view=view)   
            else:
                view = Finish(self.guild, self.author, self.name)      
                await interaction.response.edit_message(embeds=embeds, view=view)

class Section5(discord.ui.Modal):
    def __init__(self, guild, author, name, section_data):
        super().__init__(title="Section 5", timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

        if isinstance(section_data, dict):
            input_counter = 0
            

            for question_name, question_value in list(section_data.items())[:5]:
                if isinstance(question_name, str):
                    input_counter += 1
                    
                    question = self.add_item(discord.ui.TextInput(label=question_value, max_length=1500, style=discord.TextStyle.long))
                    
                    

                    if input_counter >= 5:
                        break

    async def on_submit(self, interaction: discord.Interaction) -> None:
        input_responses = {}

        for question in self.children:
            if isinstance(question, discord.ui.TextInput):
                input_responses[question.label] = question.value
        embed = discord.Embed(title="Section 5", description="", color=discord.Color.dark_embed())
        embed.set_image(url="https://astrobirb.dev/assets/img/logos/invisible.png")

        for question_label, response in input_responses.items():
            embed.description += f"### **{question_label}**\n{response}\n"

        embeds = interaction.message.embeds
        embeds.append(embed)
        view = Finish(self.guild, self.author, self.name)
        await interaction.response.edit_message(embeds=embeds, view=view)    

class Continue(discord.ui.View):
    def __init__(self, guild, author, name):
        super().__init__(timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.blurple)
    async def Continue(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await applicationn.find_one({'guild_id': int(self.guild.id), 'name': self.name})
        print(result)
        if result:
            questions  = result.get('section2', {})
            print(questions )
            await interaction.response.send_modal(Section2(self.guild, self.author, self.name, questions))    

class Continue2(discord.ui.View):
    def __init__(self, guild, author, name):
        super().__init__(timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.blurple)
    async def Continue2(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await applicationn.find_one({'guild_id': int(self.guild.id), 'name': self.name})
        print(result)
        if result:
            questions  = result.get('section3', {})
            print(questions)
            await interaction.response.send_modal(Section3(self.guild, self.author, self.name, questions))    

class Continue3(discord.ui.View):
    def __init__(self, guild, author, name):
        super().__init__(timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.blurple)
    async def Continue3(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await applicationn.find_one({'guild_id': int(self.guild.id), 'name': self.name})
        print(result)
        if result:
            questions  = result.get('section4', {})
            print(questions)
            await interaction.response.send_modal(Section4(self.guild, self.author, self.name, questions)) 

class Continue4(discord.ui.View):
    def __init__(self, guild, author, name):
        super().__init__(timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.blurple)
    async def Continue4(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await applicationn.find_one({'guild_id': int(self.guild.id), 'name': self.name})
        print(result)
        if result:
            questions  = result.get('section5', {})
            print(questions)
            await interaction.response.send_modal(Section5(self.guild, self.author, self.name, questions)) 

                      

class Finish(discord.ui.View):
    def __init__(self, guild, author, name):
        super().__init__(timeout=None)
        self.guild = guild
        self.author = author
        self.name = name

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
    async def Submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = interaction.message.embeds
        result = await ApplicationsSubChannel.find_one({'guild_id': int(self.guild.id)})
        if result is None:
            await interaction.response.send_message(f"{crisis} There is no application submission channel set!", ephemeral=True)
            return
        if result:
            channel = interaction.guild.get_channel(result.get('channel_id'))
            if channel is None:
                await interaction.response.send_message(f"{crisis} The application submission channel could not be found!", ephemeral=True)
                return
            else:
                optionsresult = await options.find_one({'guild_id': interaction.guild.id})
                if optionsresult:
                  if optionsresult.get('acceptbuttons', False) == True:
                      view = AcceptAndDeny()
                  else:    
                      view = None
                else:
                    view = None      
                
                try:
                 msg = await channel.send(embeds=embeds, view=view)
                except discord.Forbidden:
                    await interaction.response.send_message(f"{crisis} I do not have permission to send messages in the application submission channel!", ephemeral=True)
                    return 
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Submitted!", style=discord.ButtonStyle.green, disabled=True))
                await interaction.response.edit_message(view=view)
                await applicationmsglogs.insert_one({'guild_id': int(self.guild.id), 'msgid': msg.id, 'applicantid': self.author.id, 'application': self.name})
                if optionsresult:
                    if optionsresult.get('threaddiscussion'):
                        try:
                            await msg.create_thread(name="Application Discussion")
                        except:
                            print("I don't have permission to create a thread.")
                            pass    
        
class AcceptAndDeny(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="accept:persistants")
    async def Accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PassReason())


    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, custom_id="accept:deny")
    async def Deny(self, interaction: discord.Interaction, button: discord.ui.Button):
       await interaction.response.send_modal(DenyReason())

class PassReason(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Any Feedback?")

    reason = discord.ui.TextInput(label="Do you want to add any feedback to this?", required=False)

    async def on_submit(self, interaction: discord.Interaction) -> None:
            await interaction.response.defer()
            result = await applicationmsglogs.find_one({'guild_id': int(interaction.guild_id), 'msgid': interaction.message.id})
            channelresult = await ApplicationsChannel.find_one({'guild_id': interaction.guild.id})
            if result is None:
                await interaction.followup.send(f"{crisis} The application data could not be found!", ephemeral=True)
                return
            else:
             applicant = interaction.guild.get_member(result.get('applicantid'))
             if applicant is None:
                 await interaction.followup.send(f"{crisis} The applicant is no longer in the server.", ephemeral=True)
                 return
             feedback = self.reason.value

             if not self.reason.value:
                feedback = "None Given"
             if channelresult is None:
                 await interaction.followup.send(f"{crisis} There is no application results channel set!", ephemeral=True)
                 return
             else:
              channel = interaction.guild.get_channel(channelresult.get('channel_id'))
              if channel is None:
                  await interaction.followup.send(f"{crisis} I can not find the application results channel!", ephemeral=True)
                  return
              result = await applicationn.find_one({'guild_id': interaction.guild.id, 'name': result.get('application')})
              if result:
                application_roles = result.get("Accepted", [])
                if application_roles:
                        
                         roles_to_add = [discord.utils.get(interaction.guild.roles, id=role_id) for role_id in application_roles]
                         if roles_to_add and None not in roles_to_add:
                            try:
                                await applicant.add_roles(*roles_to_add)
                            except (discord.Forbidden) as e:
                                await interaction.followup.send(f"{no} **{interaction.user.display_name},** Please check if I have permission to add roles and if I'm higher than the role.", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
                                return
                            except Exception(Exception):
                                await interaction.followup.send(f"{crisis} An error has occured if this continues please contact support.", ephemeral=True)
                                return              
              embed = discord.Embed(
                title=f"{greencheck} Application Passed",
                description=f"**Applicant:** {applicant.mention}\n**Feedback:** {feedback}",
                color=discord.Color.brand_green(),
             )
              embed.set_thumbnail(url=applicant.display_avatar)
              embed.set_author(
                name=f"Reviewed by {interaction.user.display_name.capitalize()}",
                icon_url=interaction.user.display_avatar,) 
              embed.set_footer(text=f"{result.get('application')} Application")                        
              try:
               await channel.send(f"{applicant.mention}", embed=embed)
              except discord.Forbidden:
                  await interaction.followup.send(f"{crisis} I could not see or send a message to the application results channel.", ephemeral=True) 
                  return
              view = discord.ui.View()
              view.add_item(discord.ui.Button(label="Accepted!", style=discord.ButtonStyle.green, disabled=True))              
              await interaction.edit_original_response(view=view)
        
class DenyReason(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Any Feedback?")

    reason = discord.ui.TextInput(label="Do you want to add any feedback to this?", required=False)

    async def on_submit(self, interaction: discord.Interaction) -> None:    
            result = await applicationmsglogs.find_one({'guild_id': int(interaction.guild_id), 'msgid': interaction.message.id})
            channelresult = await ApplicationsChannel.find_one({'guild_id': interaction.guild.id})
            if result is None:
                await interaction.response.send_message(f"{crisis} The application data could not be found!", ephemeral=True)
                return
            else:
             applicant = interaction.guild.get_member(result.get('applicantid'))
             if applicant is None:
                 await interaction.response.send_message(f"{crisis} The applicant is no longer in the server.", ephemeral=True)
                 return
             feedback = self.reason.value

             if not self.reason.value:
                feedback = "None Given"
             if channelresult is None:
                 await interaction.response.send_message(f"{crisis} There is no application results channel set!", ephemeral=True)
                 return
             else:
              channel = interaction.guild.get_channel(channelresult.get('channel_id'))
              if channel is None:
                  await interaction.response.send_message(f"{crisis} I can not find the application results channel!", ephemeral=True)
                  return
              
              embed = discord.Embed(
                title=f"{redx} Application Failed",
                description=f"**Applicant:** {applicant.mention}\n**Feedback:** {feedback}",
                color=discord.Color.brand_red(),
            )
              embed.set_thumbnail(url=applicant.display_avatar)
              embed.footer
              embed.set_author(
                name=f"Reviewed by {interaction.user.display_name.capitalize()}",
                icon_url=interaction.user.display_avatar,
        )     
              embed.set_footer(text=f"{result.get('application')} Application")                        
              try:
               await channel.send(f"{applicant.mention}", embed=embed)
              except discord.Forbidden:
                  await interaction.response.send_message(f"{crisis} I could not see or send a message to the application results channel.", ephemeral=True) 
                  return
              view = discord.ui.View()
              view.add_item(discord.ui.Button(label="Denied!", style=discord.ButtonStyle.red, disabled=True))              
              await interaction.response.edit_message(view=view)              

async def setup(client: commands.Bot) -> None:
    await client.add_cog(ApplicationResults(client))        