import discord
from discord.ext import commands, tasks
import datetime

import discord.http
from utils.emojis import *
import os
import asyncio

from utils.Module import ModuleCheck

MONGO_URL = os.getenv("MONGO_URL")


class on_ban(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.deletebitch.start()

    @tasks.loop(name="deletebitch", minutes=15)
    async def deletebitch(self):
        await self.client.db["Appeal Sessions"].delete_many(
            {"time": {"$lt": datetime.datetime.utcnow() - datetime.timedelta(hours=1)}}
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.Member):
        result = await self.client.db["Ban Appeals Configuratio"].find_one(
            {"guild_id": guild.id}
        )
        if result is None:
            return
        if not await ModuleCheck(guild.id, "Ban Appeal"):
            return

        if result.get("questions", []) == []:
            return
        view = AppealButton(self.client)
        view.remove_item(view.endappeal)
        banmsg = result.get(
            "Ban Message",
            f"  **{user.display_name}**, you have been banned from **{guild.name}** appeal below.",
        )

        try:
            msg = await user.send(banmsg, view=view)
        except discord.Forbidden:
            return
        await self.client.db["Ban Appeal Logs"].insert_one(
            {
                "guild_id": guild.id,
                "user_id": user.id,
                "time": datetime.datetime.utcnow(),
                "msg_id": msg.id,
            }
        )


class AppealButton(discord.ui.View):
    def __init__(self, client: discord.Client):
        super().__init__(timeout=None)
        self.client = client

    @discord.ui.button(
        label="Appeal",
        style=discord.ButtonStyle.green,
        custom_id="appeal:PERSISTENT",
        emoji="<:arrow:1223062767255293972>",
    )
    async def appeal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        result = await interaction.client.db["Ban Appeal Logs"].find_one(
            {"user_id": interaction.user.id, "msg_id": interaction.message.id}
        )
        if result is None:
            await interaction.followup.send(
                f"{Warning} {interaction.user.display_name}, I couldn't find the ban data.",
                ephemeral=True,
            )
            return
        try:
            guild = await self.client.fetch_guild(result.get("guild_id", 0))
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            return await interaction.followup.send(
                f"  *{interaction.user.display_name},** I can't find the server you were banned from. They most likely removed the bot.",
                ephemeral=True,
            )
        if guild is None:
            await interaction.followup.send(
                f"  *{interaction.user.display_name},** I can't find the server you were banned from. They most likely removed the bot.",
                ephemeral=True,
            )
            return

        result2 = await interaction.client.db["Ban Appeals Configuration"].find_one(
            {"guild_id": guild.id}
        )
        if not result2:
            await interaction.followup.send(
                f"  **{interaction.user.display_name},** I couldn't find the appeal configuration for this guild.",
                ephemeral=True,
            )
            return

        data = result2.get("questions", [])
        if len(data) == 0:
            await interaction.followup.send(
                f"  I couldn't find any questions for this appeal.", ephemeral=True
            )
            return

        await interaction.followup.send(
            f"<:Application:1224722901328986183> **{interaction.user.display_name},** the appeal has started.",
            ephemeral=True,
        )
        await interaction.client.db["Appeal Sessions"].insert_one(
            {"user_id": interaction.user.id, "time": datetime.datetime.utcnow()}
        )

        responses = {}
        view = self
        view.remove_item(view.appeal)
        view.add_item(view.endappeal)
        view.endappeal.disabled = False
        await interaction.edit_original_response(view=view)
        for idx, (key, question) in enumerate(data.items(), start=1):
            if isinstance(question, str) and question.strip():
                embed = discord.Embed(title=question, color=discord.Color.yellow())
                embed.set_author(
                    name=f"Question #{idx}", icon_url=interaction.user.display_avatar
                )
                await interaction.followup.send(embed=embed)

                def check(m):
                    return m.author == interaction.user and m.guild is None

                try:
                    message = await self.client.wait_for(
                        "message", timeout=500, check=check
                    )
                    responses[key] = message.content
                except asyncio.TimeoutError:
                    await interaction.client.db["Appeal Sessions"].delete_one(
                        {"user_id": interaction.user.id}
                    )
                    await interaction.followup.send(
                        f"  **{interaction.user.display_name},** you took too long to respond. Please start the appeal process again."
                    )
                    return
        embed = discord.Embed(description="", color=discord.Color.yellow())
        embed.set_author(
            name=f"{interaction.user.display_name}'s Ban Appeal",
            icon_url=interaction.user.display_avatar,
        )
        embed.set_thumbnail(url=interaction.user.display_avatar)
        embed.set_image(url="https://www.astrobirb.dev/invisble.png")
        questions = result2.get("questions", {})
        for idx, (question_key, response) in enumerate(responses.items(), start=1):
            question_text = questions.get(question_key, "Question not found")
            embed.description += f"**{question_text}**\n{response}\n"

        channel = await guild.fetch_channel(result2.get("banchannel", 0))
        if channel is None:
            await interaction.client.db["Appeal Sessions"].delete_one(
                {"user_id": interaction.user.id}
            )
            await interaction.followup.send(
                f"  **{interaction.user.display_name},** I couldn't find the ban appeal channel for this guild."
            )
            return

        view = AcceptOrDeny(self.client)
        msg = await channel.send(embed=embed, view=view)

        await interaction.followup.send(
            f"  Your appeal has been submitted. Thanks @{interaction.user.display_name}."
        )
        await interaction.client.db["Appeal Sessions"].delete_one(
            {"user_id": interaction.user.id}
        )
        await interaction.client.db["Ban Appeal Logs"].insert_one(
            {
                "msg_id": msg.id,
                "guild_id": guild.id,
                "user_id": interaction.user.id,
                "time": datetime.datetime.utcnow(),
            }
        )
        view = self
        view.remove_item(view.appeal)
        view.remove_item(view.endappeal)
        view.add_item(
            discord.ui.Button(
                label="Appealed",
                style=discord.ButtonStyle.green,
                disabled=True,
                emoji= None,
                custom_id="APPEALEBUTRTONDS:PERSISTENT",
            )
        )
        await interaction.edit_original_response(view=view)

    @discord.ui.button(
        label="End",
        style=discord.ButtonStyle.red,
        custom_id="end:PERSISTENT",
        disabled=True,
    )
    async def endappeal(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.client.db["Appeal Sessions"].delete_one(
            {"user_id": interaction.user.id}
        )
        view = AppealButton(self.client)
        view.remove_item(view.endappeal)

        await interaction.response.edit_message(view=view)
        return


class AcceptOrDeny(discord.ui.View):
    def __init__(self, client):
        super().__init__(timeout=None)
        self.client = client

    @discord.ui.button(
        label="Accept", style=discord.ButtonStyle.green, custom_id="accept:PERSIST"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        result = await interaction.client.db["Ban Appeal Logs"].find_one(
            {"msg_id": interaction.message.id}
        )
        if not result:
            await interaction.response.send_message(
                f"  I couldn't find the appeal data for this message.",
                ephemeral=True,
            )
            return
        msg = interaction.message
        embed = msg.embeds[0]
        embed.color = discord.Color.brand_green()
        embed.title = f"  Appeal Accepted"
        embed.set_footer(
            text=f"Accepted By @{interaction.user.display_name}",
            icon_url=interaction.user.display_avatar,
        )
        try:
            user = await self.client.fetch_user(result.get("user_id"))
        except (discord.HTTPException, discord.NotFound):
            user = None
        if user:
            try:
                await interaction.guild.unban(user)
            except discord.Forbidden:
                await interaction.followup.send(
                    f"  I couldn't unban the user. Please check if I have permissions to unban people.",
                    ephemeral=True,
                )
                return
            embed2 = discord.Embed(
                title=f"  Appeal Accepted",
                description=f"You have been unbanned from **@{interaction.guild.name}**!",
                color=discord.Color.brand_green(),
            )
            try:
                await user.send(embed=embed2)
            except discord.Forbidden:
                pass
        await interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(
        label="Deny", style=discord.ButtonStyle.red, custom_id="deny:PERSIST"
    )
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        result = await interaction.client.db["Ban Appeal Logs"].find_one(
            {"msg_id": interaction.message.id}
        )
        if not result:
            await interaction.followup.send(
                f"  I couldn't find the appeal data for this message.",
                ephemeral=True,
            )
            return
        msg = interaction.message
        embed = msg.embeds[0]
        embed.color = discord.Color.brand_red()
        embed.title = f"  Appeal Denied"
        embed.set_footer(
            text=f"Denied By @{interaction.user.display_name}",
            icon_url=interaction.user.display_avatar,
        )
        try:
            user = await self.client.fetch_user(result.get("user_id"))
        except (discord.HTTPException, discord.NotFound):
            user = None
        if user:
            embed2 = discord.Embed(
                title=f"  Appeal Denied",
                description=f"Your appeal has been denied @{interaction.guild.name}.",
                color=discord.Color.brand_red(),
            )
            try:
                await user.send(embed=embed2)
            except discord.Forbidden:
                pass
        await interaction.edit_original_response(embed=embed, view=None)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_ban(client))
