import discord

from core.discord.HelpEmbeds import NotYourPanel
from core.discord.emojis import *


class PremiumButtons(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    @discord.ui.button(
        label="Upgrade Server",
        emoji="<:sparkle:1233931758089666695>",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def enable(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        await interaction.response.defer()
        from cogs.Configuration.Configuration import ConfigMenu, Options

        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})

        Subs = await interaction.client.db["Subscriptions"].find_one(
            {"user": interaction.user.id}
        )
        tokens = Subs.get("Tokens", 0) if Subs else 0
        guilds = Subs.get("guilds", []) if Subs else []

        if len(guilds) >= tokens:
            embed = discord.Embed(
                description=f"{redx} **You have reached your premium server limit ({tokens}).**",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        if interaction.guild.id in guilds:
            embed = discord.Embed(
                description=f"{redx} **This server is already activated for premium.**",
                color=discord.Colour.brand_red(),
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        await interaction.client.db["Subscriptions"].update_one(
            {"user": interaction.user.id},
            {"$push": {"guilds": interaction.guild.id}},
            upsert=True,
        )

        if Config is not None:
            features = Config.get("Features", [])
            if "PREMIUM" not in features:
                features.append("PREMIUM")
                await interaction.client.config.update_one(
                    {"_id": interaction.guild.id}, {"$set": {"Features": features}}
                )

        view = PremiumButtons(interaction.user)
        view.enable.disabled = True
        view.disable.disabled = False
        view.add_item(ConfigMenu(Options(Config=Config), interaction.user))

        await interaction.edit_original_response(
            embed=await SubscriptionsEmbed(interaction), view=view
        )

    @discord.ui.button(
        label="Deactive Server", style=discord.ButtonStyle.danger, disabled=True, row=0
    )
    async def disable(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user.id != self.author.id:

            return await interaction.response.send_message(
                embed=NotYourPanel(), ephemeral=True
            )
        from cogs.Configuration.Configuration import ConfigMenu, Options

        Config = await interaction.client.config.find_one({"_id": interaction.guild.id})
        await interaction.client.db["Subscriptions"].update_one(
            {"user": interaction.user.id}, {"$pull": {"guilds": interaction.guild.id}}
        )

        if Config is not None:
            features = Config.get("Features", [])
            if "PREMIUM" in features:
                features.remove("PREMIUM")
                await interaction.client.config.update_one(
                    {"_id": interaction.guild.id}, {"$set": {"Features": features}}
                )

        view = PremiumButtons(interaction.user)
        view.add_item(ConfigMenu(Options(Config=Config), interaction.user))
        view.enable.disabled = False
        view.disable.disabled = True

        await interaction.response.edit_message(
            embed=await SubscriptionsEmbed(interaction), view=view
        )


async def SubscriptionsEmbed(Interaction: discord.Interaction):
    Embed = discord.Embed(color=discord.Color.dark_embed())
    Embed.set_author(name=Interaction.guild.name, icon_url=Interaction.guild.icon)
    Embed.set_thumbnail(url=Interaction.guild.icon)

    GuildHasPremium = await Interaction.client.db["Subscriptions"].find_one(
        {"guilds": {"$in": [Interaction.guild.id]}}
    )
    UserDoc = await Interaction.client.db["Subscriptions"].find_one(
        {"user": Interaction.user.id}
    )

    Tokens = UserDoc.get("Tokens", 0) if UserDoc else 0
    Guilds = UserDoc.get("guilds", []) if UserDoc else []
    Used = len(Guilds)

    if not GuildHasPremium and not UserDoc:
        Embed.description = (
            "> This server has **no active subscriptions**, "
            "> and there are no premium slots available for you."
        )
        return Embed

    if UserDoc and not GuildHasPremium:
        Embed.description = (
            "> Thanks for being a **premium subscriber!**\n"
            "> You can activate this server by pressing **Upgrade Server**!"
        )
    elif UserDoc and GuildHasPremium:
        Embed.description = (
            "> Thanks for being a **premium server!**\n"
            "> If you no longer want this server to have premium, deactivate it below."
        )
    elif GuildHasPremium and not UserDoc:
        Embed.description = "> This server is premium, but you do not have any active subscriptions associated with your account."

    if UserDoc:
        Embed.add_field(
            name="Current Subscription", value=f"> **Tokens:** `{Used}`/`{Tokens}`"
        )

    return Embed
