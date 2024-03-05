import discord
from discord.ext import commands
import motor.motor_asyncio
from dotenv import load_dotenv
import os
from emojis import *

load_dotenv()

MONGO_URL = os.getenv('MONGO_URL')
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client['astro']
scollection = db['staffrole']
arole = db['adminrole']
consentdb = db['consent']


class Consent(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_command(description="Configure notifications", name="consent")
    async def consent(self, ctx):
        consent_data = await consentdb.find_one({"user_id": ctx.author.id})

        if consent_data is None:
            await consentdb.insert_one({"user_id": ctx.author.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled"})
            consent_data = {"user_id": ctx.author.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled"}
        view = Confirm(consent_data, ctx.author)
        if consent_data.get('infractionalert') == "Enabled":
            infraction_alerts = "<:check:1214613370448253038>"
            view.toggle_infractions.style = discord.ButtonStyle.green
        else:
            infraction_alerts = "<:x_:1214611537524949123>"
            view.toggle_infractions.style = discord.ButtonStyle.red

        if consent_data.get('PromotionAlerts') == "Enabled":
            promotion_alert = "<:check:1214613370448253038>"
            view.toggle_promotions.style = discord.ButtonStyle.green

        else:
            promotion_alert = "<:x_:1214611537524949123>"
            view.toggle_promotions.style = discord.ButtonStyle.red

        embed = discord.Embed(title="<:Notification:1184528462338347039> Notifications",
                              description=f"* **Infraction Alerts:** {infraction_alerts}\n* **Promotion Alerts:** {promotion_alert}",
                              color=discord.Color.dark_embed())
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        
        
        await ctx.send(embed=embed, view=view)


class Confirm(discord.ui.View):
    def __init__(self, consent_data, author):
        super().__init__(timeout=None)
        self.author = author
        self.consent_data = consent_data

    async def update_embed(self, interaction: discord.Interaction):
        consent_data = await consentdb.find_one({"user_id": interaction.user.id})
        view = Confirm(consent_data, interaction.user)

        if consent_data.get('infractionalert') == "Enabled":
            infraction_alerts = "<:check:1214613370448253038>"
            view.toggle_infractions.style = discord.ButtonStyle.green

        else:
            infraction_alerts = "<:x_:1214611537524949123>"
            view.toggle_infractions.style = discord.ButtonStyle.red

        if consent_data.get('PromotionAlerts') == "Enabled":
            promotion_alert = "<:check:1214613370448253038>"
            view.toggle_promotions.style = discord.ButtonStyle.green
        else:
            promotion_alert = "<:x_:1214611537524949123>"
            view.toggle_promotions.style = discord.ButtonStyle.red


        embed = discord.Embed(title="<:Notification:1184528462338347039> Notifications",
                              description=f"* **Infraction Alerts:** {infraction_alerts}\n* **Promotion Alerts:** {promotion_alert}",
                              color=discord.Color.dark_embed()
                              )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.message.edit(embed=embed, view=view)

    @discord.ui.button(label='Infractions Alerts', style=discord.ButtonStyle.grey)
    async def toggle_infractions(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.consent_data['infractionalert'] = "Enabled" if self.consent_data['infractionalert'] == "Disabled" else "Disabled"
        await consentdb.update_one({"user_id": self.consent_data['user_id']}, {"$set": self.consent_data})
        await interaction.response.edit_message(content=None)
        await self.update_embed(interaction)

    @discord.ui.button(label='Promotion Alerts', style=discord.ButtonStyle.grey)
    async def toggle_promotions(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.global_name},** this is not your view!",
                                  color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.consent_data['PromotionAlerts'] = "Enabled" if self.consent_data['PromotionAlerts'] == "Disabled" else "Disabled"
        await consentdb.update_one({"user_id": self.consent_data['user_id']}, {"$set": self.consent_data})
        await interaction.response.edit_message(content=None)
        await self.update_embed(interaction)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Consent(client))        
