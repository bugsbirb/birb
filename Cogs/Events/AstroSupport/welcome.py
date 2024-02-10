import discord
from discord.ext import commands
from emojis import *


class welcome(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        target_guild_id = 1092976553752789054
        guild_on_join = self.client.get_guild(target_guild_id)

        if guild_on_join and member.guild.id == target_guild_id:
            channel_id = 1092976554541326372
            channel = guild_on_join.get_channel(channel_id)

            if channel:
                member_count = guild_on_join.member_count
                message = f"Welcome {member.mention} to **Astro Birb**! 👋"
                view = Welcome(member_count, member)
                await channel.send(message, view=view)

class Welcome(discord.ui.View):
    def __init__(self, member_count, member):
        super().__init__(timeout=None)
        self.gray_button.label = member_count
        self.member = member

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="<:logMembershipJoin:1172854752346918942>")
    async def gray_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.member
        embed = discord.Embed(title=f"@{user.display_name}", description=f"", color=0x2b2d31)
        embed.set_thumbnail(url=user.display_avatar.url)    
        embed.add_field(name='**Profile**', value=f"* **User:** {user.mention}\n* **Display:** {user.display_name}\n* **ID:** {user.id}\n* **Join:** <t:{int(user.joined_at.timestamp())}:F>\n* **Created:** <t:{int(user.created_at.timestamp())}:F>", inline=False)
        user_roles = " ".join([role.mention for role in reversed(user.roles) if role != interaction.guild.default_role][:20])
        embed.add_field(name="**Roles**", value=user_roles, inline=False)  
        await interaction.response.send_message(embed=embed, ephemeral=True)
async def setup(client: commands.Bot) -> None:
    await client.add_cog(welcome(client))   

