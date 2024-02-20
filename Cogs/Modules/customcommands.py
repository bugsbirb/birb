import discord
from discord.ext import commands
from discord.ext import commands
from emojis import *
from discord import app_commands
import os
import typing
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from permissions import has_admin_role
MONGO_URL = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(MONGO_URL)
db = client['astro']

custom_commands = db['Custom Commands']
CustomVoting = db['Commands Voting']

class CustomCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client


    async def commands_auto_complete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        try:
            filter = {
                'guild_id': interaction.guild_id 
            }

            tag_names = await custom_commands.distinct("name", filter)

 
            filtered_names = [name for name in tag_names if current.lower() in name.lower()]


            choices = [app_commands.Choice(name=name, value=name) for name in filtered_names[:25]]

            return choices
        except Exception as e:
            print(f"Error in commands_auto_complete: {e}")
            return []
        
    @commands.hybrid_group()
    async def command(self, ctx):
        pass



    @command.command(description="Run one of your servers custom commands.")
    @app_commands.autocomplete(command=commands_auto_complete)
    async def run(self, ctx, command, channel: discord.TextChannel = None):
        if not await has_customcommandrole(ctx, command):
            return

        command_data  = await custom_commands.find_one({'name': command, 'guild_id': ctx.guild.id})
        if command_data is None:
            return await ctx.send(f'{no} **{ctx.author.display_name},** That command does not exist.')
        
        if 'buttons' in command_data and command_data['buttons'] == "Voting Buttons":
            voting_data = {
                'guild_id': ctx.guild.id,
                'message_id': ctx.message.id,
                'author': ctx.author.id,
                'votes': 0,
                'Voters': []
            }
            await CustomVoting.insert_one(voting_data)
            view = Voting()
        elif 'buttons' in command_data and command_data['buttons'] == "Link Button":
            view = URL(command_data['url'], command_data['button_label'])
        else:
            view = None

        timestamp = datetime.utcnow().timestamp()
        timestampformat = f"<t:{int(timestamp)}:F>"

        replacements = {
            '{author.mention}': ctx.author.mention,
            '{author.name}': ctx.author.display_name,
            '{author.id}': str(ctx.author.id),
            '{timestamp}': timestampformat,
            '{guild.name}': ctx.guild.name if ctx.guild else '',
            '{guild.id}': str(ctx.guild.id) if ctx.guild else '',
            '{guild.owner.mention}': ctx.guild.owner.mention if ctx.guild and ctx.guild.owner else '',
            '{guild.owner.name}': ctx.guild.owner.display_name if ctx.guild and ctx.guild.owner else '',
            '{guild.owner.id}': str(ctx.guild.owner.id) if ctx.guild and ctx.guild.owner else '',
            '\n': "\n"
        }

        content = await self.replace_variables(command_data.get('content', ''), replacements)
        if content == "":
            content = ""

        if 'embed' in command_data and command_data['embed']:
            embed_title = await self.replace_variables(command_data['title'], replacements)
            embed_description = await self.replace_variables(command_data['description'], replacements)
            embed_author = await self.replace_variables(command_data['author'], replacements)

            if embed_title in ["None", None]:
                embed_title = ""
            if embed_description in ["None", None]:
                embed_description = ""
            color_value = command_data.get('color', None)
            colors = discord.Colour(int(color_value, 16)) if color_value else discord.Colour.dark_embed()

            embed = discord.Embed(
                title=embed_title,
                description=embed_description, color=colors)

            if embed_author in ["None", None]:
                embed_author = ""
            if 'image' in command_data:
                embed.set_image(url=command_data['image'])
            if 'thumbnail' in command_data:
                embed.set_thumbnail(url=command_data['thumbnail'])
            if 'author' in command_data and 'author_icon' in command_data:
                embed.set_author(name=embed_author, icon_url=command_data['author_icon'])

            if channel:
                try:
                    if content or embed or view:
                        msg = await channel.send(content, embed=embed, view=view)
                    else:
                        await ctx.send(f"{no} **{ctx.author.display_name},** This command does not have any content or embed.")
                        return
                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name},** I do not have permission to send messages in that channel.")
                    return
                await ctx.send(f"{tick} **{ctx.author.display_name},** The command has been sent", ephemeral=True)

            else:
                try:
                    if content or embed or view:
                        msg = await ctx.channel.send(content, embed=embed, view=view)
                    else:
                        await ctx.send(f"{no} **{ctx.author.display_name},** This command does not have any content or embed.")
                        return
                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name},** I do not have permission to send messages in that channel.")
                    return
                await ctx.send(f"{tick} **{ctx.author.display_name},** The command has been sent", ephemeral=True)

        else:
            if content is None:
                await ctx.send(f"{no} **{ctx.author.display_name},** That command does not have any content. Please remake it.")
                return
            if channel:
                try:
                    if content or view:
                        msg = await channel.send(content, view=view)
                    else:
                        await ctx.send(f"{no} **{ctx.author.display_name},** This command does not have any content or embed.")
                        return
                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name},** I do not have permission to send messages in that channel.")
                    return
                await ctx.send(f"{tick} **{ctx.author.display_name},** The command has been sent", ephemeral=True)

            else:
                try:
                    if content or view:
                        msg = await ctx.channel.send(content, view=view)
                    else:
                        await ctx.send(f"{no} **{ctx.author.display_name},** This command does not have any content or embed.")
                        return
                except discord.Forbidden:
                    await ctx.send(f"{no} **{ctx.author.display_name},** I do not have permission to send messages in that channel.")
                    return
                await ctx.send(f"{tick} {ctx.author.display_name}, The command has been sent", ephemeral=True)

        if 'buttons' in command_data and command_data['buttons'] == "Voting Buttons":
             voting_data = {
                'guild_id': ctx.guild.id,
                'message_id': msg.id,
                'author': ctx.author.id,
                'votes': 0,
                'Voters': []
            }
             await CustomVoting.insert_one(voting_data)

    async def replace_variables(self, message, replacements):
     for placeholder, value in replacements.items():
        if value is not None:
            message = str(message).replace(placeholder, str(value))
        else:
            message = str(message).replace(placeholder, "")  
     return message
        
        
