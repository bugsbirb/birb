import discord
from discord.ext import commands
import asyncio
from utils.emojis import *

from utils.permissions import has_staff_role

class ForumCreaton(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        guild_id = thread.guild.id
        config_data = await self.client.db['Forum Configuration'].find_one(
            {"guild_id": guild_id, "channel_id": thread.parent_id}
        )
        if not config_data or "channel_id" not in config_data:
            return

        if thread.guild.id != guild_id:
            return
        if thread.parent_id != config_data["channel_id"]:
            return
        await asyncio.sleep(2)
        if config_data:
            from Cogs.Configuration.Components.EmbedBuilder import DisplayEmbed

            embed = await DisplayEmbed(
                config_data,
            )
            Roles = ""
            view = None
            Roled = config_data.get("role")
            if Roled:
                if not isinstance(Roled, list):
                    Roled = [Roled]

                Roles = []
                for role_id in Roled:
                    role = thread.guild.get_role(role_id)
                    if role:
                        Roles.append(role)
                Roles = ", ".join([role.mention for role in Roles])

            if config_data.get("Close") or config_data.get("Lock"):
                view = CloseLock()
                view.remove_item(view.Close)
                view.remove_item(view.lock)
                if config_data.get("Close"):
                    view.add_item(view.Close)
                if config_data.get("Lock"):
                    view.add_item(view.lock)

            msg = await thread.send(
                content=f"{Roles}",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(roles=True, users=True),
                view=view,
            )
            try:
                await msg.pin()
            except discord.Forbidden:
                print("[ERROR] Unable to pin message.")
            except discord.HTTPException:
                print("[ERROR] Unable to pin message.")


class CloseLock(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(
        label="Lock",
        style=discord.ButtonStyle.blurple,
        emoji="<:close:1280576608125849731>",
    )
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await has_staff_role(interaction):
            return
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message(
                f"  **{interaction.user.display_name},** This can only be used in a thread.",
                ephemeral=True,
            )
            return
        thread = interaction.channel
        if self.lock.label == "Lock":
            self.lock.label = "Unlock"
            self.lock.emoji = "<:unlock:1280576824065396848>"
            self.lock.style = discord.ButtonStyle.green
            await thread.edit(locked=True)
            await interaction.channel.send(
                content=f"<:close:1280576608125849731> **@{interaction.user.display_name}**, has locked the thread."
            )
        else:
            self.lock.label = "Lock"
            self.lock.emoji = "<:close:1280576608125849731>"
            self.lock.style = discord.ButtonStyle.blurple
            await interaction.channel.edit(locked=False)
            await interaction.channel.send(
                content=f"<:unlock:1280576824065396848> **@{interaction.user.display_name}**, has unlocked the thread."
            )
        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.red,
        emoji="<:close:1280577170233753650>",
    )
    async def Close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await has_staff_role(interaction):
            return
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message(
                f"  **{interaction.user.display_name},** This can only be used in a thread.",
                ephemeral=True,
            )
            return
        thread = interaction.channel

        if self.Close.label == "Close":
            await thread.edit(archived=True)
            self.Close.label = "Reopen"
            self.Close.emoji = "<:Add:1163095623600447558>"

            await interaction.channel.send(
                content=f"<:close:1280577170233753650> **@{interaction.user.display_name}**, has closed the thread.",
                
            )

            self.Close.style = discord.ButtonStyle.green
        else:
            await interaction.channel.edit(archived=False)
            self.Close.label = "Close"
            self.Close.emoji = "<:close:1280577170233753650>"

            await interaction.channel.send(
                content=f"<:Add:1163095623600447558> **@{interaction.user.display_name}**, has reopened the thread.",
                
            )
            self.Close.style = discord.ButtonStyle.red

        await interaction.response.edit_message(view=self)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ForumCreaton(client))
