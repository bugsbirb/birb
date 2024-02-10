import discord
from discord.ext import commands
from emojis import *
from typing import Literal
import os
from permissions import *
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
class ApplicationResults(commands.Cog):
    def __init__(self, client):
        self.client = client
 


    async def modulecheck(self, ctx): 
     modulesdata = await modules.find_one({"guild_id": ctx.guild.id})    
     if modulesdata is None:
        return False
     elif modulesdata['Applications'] == True:   
        return True


    @commands.hybrid_group()
    async def application(self, ctx):
        return

    @application.command(description="Log Application results")
    async def results(
        self,
        ctx,
        applicant: discord.Member,
        result: Literal["Passed", "Failed"],
        *,
        feedback,
    ):
        if not await self.modulecheck(ctx):
            await ctx.send(f"{no} **{ctx.author.display_name}**, this module is currently disabled.")
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
                    msg = await channel.send(f"{applicant.mention}", embed=embed)
                    await ctx.send(f"{tick} **{ctx.author.display_name}**, submitted application results for **@{applicant.display_name}**")
                except discord.Forbidden:
                    await ctx.send(
                        f"{no} **{ctx.author.display_name}**, I don't have permission to send messages in {channel.mention}."
                    )
                    return
                view = JumpUrl(msg.jump_url)
                try:
                    await applicant.send(f"<:ApplicationFeedback:1178754449125167254> **{applicant.display_name}**, you application has been reviewed.", view=view)
                except discord.Forbidden:
                    pass
                if result == 'Passed':
                    roles_data = await ApplicationsRolesDB.find_one({"guild_id": ctx.guild.id})
                    if roles_data:
                        application_roles = roles_data.get("applicationroles", [])
                        member = ctx.guild.get_member(applicant.id)
                        roles_to_add = [discord.utils.get(ctx.guild.roles, id=role_id) for role_id in application_roles]
                        if roles_to_add and None not in roles_to_add:
                            try:
                                await member.add_roles(*roles_to_add)
                            except discord.Forbidden as e:
                                await ctx.send(f"{no} **{ctx.author.display_name},** Please check if I have permission to add roles and if I'm higher than the role.")
                                return
                else:
                    await ctx.send(
                        f"{no} **{ctx.author.display_name}**, the specified channel doesn't exist."
                    )
        else:
            await ctx.send(
                f"{no} **{ctx.author.display_name}**, this channel isn't configured. Please do `/config`."
            )


class JumpUrl(discord.ui.View):
    def __init__(self, jumpurl):
        super().__init__()
        url = jumpurl
        self.add_item(discord.ui.Button(label='Results', url=url, style=discord.ButtonStyle.blurple))



async def setup(client: commands.Bot) -> None:
    await client.add_cog(ApplicationResults(client))        