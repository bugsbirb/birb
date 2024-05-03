import discord
from discord import app_commands
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

    @app_commands.command(description="Configure notifications", name="consent")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)       
    async def consent(self, interaction: discord.Interaction):
        consent_data = await consentdb.find_one({"user_id": interaction.user.id})

        if consent_data is None:
            await consentdb.insert_one({"user_id": interaction.user.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled", "LOAAlerts": "Enabled"})
            consent_data = {"user_id": interaction.user.id, "infractionalert": "Enabled", "PromotionAlerts": "Enabled", "LOAAlerts": "Enabled"}
        view = Confirm(consent_data, interaction.user)
        if consent_data.get('infractionalert') == "Enabled":
            view.toggle_infractions.style = discord.ButtonStyle.green
        else:

            view.toggle_infractions.style = discord.ButtonStyle.red

        if consent_data.get('PromotionAlerts') == "Enabled":
            view.toggle_promotions.style = discord.ButtonStyle.green

        else:
            view.toggle_promotions.style = discord.ButtonStyle.red
        if consent_data.get('LOAAlerts', "Enabled") == "Enabled":
            view.toggle_loa.style = discord.ButtonStyle.green
        else:
            view.toggle_loa.style = discord.ButtonStyle.red
        embed = discord.Embed(title="Notifications",
                              description=f"{replytop}**Infraction Alerts:** When you are infracted you'll receive a direct message.\n{replymiddle}**Promotion Alerts:** When you are promoted you'll receive a direct message.\n{replybottom}**LOA Alerts:** When you are on LOA you'll receive direct messages.",
                              color=discord.Color.dark_embed())
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        
        
        await interaction.response.send_message(embed=embed, view=view)


class Confirm(discord.ui.View):
    def __init__(self, consent_data, author):
        super().__init__(timeout=None)
        self.author = author
        self.consent_data = consent_data



    @discord.ui.button(label='Infractions Alerts', style=discord.ButtonStyle.grey)
    async def toggle_infractions(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.consent_data['infractionalert'] = "Enabled" if self.consent_data['infractionalert'] == "Disabled" else "Disabled"
        await consentdb.update_one({"user_id": self.consent_data['user_id']}, {"$set": self.consent_data}, upsert=True)
        self.toggle_infractions.style = discord.ButtonStyle.green if self.consent_data['infractionalert'] == "Enabled" else discord.ButtonStyle.red
        await interaction.response.edit_message(content=None, view=self)

    @discord.ui.button(label='Promotion Alerts', style=discord.ButtonStyle.grey)
    async def toggle_promotions(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"{redx} **{interaction.user.display_name},** this is not your panel!",
                                  color=discord.Colour.brand_red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.consent_data['PromotionAlerts'] = "Enabled" if self.consent_data['PromotionAlerts'] == "Disabled" else "Disabled"
        await consentdb.update_one({"user_id": self.consent_data['user_id']}, {"$set": self.consent_data}, upsert=True)
        self.toggle_promotions.style = discord.ButtonStyle.green if self.consent_data['PromotionAlerts'] == "Enabled" else discord.ButtonStyle.red
        await interaction.response.edit_message(content=None, view=self)
    @discord.ui.button(label='LOA Alerts', style=discord.ButtonStyle.grey)
    async def toggle_loa(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description=f"**{interaction.user.display_name},** this is not your view!",
                                color=discord.Colour.dark_embed())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        consent = self.consent_data.get('LOAAlerts', "Enabled")
        consent = "Enabled" if consent == "Disabled" else "Disabled"
        update_data = {"LOAAlerts": consent}
        await consentdb.update_one({"user_id": self.consent_data['user_id']}, {"$set": update_data}, upsert=True)
        self.consent_data['LOAAlerts'] = consent
        self.toggle_loa.style = discord.ButtonStyle.green if consent == "Enabled" else discord.ButtonStyle.red
        await interaction.response.edit_message(content=None, view=self)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Consent(client))        
