import discord
import discord
from discord.ext import commands
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from discord.ui import button
import os
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
modules = db['Modules']
suggestions_collection = db["suggestions"]
from emojis import *
suggestschannel = db["suggestion channel"]
class suggestions(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def modulecheck(self, ctx): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata.get('Suggestions', False) == True: 
        return True
     else:   
        return False


    @commands.hybrid_command(description="Submit a suggestion for improvement")
    async def suggest(self, ctx, suggestion: str):
        if not await self.modulecheck(ctx):
         await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.", allowed_mentions=discord.AllowedMentions.none())
         return    

        suggestion_data = {
            "author_id": ctx.author.id,
            "suggestion": suggestion,
            "upvotes": 0,
            "downvotes": 0,
            "upvoters": [],
            "downvoters": [],
            'guild_id': ctx.guild.id
        }
        result = await suggestions_collection.insert_one(suggestion_data)
        suggestion_id = result.inserted_id

        embed = discord.Embed(title="", description=f"**Submitter**\n {ctx.author.mention} \n\n**Suggestion**\n{suggestion}", color=discord.Color.dark_embed())
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1143363161609736192/1152281646414958672/invisible.png")
        embed.set_author(icon_url=ctx.guild.icon, name=ctx.guild.name)
        embed.set_footer(text=f"0 Upvotes | 0 Downvotes")
        view = SuggestionView()
        view.add_item(ManageSuggestion())
        channeldata = await suggestschannel.find_one({"guild_id": ctx.guild.id})
        if channeldata:
         channel_id = channeldata['channel_id']
         channel = self.client.get_channel(channel_id)
         if channel:
          try:  
           msg = await channel.send(embed=embed, view=view)
           await ctx.send(f"{tick} **{ctx.author.display_name}**, succesfully sent the suggestion.", allowed_mentions=discord.AllowedMentions.none())
           await suggestions_collection.update_one({"_id": suggestion_id}, {"$set": {"message_id": msg.id}})           
          except discord.Forbidden: 
             await ctx.send(f"{no} I don't have permission to view that channel.")              
             return

        else: 
            await ctx.send(f"{no} {ctx.author.display_name}, this channel isn't configured. Please do `/config`.", allowed_mentions=discord.AllowedMentions.none())



    async def update_embed(self, interaction: discord.Interaction):
        suggestion_data = await suggestions_collection.find_one({"_id": self.suggestion_id})
        embed = interaction.message.embeds[0]
        upvotes, downvotes = suggestion_data["upvotes"], suggestion_data["downvotes"]
        embed.set_footer(text=f"{upvotes} Upvotes | {downvotes} Downvotes")
        await interaction.message.edit(embed=embed)

class SuggestionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def on_timeout(self):
        self.clear_items()

    @button(label='Upvote', style=discord.ButtonStyle.green, custom_id="upvote_button", emoji="<:UpVote:1183063056834646066>")
    async def Yes(self, interaction, button):
        message_id = interaction.message.id
        suggestion_data = await suggestions_collection.find_one({"message_id": message_id})
        if suggestion_data is None:
            await interaction.response.send_message(f"{crisis} **Suggestion** data for this suggestion can not be found.", ephemeral=True)
            return
        upvoters = suggestion_data.get("upvoters", [])
        downvoters = suggestion_data.get("downvoters", [])

        if interaction.user.id in upvoters:
            await suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"upvotes": -1},
                    "$pull": {"upvoters": interaction.user.id},
                },
            )
            suggestion_data = await suggestions_collection.find_one({"message_id": message_id})  
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Unvoted.", ephemeral=True)
        elif interaction.user.id in downvoters:
            await suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"upvotes": 1, "downvotes": -1},
                    "$pull": {"downvoters": interaction.user.id},
                    "$push": {"upvoters": interaction.user.id},
                },
            )
            suggestion_data = await suggestions_collection.find_one({"message_id": message_id})  
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Switched to upvote.", ephemeral=True)
        else:
            await suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"upvotes": 1},
                    "$push": {"upvoters": interaction.user.id},
                },
            )
            suggestion_data = await suggestions_collection.find_one({"message_id": message_id})  
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Upvoted.", ephemeral=True)

    @button(label='Downvote', style=discord.ButtonStyle.red, custom_id="downvote_button", emoji="<:DownVote:1183063097477451797>")
    async def No(self, interaction, button):
        message_id = interaction.message.id
        suggestion_data = await suggestions_collection.find_one({"message_id": message_id})
        if suggestion_data is None:
            await interaction.response.send_message(f"{crisis} **Suggestion** data for this suggestion can not be found.", ephemeral=True)
            return        
        upvoters = suggestion_data.get("upvoters", [])
        downvoters = suggestion_data.get("downvoters", [])

        if interaction.user.id in downvoters:
            await suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"downvotes": -1},
                    "$pull": {"downvoters": interaction.user.id},
                },
            )
            suggestion_data = await suggestions_collection.find_one({"message_id": message_id})  
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Unvoted.", ephemeral=True)
        elif interaction.user.id in upvoters:
            await suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"upvotes": -1, "downvotes": 1},
                    "$pull": {"upvoters": interaction.user.id},
                    "$push": {"downvoters": interaction.user.id},
                },
            )
            suggestion_data = await suggestions_collection.find_one({"message_id": message_id}) 
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Switched to downvote.", ephemeral=True)
        else:
            await suggestions_collection.update_one(
                {"message_id": message_id},
                {
                    "$inc": {"downvotes": 1},
                    "$push": {"downvoters": interaction.user.id},
                },
            )
            suggestion_data = await suggestions_collection.find_one({"message_id": message_id})  
            await self.update_embed(interaction, suggestion_data)
            await interaction.response.send_message("Downvoted.", ephemeral=True)

    async def update_embed(self, interaction, suggestion_data):
        if interaction.message:
            print(f"Editing message with ID {interaction.message.id}")
            embed = interaction.message.embeds[0]
            upvotes, downvotes = suggestion_data["upvotes"], suggestion_data["downvotes"]
            embed.set_footer(text=f"{upvotes} Upvotes | {downvotes} Downvotes")
            await interaction.message.edit(embed=embed)
        else:
            print("Interaction message is None!")

    @button(label='Voters List', style=discord.ButtonStyle.gray, custom_id="view_voters_button", emoji="<:List:1179470251860185159>")
    async def view_voters(self, interaction, button):
        message_id = interaction.message.id
        suggestion_data = await suggestions_collection.find_one({"message_id": message_id})

        upvoters = suggestion_data.get("upvoters", [])
        downvoters = suggestion_data.get("downvoters", [])

        upvoters_mentions = [f"<@{upvoter}>" for upvoter in upvoters]
        downvoters_mentions = [f"<@{downvoter}>" for downvoter in downvoters]

        embed = discord.Embed(title="Voters List", color=discord.Color.dark_embed())
        embed.add_field(name="Upvoters", value="\n".join(upvoters_mentions) or "No upvoters")
        embed.add_field(name="Downvoters", value="\n".join(downvoters_mentions) or "No downvoters")

        await interaction.response.send_message(embed=embed, ephemeral=True)

class SuggestionManageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ManageSuggestion())

class ManageSuggestion(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Accept", emoji=f"{tick}"),
            discord.SelectOption(label="Deny", emoji=f"{no}")
            

        
            
        ]
        super().__init__(placeholder='⚙️ |  Suggestion Manage', min_values=1, max_values=1, options=options, custom_id="manage_suggestion_select")







    async def callback(self, interaction: discord.Interaction):
        if not await self.has_staff_role(interaction): 
            return
        color = self.values[0]
        if color == "Accept":
         suggestiondata = await suggestions_collection.find_one({"message_id": interaction.message.id})
         if suggestiondata is None:
            await interaction.response.send_message(f"{no} I can not find the suggestion data for this suggestion.", ephemeral=True)
            return
         embed = interaction.message.embeds[0]
         embed.title = f"{greencheck} Suggestion Accepted"
         embed.color = discord.Color.brand_green()
         view = SuggestionView()
         view.view_voters.disabled = False
         view.No.disabled = True
         view.Yes.disabled = True        
         await interaction.message.edit(embed=embed, view=view)
         await interaction.response.send_message(f"{tick} Suggestion Accepted", ephemeral=True)
        elif color == "Deny":
            await interaction.response.send_modal(Deny())

    async def has_staff_role(self, interaction):
        filter = {'guild_id': interaction.guild.id}
        staff_data = await scollection.find_one(filter)

        if staff_data and 'staffrole' in staff_data:
            staff_role_ids = staff_data['staffrole']
            staff_role_ids = staff_role_ids if isinstance(staff_role_ids, list) else [staff_role_ids]


            admin_data = await arole.find_one(filter)


            if not admin_data:

                pass
            else:
                if 'staffrole' in admin_data:
                    admin_role_ids = admin_data['staffrole']
                    admin_role_ids = admin_role_ids if isinstance(admin_role_ids, list) else [admin_role_ids]

                    if any(role.id in staff_role_ids + admin_role_ids for role in interaction.user.roles):
                        return True


            if any(role.id in staff_role_ids for role in interaction.user.roles):
                return True
        else:
            if interaction.user.guild_permissions.administrator:
                

             await interaction.user.send(f"{no} **{interaction.user.display_name}**, the staff role isn't set please run </config:1140463441136586784>!", view=PermissionsButtons(), allowed_mentions=discord.AllowedMentions.none())
            else:
                await interaction.user.send(f"{no} **{interaction.user.display_name}**, the admin role is not setup please tell an admin to run </config:1140463441136586784> to fix it!", view=PermissionsButtons(), allowed_mentions=discord.AllowedMentions.none()) 
            return
        await interaction.response.send_message(f"{no} **{interaction.user.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Staff Role`", allowed_mentions=discord.AllowedMentions.none())
        return False

class Deny(discord.ui.Modal, title='Deny'):
    def __init__(self):
        super().__init__()

    reason = discord.ui.TextInput(label='Reason', style=discord.TextStyle.long, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        suggestiondata = await suggestions_collection.find_one({"message_id": interaction.message.id})
        if suggestiondata is None:
            await interaction.response.send_message(f"{no} I can not find the suggestion data for this suggestion.", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        embed.title = f"{redx} Suggestion Denied"
        embed.color = discord.Color.brand_red()
        embed.add_field(name="<:ApplicationFeedback:1178754449125167254> Deny Reason", value=self.reason.value)
        view = SuggestionView()
        view.view_voters.disabled = False
        view.No.disabled = True
        view.Yes.disabled = True
        await interaction.message.edit(embed=embed, view=view)
        await interaction.response.send_message(f"{tick} Suggestion Denied", ephemeral=True)
   
class PermissionsButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        url1 = f'https://discord.gg/DhWdgfh3hN'
        self.add_item(discord.ui.Button(label='Support Server', url=url1, style=discord.ButtonStyle.blurple))
        self.add_item(discord.ui.Button(label='Documentation', url="https://docs.astrobirb.dev/overview", style=discord.ButtonStyle.blurple))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(suggestions(client))     
