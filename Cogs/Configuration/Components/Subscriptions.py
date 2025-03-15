import discord

from dotenv import load_dotenv
from utils.emojis import *
load_dotenv()
# Mongos = AsyncIOMotorClient(os.getenv("MONGO_URL"))
# DB = Mongos["astro"]
# Customisation = DB["Customisation"]
# prem = DB["premium"]
# cfg = DB['Config']

class PremiumButtons(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    @discord.ui.button(
        label="Upgrade Server",
        emoji="<:sparkle:1233931758089666695>",
        style=discord.ButtonStyle.blurple,
        row=0
    )
    async def enable(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        from Cogs.Configuration.Configuration import ConfigMenu, Options        
        Config = await interaction.client.config.find_one({'_id': interaction.guild.id})        
        await interaction.client.db['premium'].update_one(
            {"user_id": interaction.user.id},
            {"$set": {"guild_id": interaction.guild.id}},
        )
        view = PremiumButtons(interaction.user)
        view.enable.disabled = True
        view.disable.disabled = False
        view.add_item(ConfigMenu(Options(Config=Config), interaction.user))

        await interaction.response.edit_message(
            embed=await SubscriptionsEmbed(interaction),
            view=view
            
        )

    @discord.ui.button(
        label="Deactive Server", style=discord.ButtonStyle.danger, disabled=True,
        row=0
    )
    async def disable(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user.id != self.author.id:
            embed = discord.Embed(
                description=f"  **{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)        
        from Cogs.Configuration.Configuration import ConfigMenu, Options        
        Config = await interaction.client.config.find_one({'_id': interaction.guild.id})
        await interaction.client.db['premium'].update_one(
            {"user_id": interaction.user.id}, {"$set": {"guild_id": None}}
        )
        view = PremiumButtons(interaction.user)
        view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
        view.enable.disabled = False
        view.disable.disabled = True
        await interaction.response.edit_message(
            embed=await SubscriptionsEmbed(interaction),
            view=view
            
        )


async def SubscriptionsEmbed(interaction: discord.Interaction):
    embed = discord.Embed(color=discord.Color.dark_embed())
    embed.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon)
    embed.set_thumbnail(url=interaction.guild.icon)
    result = await interaction.client.db['premium'].find_one({"guild_id": interaction.guild.id})
    user = await interaction.client.db['premium'].find_one({"user_id": interaction.user.id})
    if not result and not user:
        embed.description = "> This server has **no active subscriptions**, and there are no premium slots available for you."
    if user and not result:
        embed.description = "> Thanks for being a **premium subscriber!** You can active there server by pressing Upgrade Server!"
    if user and result:
        embed.description = "> Thanks for being a **premium server!** If you no longer want this server to have premium deactivate it below."
    return embed