class Voting(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        


    @discord.ui.button(label="0", style=discord.ButtonStyle.green, emoji=f"{tick}", custom_id="vote")
    async def upvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id


        voting = await CustomVoting.find_one({"message_id": interaction.message.id})



        if interaction.user.id in voting.get('Voters', []):
         CustomVoting.update_one(
        {"message_id": message_id},
        {
            "$inc": {"votes": -1},
            "$pull": {"Voters": interaction.user.id},
        },
         )
         new_label = str(voting.get('votes', 0) - 1)
         button.label = new_label
         await interaction.message.edit(view=self)
         await interaction.response.send_message(f"{tick} **{interaction.user.display_name},** You have successfully unvoted.", ephemeral=True)
         return

        CustomVoting.update_one(
        {"message_id": message_id},
        {
            "$inc": {"votes": 1},
            "$push": {"Voters": interaction.user.id},
        },
         )
        new_label = str(voting.get('votes', 0) + 1)
        button.label = new_label

        await interaction.response.send_message(f"{tick} **{interaction.user.display_name},** You have successfully voted.", ephemeral=True)

        await interaction.message.edit(view=self)
 
    @discord.ui.button(label="Voters", style=discord.ButtonStyle.blurple, emoji=f"{folder}", custom_id="viewlist")
    async def list(self, interaction: discord.Interaction, button: discord.ui.Button):
        voting = await CustomVoting.find_one({"message_id": interaction.message.id})
        voters = voting.get('Voters', [])
        if not voters: 
         voters_str = f"**{interaction.user.display_name},** there are no voters!"
        else:
         voters_str = "\n".join([f"<@{voter}> ({voter})" for voter in voters])
 

        embed_description = str(voters_str)[:4096]
        embed = discord.Embed(title="Voters", description=embed_description, color=discord.Color.dark_embed())
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def has_customcommandrole(ctx, command):
    filter = {
        'guild_id': ctx.guild.id,
        'name': command
    }
    role_data = await custom_commands.find_one(filter)

    if role_data and 'permissionroles' in role_data:
        role_ids = role_data['permissionroles']
        if not isinstance(role_ids, list):
            role_ids = [role_ids]

        if any(role.id in role_ids for role in ctx.author.roles):
            print('allowed')
            return True
        else:
            print('not allowed')
            await ctx.send(f"{no} **{ctx.author.display_name}**, you don't have permission to use this command.\n<:Arrow:1115743130461933599>**Required:** `Custom Command Permission`")
            return False
    else:
        print('none')
        return await has_admin_role(ctx)

class URL(discord.ui.View):
    def __init__(self, url, buttonname):
        super().__init__()
        self.add_item(discord.ui.Button(label=buttonname, url=url, style=discord.ButtonStyle.blurple))
        

async def setup(client: commands.Bot) -> None:
    await client.add_cog(CustomCommands(client))     
